import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from saa.contracts.asset_class import CmaMethodEstimate, CmaMethodId, CmaMethodsBody
from saa.contracts.portfolio import CovarianceBody
from saa.contracts.registry import read
from saa.data.lake import DataLake
from saa.data.store import DataStore
from saa.run import RunContext
from saa.skills.cma_methods import (
    load_cma_settings,
    run_cma_methods,
    run_methods,
    write_outputs,
)
from saa.skills.cma_methods import methods as cm

AS_OF = pd.Timestamp("2026-09-15")
M = CmaMethodId


@pytest.fixture(scope="module")
def settings(config):
    return load_cma_settings(config)


def market(config, *, months=240, excess=0.005, **overrides) -> cm.MarketInputs:
    """Synthetic inputs: every asset earns T-bill + ``excess`` a month, vol 10% (cash 1%)."""
    assets = config.universe.assets
    ids = [a.id for a in assets]
    index = pd.date_range(end="2026-08-31", periods=months, freq="ME")
    rf = pd.Series(0.003, index=index)
    returns = pd.DataFrame({a: rf + excess for a in ids}, index=index)
    vols = {a: (1.0 if a == "cash" else 10.0) for a in ids}
    cov = np.diag([(vols[a] / 100) ** 2 for a in ids])
    macro_index = pd.date_range(end="2026-09-30", periods=24, freq="ME")
    macro = pd.DataFrame(
        {
            "DTB3": 4.0,
            "DGS7": 4.5,
            "DGS10": 5.0,
            "AAA": 5.5,
            "BAA": 6.5,
            "BAMLH0A0HYM2EY": 8.0,
        },
        index=macro_index,
    )
    inputs = dict(
        as_of=AS_OF,
        returns=returns,
        risk_free=rf,
        risk_free_pct=4.0,
        covariance=CovarianceBody(
            asset_ids=ids,
            method="sample",
            window_years=20,
            matrix=cov.tolist(),
            volatilities_pct=vols,
        ),
        horizon_years=3,
        groups={a.id: a.group for a in assets},
        tickers={a.id: a.ticker for a in assets},
        macro=macro,
        surveys={
            "STOCK10": (7.0, pd.Timestamp("2026-01-01")),
            "BOND10": (4.0, pd.Timestamp("2026-01-01")),
            "BILL10": (3.0, pd.Timestamp("2026-01-01")),
            "RGDP10": (2.0, pd.Timestamp("2026-01-01")),
            "CPI10": (2.5, pd.Timestamp("2026-07-01")),
        },
    )
    inputs.update(overrides)
    return cm.MarketInputs(**inputs)


def by_method(estimates):
    return {e.method: e for e in estimates}


# --------------------------------------------------------------------------- contract
def test_an_unavailable_method_carries_no_number():
    with pytest.raises(ValidationError, match="no estimate"):
        CmaMethodEstimate(
            method=M.INVERSE_GORDON,
            expected_return_pct=0.0,
            confidence=0.0,
            rationale="-",
            unavailable_reason="not applicable",
        )
    with pytest.raises(ValidationError, match="needs expected_return_pct"):
        CmaMethodEstimate(method=M.HISTORICAL_ERP, confidence=0.5, rationale="-")


def test_method_range_ignores_unavailable_methods():
    body = CmaMethodsBody(
        asset_id="gold",
        horizon_years=3,
        volatility_pct=15.0,
        methods=[
            CmaMethodEstimate(
                method=M.HISTORICAL_ERP, expected_return_pct=6.0, confidence=0.5, rationale="-"
            ),
            cm.unavailable(M.INVERSE_GORDON, "not applicable"),
            CmaMethodEstimate(
                method=M.AUTO_BLEND, expected_return_pct=6.0, confidence=0.5, rationale="-"
            ),
        ],
    )
    assert body.method_range == (6.0, 6.0)


# --------------------------------------------------------------------------- methods
def test_historical_erp_is_the_mean_excess_plus_todays_bill(config, settings):
    e = cm.historical_erp("us_large_cap", market(config), settings)
    assert e.expected_return_pct == pytest.approx(4.0 + 0.005 * 12 * 100)
    assert e.components["months"] == 240


def test_historical_erp_confidence_grows_with_history(config, settings):
    short = cm.historical_erp("us_large_cap", market(config, months=90), settings)
    long = cm.historical_erp("us_large_cap", market(config, months=400), settings)
    assert short.confidence < long.confidence == 0.5


def test_regime_premium_uses_returns_after_the_regime_not_during_it(config, settings):
    """Months labelled `bust` have a -5% return themselves, but the 36 months after them earn
    +2% a month. A predictive premium reads the second; the contemporaneous one the first."""
    x = market(config, months=240)
    index = x.returns.index
    labels = pd.Series("boom", index=index)
    bust = index[100:106]
    labels[bust] = "bust"
    labels.iloc[-1] = "bust"  # today is a bust month
    excess = pd.Series(0.0, index=index)
    excess[bust] = -0.05
    excess[index[106:142]] = 0.02
    x.returns["us_large_cap"] = x.risk_free + excess
    x.regime_labels = labels
    e = cm.regime_adjusted("us_large_cap", x, settings)
    assert e.components["regime_excess_return_pct"] > 0
    assert e.components["regime_months"] == 6  # today's month has no forward window yet
    w = 6 / (6 + settings.regime.credibility_months)
    expected = (
        w * e.components["regime_excess_return_pct"]
        + (1 - w) * e.components["unconditional_excess_return_pct"]
    )
    assert e.expected_return_pct == pytest.approx(4.0 + expected, abs=1e-3)


def test_regime_adjusted_needs_labels(config, settings):
    with pytest.raises(cm.Unavailable, match="regime labels"):
        cm.regime_adjusted("us_large_cap", market(config), settings)


def test_black_litterman_is_delta_sigma_w(config, settings):
    ids = [a.id for a in config.universe.assets]
    aum = pd.DataFrame(
        {"total_assets": [float(i + 1) for i in range(len(ids))]},
        index=[a.ticker for a in config.universe.assets],
    )
    x = market(config, fund_snapshot=aum)
    w = aum["total_assets"].to_numpy() / aum["total_assets"].sum()
    pi = settings.black_litterman.risk_aversion * np.asarray(x.covariance.matrix) @ w
    for i, asset in enumerate(ids):
        e = cm.bl_equilibrium(asset, x, settings)
        assert e.expected_return_pct == pytest.approx(4.0 + 100 * pi[i], abs=1e-4)


def test_black_litterman_without_a_snapshot_is_unavailable(config, settings):
    with pytest.raises(cm.Unavailable, match="snapshot"):
        cm.bl_equilibrium("us_large_cap", market(config), settings)


def shiller(cape, dividend=2.0, price=100.0):
    index = pd.date_range("1990-01-31", "2026-06-30", freq="ME")
    return pd.DataFrame({"price": price, "dividend": dividend, "cape": cape}, index=index)


def test_inverse_gordon_sums_yield_growth_and_valuation(config, settings):
    x = market(config, shiller=shiller(cape=25.0))  # CAPE at its anchor: no valuation drift
    e = cm.inverse_gordon("us_large_cap", x, settings)
    addback = 0.5 * 0.10**2 * 100
    assert e.components["valuation_change_pct"] == pytest.approx(0.0)
    assert e.expected_return_pct == pytest.approx(2.0 + 2.0 + 2.5 + addback)


def test_expensive_markets_subtract_valuation_drift(config, settings):
    frame = shiller(cape=25.0)
    frame.iloc[-1, frame.columns.get_loc("cape")] = 50.0  # doubled against the anchor
    e = cm.inverse_gordon("us_large_cap", market(config, shiller=frame), settings)
    years = settings.valuation.reversion_years
    assert e.components["valuation_change_pct"] == pytest.approx((0.5 ** (1 / years) - 1) * 100)


def test_cape_method_adds_inflation_to_the_earnings_yield(config, settings):
    e = cm.implied_erp_cape("us_large_cap", market(config, shiller=shiller(cape=40.0)), settings)
    assert e.expected_return_pct == pytest.approx(2.5 + 2.5 + 0.5)


def test_stale_valuation_is_unavailable(config, settings):
    x = market(config, shiller=shiller(cape=25.0).loc[:"2025-06-30"])
    with pytest.raises(cm.Unavailable, match="Shiller"):
        cm.inverse_gordon("us_large_cap", x, settings)


def test_survey_only_covers_mapped_assets(config, settings):
    x = market(config)
    assert cm.survey_consensus("us_large_cap", x, settings).components["survey_pct"] == 7.0
    with pytest.raises(cm.Unavailable, match="no public consensus"):
        cm.survey_consensus("gold", x, settings)
    x.surveys["STOCK10"] = (7.0, pd.Timestamp("2024-01-01"))
    with pytest.raises(cm.Unavailable, match="too old"):
        cm.survey_consensus("us_large_cap", x, settings)


def test_yield_builder_subtracts_credit_losses(config, settings):
    e = cm.yield_building_block("hy_corporates", market(config), settings)
    loss = settings.credit_loss_pct["hy_corporates"]
    assert e.expected_return_pct == pytest.approx(8.0 - loss + 0.5 * 0.1**2 * 100)


def test_yield_builder_falls_back_at_lower_confidence(config, settings):
    """No ICE index yield in the synthetic lake: IG falls back to the Moody's AAA/BAA mean."""
    e = cm.yield_building_block("ig_corporates", market(config), settings)
    assert e.components["yield_pct"] == pytest.approx(6.0)
    base = settings.base_confidence(M.YIELD_BUILDING_BLOCK, "ig_corporates", "fixed_income")
    assert e.confidence == pytest.approx(base * settings.adjustments.fallback_input)


def test_stale_yields_are_unavailable(config, settings):
    x = market(config)
    x.macro = x.macro.loc[:"2025-12-31"]
    with pytest.raises(cm.Unavailable, match="days old"):
        cm.yield_building_block("intermediate_treasuries", x, settings)


def test_auto_blend_weights_by_confidence(config, settings):
    estimates = [
        CmaMethodEstimate(
            method=M.HISTORICAL_ERP, expected_return_pct=10.0, confidence=0.6, rationale="-"
        ),
        CmaMethodEstimate(
            method=M.SURVEY_CONSENSUS, expected_return_pct=4.0, confidence=0.2, rationale="-"
        ),
        cm.unavailable(M.INVERSE_GORDON, "missing"),
    ]
    blend = cm.auto_blend(estimates)
    assert blend.expected_return_pct == pytest.approx(0.75 * 10 + 0.25 * 4)
    assert blend.components == {"weight:historical_erp": 0.75, "weight:survey_consensus": 0.25}


def test_every_asset_lists_every_method_in_order(config, settings):
    x = market(config, shiller=shiller(cape=25.0))
    for asset in config.universe.assets:
        estimates = run_methods(asset.id, x, settings)
        assert [e.method for e in estimates] == list(CmaMethodId)
    gold = by_method(run_methods("gold", x, settings))
    assert gold[M.INVERSE_GORDON].unavailable_reason == "not applicable to real_assets"
    reits = by_method(run_methods("reits", x, settings))
    assert "not applicable" not in (reits[M.INVERSE_GORDON].unavailable_reason or "")


def test_settings_reject_unknown_series(config, settings):
    bad = settings.model_copy(deep=True)
    bad.yields["cash"][0].series = ["NOT_A_SERIES"]
    with pytest.raises(ValueError, match="NOT_A_SERIES"):
        bad.cross_validate(config)


# --------------------------------------------------------------------------- skill run
@pytest.fixture
def store(tmp_config):
    rng = np.random.default_rng(5)
    dates = pd.date_range("1994-01-31", "2026-07-31", freq="ME")
    frames = [
        pd.DataFrame(
            {
                "asset_id": a.id,
                "date": dates,
                "ret": rng.normal(0.006, 0.01 + 0.002 * i, len(dates)),
                "source": a.ticker,
                "kind": "etf",
                "priority": 0,
                "available_from": dates + pd.Timedelta(days=1),
            }
        )
        for i, a in enumerate(tmp_config.universe.assets)
    ]
    lake = DataLake(tmp_config.settings.data_dir)
    lake.write_dataset(
        "market/asset_returns_monthly", pd.concat(frames), run_id="r1", source="test"
    )
    macro_dates = pd.date_range("1990-01-31", "2026-08-31", freq="ME")
    macro = pd.concat(
        pd.DataFrame(
            {
                "series_id": sid,
                "date": macro_dates,
                "value": value,
                "realtime_start": pd.NaT,
                "realtime_end": pd.NaT,
                "available_from": macro_dates,
            }
        )
        for sid, value in {"DTB3": 4.0, "DGS1": 4.2, "DGS2": 4.3, "DGS3": 4.4}.items()
    )
    lake.write_dataset("macro/fred_observations", macro, run_id="r1", source="test")
    return DataStore(tmp_config)


def test_skill_writes_a_valid_contract_per_asset(store, tmp_config, tmp_path):
    result = run_cma_methods(store, as_of="2026-09-15", assets=["short_treasuries", "gold"])
    short = by_method(result.bodies["short_treasuries"].methods)
    assert short[M.YIELD_BUILDING_BLOCK].components["yield_pct"] == pytest.approx(4.3)
    assert short[M.REGIME_ADJUSTED].unavailable_reason == "no macro regime labels"
    assert result.bodies["gold"].horizon_years == tmp_config.ips.objectives.cma_horizon_years

    run = RunContext.create(tmp_config, as_of="2026-09-15", run_id="r", root=tmp_path / "run")
    written = write_outputs(result, run)
    loaded = read("cma_methods", run.path("cma_methods", asset_id="gold"))
    assert loaded.body.asset_id == "gold"
    assert loaded.header.report_path == "reports/cma_methods.md"
    assert "| gold |" in written[0].read_text(encoding="utf-8")

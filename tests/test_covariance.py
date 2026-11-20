import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from saa.contracts.portfolio import CovarianceBody, CovarianceMethod
from saa.contracts.registry import read
from saa.data.lake import DataLake
from saa.data.store import DataStore
from saa.run import RunContext
from saa.skills.covariance import (
    CovarianceSettings,
    compare_estimators,
    estimate_covariance,
    estimators,
    write_outputs,
)


def correlated_returns(t, n=6, seed=0, loadings=None):
    """T x N monthly returns on one common factor, volatilities from 1% to 6% a month.

    Correlation between i and j is loadings[i] * loadings[j]. Unequal loadings (the default)
    make correlations differ across pairs, as they do across asset classes."""
    rng = np.random.default_rng(seed)
    loadings = np.linspace(0.2, 0.9, n) if loadings is None else np.asarray(loadings, float)
    common = rng.normal(size=(t, 1))
    noise = rng.normal(size=(t, n))
    vols = np.linspace(0.01, 0.06, n)
    x = (common * loadings + noise * np.sqrt(1 - loadings**2)) * vols
    index = pd.date_range("1990-01-31", periods=t, freq="ME")
    return pd.DataFrame(x, index=index, columns=[f"a{i}" for i in range(n)])


# --------------------------------------------------------------------------- estimators
def test_sample_matches_pandas():
    r = correlated_returns(120)
    np.testing.assert_allclose(estimators.sample_covariance(r), r.cov().to_numpy())


def test_ledoit_wolf_keeps_variances_and_pulls_correlations_together():
    r = correlated_returns(60)
    shrunk, delta = estimators.ledoit_wolf(r)
    x = r.to_numpy() - r.to_numpy().mean(axis=0)
    mle = x.T @ x / len(x)
    assert 0.0 <= delta <= 1.0
    np.testing.assert_allclose(np.diag(shrunk), np.diag(mle))  # constant-correlation target
    r_bar = estimators.average_correlation(mle)
    before = np.abs(estimators.correlation_from(mle) - r_bar)
    after = np.abs(estimators.correlation_from(shrunk) - r_bar)
    assert (after <= before + 1e-12).all()
    assert estimators.is_positive_definite(shrunk)


def test_ledoit_wolf_shrinks_more_when_data_are_scarce():
    _, short = estimators.ledoit_wolf(correlated_returns(24, seed=1))
    _, long = estimators.ledoit_wolf(correlated_returns(2400, seed=1))
    assert short > long
    assert long < 0.2  # plenty of data and a misspecified target: trust the sample


def test_ledoit_wolf_trusts_the_target_when_it_is_true():
    """Equal loadings make every correlation equal, so the target is the truth."""
    _, delta = estimators.ledoit_wolf(correlated_returns(2400, seed=1, loadings=[0.6] * 6))
    assert delta > 0.5


def test_ledoit_wolf_repairs_a_singular_sample():
    """Fewer months than assets: the sample covariance is singular, the shrunk one is not."""
    r = correlated_returns(10, n=18, seed=2)
    assert not estimators.is_positive_definite(estimators.sample_covariance(r))
    assert estimators.is_positive_definite(estimators.ledoit_wolf(r)[0])


def test_exponential_with_a_long_halflife_is_the_sample():
    r = correlated_returns(120)
    np.testing.assert_allclose(
        estimators.exponential_covariance(r, 1e9), r.cov().to_numpy(), rtol=1e-6
    )


def test_exponential_reacts_to_a_recent_volatility_jump():
    r = correlated_returns(120)
    r.iloc[-12:] *= 3  # a volatile final year
    ewma = estimators.exponential_covariance(r, 12)
    sample = estimators.sample_covariance(r)
    assert (np.diag(ewma) > np.diag(sample)).all()


# --------------------------------------------------------------------------- contract units
def test_contract_rejects_a_percent_squared_matrix():
    with pytest.raises(ValidationError, match="decimal-squared"):
        CovarianceBody(
            asset_ids=["a"],
            method="sample",
            window_years=10,
            matrix=[[400.0]],  # 20% volatility written in percent-squared
            volatilities_pct={"a": 20.0},
        )


# --------------------------------------------------------------------------- skill run
@pytest.fixture
def store(tmp_config):
    rng = np.random.default_rng(3)
    dates = pd.date_range("1994-01-31", "2026-07-31", freq="ME")
    common = rng.normal(size=len(dates))
    frames = []
    for i, asset in enumerate(tmp_config.universe.assets):
        vol = 0.005 + 0.003 * i
        ret = vol * (0.5 * common + np.sqrt(0.75) * rng.normal(size=len(dates)))
        frames.append(
            pd.DataFrame(
                {
                    "asset_id": asset.id,
                    "date": dates,
                    "ret": ret,
                    "source": asset.ticker,
                    "kind": "etf",
                    "priority": 0,
                    "available_from": dates + pd.Timedelta(days=1),
                }
            )
        )
    DataLake(tmp_config.settings.data_dir).write_dataset(
        "market/asset_returns_monthly", pd.concat(frames), run_id="r1", source="test"
    )
    return DataStore(tmp_config)


def test_default_is_ledoit_wolf_over_all_history(store, config):
    result = estimate_covariance(store, as_of="2026-09-15")
    body = result.body
    assert body.method is CovarianceMethod.LEDOIT_WOLF
    assert body.asset_ids == [a.id for a in config.universe.assets]
    assert result.start.isoformat() == "1994-01-31"  # every month the fixture has
    assert body.shrinkage is not None
    assert result.end.isoformat() == "2026-07-31"
    assert result.positive_definite
    i = body.asset_ids.index("us_large_cap")
    assert body.volatilities_pct["us_large_cap"] == pytest.approx(100 * body.matrix[i][i] ** 0.5)


def test_a_fixed_window_uses_that_many_months(store):
    result = estimate_covariance(
        store, as_of="2026-09-15", settings=CovarianceSettings(window_years=10)
    )
    assert result.months == 120 and result.body.window_years == 10.0


def test_a_singular_matrix_is_refused(tmp_config, tmp_path):
    """Two assets with identical returns -- as International Sovereigns and Corporates are
    before 2007 -- make the sample covariance singular; Ledoit-Wolf repairs it."""
    rng = np.random.default_rng(4)
    dates = pd.date_range("1994-01-31", "2004-12-31", freq="ME")
    shared = rng.normal(0, 0.02, len(dates))
    frames = []
    for asset in tmp_config.universe.assets:
        ret = shared if asset.id in {"intl_sovereigns", "intl_corporates"} else None
        frames.append(
            pd.DataFrame(
                {
                    "asset_id": asset.id,
                    "date": dates,
                    "ret": ret if ret is not None else rng.normal(0, 0.03, len(dates)),
                    "source": "PROXY",
                    "kind": "active_fund",
                    "priority": 1,
                    "available_from": dates + pd.Timedelta(days=1),
                }
            )
        )
    DataLake(tmp_config.settings.data_dir).write_dataset(
        "market/asset_returns_monthly", pd.concat(frames), run_id="r1", source="test"
    )
    store = DataStore(tmp_config)
    results = compare_estimators(store, as_of="2005-06-30")
    assert not results[CovarianceMethod.SAMPLE].positive_definite
    assert results[CovarianceMethod.LEDOIT_WOLF].positive_definite

    run = RunContext.create(tmp_config, as_of="2005-06-30", run_id="r", root=tmp_path / "run")
    with pytest.raises(ValueError, match="singular"):
        write_outputs(CovarianceMethod.SAMPLE, results, run, store.provenance())
    write_outputs(CovarianceMethod.LEDOIT_WOLF, results, run, store.provenance())


def test_as_of_excludes_months_not_yet_available(store):
    assert estimate_covariance(store, as_of="2026-07-31").end.isoformat() == "2026-06-30"


def test_compare_returns_every_estimator_on_the_same_window(store):
    results = compare_estimators(store, as_of="2026-09-15")
    assert set(results) == {
        CovarianceMethod.SAMPLE,
        CovarianceMethod.LEDOIT_WOLF,
        CovarianceMethod.EXPONENTIAL,
        CovarianceMethod.RECENT_VOLATILITY,
    }
    assert len({r.end for r in results.values()}) == 1


def test_regime_conditional_uses_only_that_regimes_months(store):
    idx = pd.date_range("1994-01-31", "2026-07-31", freq="ME")
    labels = pd.Series(np.where(idx.year % 4 == 0, "recession", "expansion"), index=idx)
    result = estimate_covariance(
        store,
        as_of="2026-09-15",
        method="regime_conditional",
        regime="recession",
        regime_labels=labels,
    )
    assert result.body.regime == "recession"
    assert result.months == int((labels == "recession").sum())
    assert result.positive_definite


def test_regime_conditional_refuses_too_few_months(store):
    idx = pd.date_range("1994-01-31", "2026-07-31", freq="ME")
    labels = pd.Series("expansion", index=idx)
    labels.iloc[:5] = "recession"
    with pytest.raises(ValueError, match="need 24"):
        estimate_covariance(
            store,
            as_of="2026-09-15",
            method="regime_conditional",
            regime="recession",
            regime_labels=labels,
        )


def test_outputs_are_a_valid_contract_in_the_run(store, tmp_config, tmp_path):
    run = RunContext.create(tmp_config, as_of="2026-09-15", run_id="r", root=tmp_path / "run")
    results = compare_estimators(store, as_of="2026-09-15", settings=CovarianceSettings())
    paths = write_outputs(CovarianceMethod.LEDOIT_WOLF, results, run, store.provenance())
    assert paths[0] == run.root / "pc" / "covariance.json"
    loaded = read("covariance", paths[0])
    assert loaded.body.method is CovarianceMethod.LEDOIT_WOLF
    assert loaded.header.report_path == "reports/covariance.md"
    assert "| ledoit_wolf |" in (run.root / "reports" / "covariance.md").read_text(encoding="utf-8")


# ------------------------------------------------------------ validation (decision 63)
from saa.agents.covariance import judgment_model, run_covariance  # noqa: E402
from saa.contracts.portfolio import CovarianceJudgment  # noqa: E402
from saa.llm import LlmClient  # noqa: E402
from saa.skills.covariance import VALIDATED, validate_estimators  # noqa: E402
from saa.skills.portfolio_construction.analysis import benchmark_weights  # noqa: E402
from tests.test_macro_agent import FakeAnthropic  # noqa: E402


def regime_labels(dates: pd.DatetimeIndex) -> pd.Series:
    """Alternating two-year regimes, so every label has enough months to condition on."""
    names = np.where((dates.year // 2) % 2 == 0, "expansion", "late_cycle")
    return pd.Series(names, index=dates, name="regime")


def test_validation_scores_every_estimator_out_of_sample(store, tmp_config):
    dates = pd.date_range("1994-01-31", "2026-07-31", freq="ME")
    records = validate_estimators(
        store,
        as_of="2026-09-15",
        benchmark=benchmark_weights(tmp_config),
        regime_labels=regime_labels(dates),
    )
    assert {r.method for r in records} == set(VALIDATED)
    for r in records:
        # The fixture's returns are stationary, so an estimator fitted on the past should be
        # roughly unbiased about the next year.
        assert 0.7 < r.realised_to_forecast < 1.3
        assert r.abs_log_error >= 0.0
        assert r.stock_bond_correlation_error is not None
    # The panel ends 2026-07, so year-ends 1999..2024 have a full following year.
    lw = next(r for r in records if r.method is CovarianceMethod.LEDOIT_WOLF)
    assert lw.years == 2024 - 1999 + 1


def test_validation_uses_only_data_known_at_each_year_end(store, tmp_config):
    """A cutoff in 2010 can score only year-ends whose next 12 months precede it."""
    records = validate_estimators(
        store, as_of="2010-06-30", benchmark=benchmark_weights(tmp_config)
    )
    assert {r.method for r in records} == {
        CovarianceMethod.LEDOIT_WOLF,
        CovarianceMethod.EXPONENTIAL,
        CovarianceMethod.RECENT_VOLATILITY,
    }  # no labels, no regime record
    assert all(r.years == 2008 - 1999 + 1 for r in records)


# ------------------------------------------------------------------ the covariance agent
def test_the_agent_without_a_model_keeps_the_ledoit_wolf_default(store, tmp_config, tmp_path):
    run = RunContext.create(tmp_config, as_of="2026-09-15", run_id="r", root=tmp_path / "run")
    result = run_covariance(run, store, config=tmp_config, llm=None)
    out = read("covariance", run.path("covariance"))
    assert out.body.method is CovarianceMethod.LEDOIT_WOLF
    assert out.body.judgment.method is CovarianceMethod.LEDOIT_WOLF
    assert "--no-llm" in out.body.judgment.rationale
    assert out.body.validation and out.header.produced_by.value == "script"
    assert result.cost_usd == 0.0
    assert "Out-of-sample record" in run.report_path("covariance.md").read_text(encoding="utf-8")


def test_the_agent_hands_on_the_estimator_the_model_chose(store, tmp_config, tmp_path):
    dates = pd.date_range("1994-01-31", "2026-07-31", freq="ME")
    run = RunContext.create(tmp_config, as_of="2026-09-15", run_id="r", root=tmp_path / "run")
    payload = {
        "method": "exponential",
        "rationale": "The estimators disagree on the stock-bond correlation and exponential has "
        "the smallest error on it, so recent years should weigh more. " * 3,
        "what_would_change_it": "A confident regime call with enough labelled months.",
    }
    fake = FakeAnthropic([payload])
    run_covariance(
        run, store, config=tmp_config, llm=LlmClient(fake), regime_labels=regime_labels(dates)
    )
    out = read("covariance", run.path("covariance"))
    assert out.body.method is CovarianceMethod.EXPONENTIAL
    assert out.body.judgment.method is CovarianceMethod.EXPONENTIAL
    assert out.header.produced_by.value == "hybrid" and out.header.model_calls
    prompt = fake.messages.calls[0]["messages"][0]["content"]
    assert "Out-of-sample record" in prompt and "Stock-bond corr" in prompt
    assert "Risk parity vol" in prompt  # what the risk-only methods will see (decision 65)
    assert "recent_volatility" in prompt and "regime_blend" in prompt
    assert "regime_conditional" in prompt  # on offer: the labels have enough months


def test_the_model_may_choose_only_an_estimator_on_offer():
    model = judgment_model([CovarianceMethod.LEDOIT_WOLF, CovarianceMethod.EXPONENTIAL])
    ok = {"method": "exponential", "rationale": "r", "what_would_change_it": "w"}
    assert isinstance(model.model_validate(ok), CovarianceJudgment)
    with pytest.raises(ValidationError):
        model.model_validate({**ok, "method": "sample"})


# ------------------------------------------------------------ decision 65 estimators
def test_recent_volatility_keeps_long_run_correlations_and_tracks_recent_volatility():
    calm = correlated_returns(300, seed=4)
    stormy = calm.copy()
    stormy.iloc[-24:, 0] *= 3.0  # the first asset's last two years are three times as volatile
    cov, shrinkage = estimators.recent_volatility_covariance(stormy, halflife_months=6)
    long_run, lw_shrinkage = estimators.ledoit_wolf(stormy)
    np.testing.assert_allclose(
        estimators.correlation_from(cov), estimators.correlation_from(long_run), atol=1e-12
    )
    assert shrinkage == lw_shrinkage
    assert np.sqrt(cov[0, 0]) > 1.5 * np.sqrt(long_run[0, 0])  # recent turbulence shows
    assert np.sqrt(cov[-1, -1]) == pytest.approx(np.sqrt(long_run[-1, -1]), rel=0.5)


def test_a_blend_with_all_weight_on_one_regime_is_that_regimes_ledoit_wolf():
    x = correlated_returns(240, seed=5)
    labels = pd.Series(np.where(np.arange(240) < 120, "expansion", "recession"))
    cov, used = estimators.regime_blend_covariance(x, labels, {"recession": 1.0}, 24)
    expected, _ = estimators.ledoit_wolf(x.iloc[120:])
    np.testing.assert_allclose(cov, expected)
    assert used == {"recession": 1.0}


def test_the_blend_adds_the_spread_between_regime_means():
    """Law of total covariance: two regimes with different means co-move through the switch."""
    x = correlated_returns(240, seed=6)
    x.iloc[120:] += 0.03  # every asset returns 3% a month more in the second regime
    labels = pd.Series(np.where(np.arange(240) < 120, "a", "b"))
    cov, _ = estimators.regime_blend_covariance(x, labels, {"a": 0.5, "b": 0.5}, 24)
    within = (
        0.5 * estimators.ledoit_wolf(x.iloc[:120])[0]
        + 0.5 * estimators.ledoit_wolf(x.iloc[120:])[0]
    )
    gap = x.iloc[120:].mean().to_numpy() - x.iloc[:120].mean().to_numpy()  # about 3% each
    np.testing.assert_allclose(cov - within, 0.25 * np.outer(gap, gap), atol=1e-12)
    assert (np.diag(cov - within) > 0.25 * 0.02**2).all()


def test_a_regime_with_too_few_months_is_dropped_and_the_rest_renormalised():
    x = correlated_returns(120, seed=7)
    labels = pd.Series(["expansion"] * 110 + ["recession"] * 10)
    _, used = estimators.regime_blend_covariance(
        x, labels, {"expansion": 0.6, "recession": 0.4}, 24
    )
    assert used == {"expansion": pytest.approx(1.0)}
    with pytest.raises(ValueError, match="no regime"):
        estimators.regime_blend_covariance(x, labels, {"recession": 1.0}, 24)


def test_blend_weights_follow_the_macro_view():
    labels = pd.Series(["expansion"] * 50 + ["late_cycle"] * 30 + ["recession"] * 20)
    base = estimators.blend_weights(labels, None, None)
    assert base == pytest.approx({"expansion": 0.5, "late_cycle": 0.3, "recession": 0.2})
    w = estimators.blend_weights(labels, "late_cycle", 0.6)
    assert w["late_cycle"] == pytest.approx(0.6 + 0.4 * 0.3)
    assert sum(w.values()) == pytest.approx(1.0)
    r = estimators.blend_weights(labels, "late_cycle", 0.6, recession_probability=0.25)
    assert r["recession"] == pytest.approx(0.25)
    assert sum(r.values()) == pytest.approx(1.0)
    # The non-recession regimes keep their proportions.
    assert r["late_cycle"] / r["expansion"] == pytest.approx(w["late_cycle"] / w["expansion"])


def test_compare_offers_the_new_estimators(store):
    dates = pd.date_range("1994-01-31", "2026-07-31", freq="ME")
    labels = regime_labels(dates)
    weights = estimators.blend_weights(labels, "expansion", 0.5)
    estimates = compare_estimators(
        store, as_of="2026-09-15", regime="expansion", regime_labels=labels, regime_weights=weights
    )
    assert CovarianceMethod.RECENT_VOLATILITY in estimates
    blend = estimates[CovarianceMethod.REGIME_BLEND]
    assert blend.positive_definite
    assert blend.body.regime_weights == pytest.approx(weights)

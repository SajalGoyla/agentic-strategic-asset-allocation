import json
import math

import numpy as np
import pandas as pd
import pytest

from saa.data.lake import DataLake
from saa.data.store import DataStore
from saa.skills.historical_analysis import metrics as m
from saa.skills.historical_analysis import run_historical_analysis, write_outputs

MONTHS = pd.date_range("2020-01-31", periods=4, freq="ME")


# --------------------------------------------------------------------------- metrics
def test_annualized_return_and_volatility():
    r = pd.Series([0.01] * 24, index=pd.date_range("2020-01-31", periods=24, freq="ME"))
    assert m.annualized_return(r) == pytest.approx(1.01**12 - 1)
    assert m.annualized_volatility(r) == pytest.approx(0.0)


def test_sharpe_and_sortino():
    rf = pd.Series(0.0, index=MONTHS)
    assert m.sharpe_ratio(pd.Series([0.02, 0.0, 0.02, 0.0], index=MONTHS), rf) == pytest.approx(3.0)
    sortino = m.sortino_ratio(pd.Series([0.03, -0.01, 0.03, -0.01], index=MONTHS), rf)
    assert sortino == pytest.approx(2 * math.sqrt(6))


def test_max_drawdown_dates_and_recovery():
    dd = m.max_drawdown(pd.Series([0.1, -0.5, 0.2, 0.8], index=MONTHS))
    assert dd.depth == pytest.approx(-0.5)
    assert (dd.peak, dd.trough, dd.recovery) == (MONTHS[0], MONTHS[1], MONTHS[3])
    assert dd.duration_months == 3
    assert m.current_drawdown(pd.Series([0.1, -0.5, 0.2, 0.8], index=MONTHS)) == 0.0


def test_drawdown_from_window_start_and_unrecovered():
    dd = m.max_drawdown(pd.Series([-0.2, 0.1], index=MONTHS[:2]))
    assert dd.peak is None and dd.recovery is None
    assert dd.depth == pytest.approx(-0.2)
    assert dd.duration_months == 2


def test_var_and_cvar():
    r = pd.Series(np.round(np.arange(-0.10, 0.10, 0.01), 2))
    assert m.value_at_risk(r) == pytest.approx(0.0905)
    assert m.conditional_value_at_risk(r) == pytest.approx(0.10)
    assert math.isnan(m.value_at_risk(r.head(5)))


def test_conditional_stats_by_label():
    idx = pd.date_range("2000-01-31", periods=24, freq="ME")
    labels = pd.Series(["expansion", "recession"] * 12, index=idx)
    r = pd.Series(np.where(labels == "expansion", 0.01, -0.01), index=idx)
    out = m.conditional_stats(r, pd.Series(0.0, index=idx), labels).set_index("regime")
    assert out.loc["expansion", "annualized_mean_return"] == pytest.approx(0.12)
    assert out.loc["recession", "hit_rate"] == 0.0


def test_realized_volatility_needs_enough_days():
    daily = pd.Series(np.random.default_rng(0).normal(0, 0.01, 30))
    assert math.isnan(m.realized_volatility(daily, 63))


# --------------------------------------------------------------------------- skill run
@pytest.fixture
def store(tmp_config):
    lake = DataLake(tmp_config.settings.data_dir)
    rng = np.random.default_rng(7)
    dates = pd.date_range("1995-01-31", "2026-07-31", freq="ME")
    etf_start = pd.Timestamp("2005-01-31")
    frames = []
    for i, asset in enumerate(tmp_config.universe.assets):
        start = pd.Timestamp("2020-01-31") if asset.id == "intl_corporates" else dates[0]
        d = dates[dates >= start]
        is_etf = d >= etf_start
        frames.append(
            pd.DataFrame(
                {
                    "asset_id": asset.id,
                    "date": d,
                    "ret": rng.normal(0.005, 0.02 + 0.002 * i, len(d)),
                    "source": np.where(is_etf, asset.ticker, "PROXY"),
                    "kind": np.where(is_etf, "etf", "index_fund"),
                    "priority": np.where(is_etf, 0, 1),
                    "available_from": d + pd.Timedelta(days=1),
                }
            )
        )
    lake.write_dataset(
        "market/asset_returns_monthly", pd.concat(frames), run_id="r1", source="test"
    )

    tbill_dates = pd.date_range("1994-12-31", "2026-07-31", freq="ME")
    lake.write_dataset(
        "macro/fred_observations",
        pd.DataFrame(
            {
                "series_id": "DTB3",
                "date": tbill_dates,
                "value": 2.4,
                "realtime_start": pd.NaT,
                "realtime_end": pd.NaT,
                "available_from": tbill_dates + pd.Timedelta(days=1),
            }
        ),
        run_id="r1",
        source="test",
    )

    days = pd.bdate_range(end="2026-08-14", periods=300)
    px = 100 * np.cumprod(1 + rng.normal(0, 0.01, len(days)))
    prices = pd.DataFrame({"date": days, "ticker": "SPY", "adj_close": px})
    for col in ("open", "high", "low", "close", "volume"):
        prices[col] = px
    prices[["dividends", "splits", "capital_gains"]] = 0.0
    lake.write_dataset("market/prices_daily", prices, run_id="r1", source="test")
    return DataStore(tmp_config)


def test_run_covers_all_assets_and_windows(store):
    analysis = run_historical_analysis(store, as_of="2026-09-15")
    assert len(analysis.assets) == 18
    assert analysis.data_end.isoformat() == "2026-07-31"
    spy = next(a for a in analysis.assets if a.asset_id == "us_large_cap")
    ten = spy.windows["10y"]
    assert ten.sufficient and ten.months == 120
    assert ten.proxy_share == 0.0 and spy.windows["full"].proxy_share > 0
    assert ten.correlation_to_us_large_cap == pytest.approx(1.0)
    assert [s.kind for s in spy.sources] == ["index_fund", "etf"]
    assert spy.recent_daily_volatility["3m"] is not None
    assert analysis.risk_free["current_annual_yield_pct"] == pytest.approx(2.4)
    assert set(spy.provenance) >= {"market/asset_returns_monthly", "macro/fred_observations"}


def test_short_history_windows_are_null_not_misleading(store):
    analysis = run_historical_analysis(store, as_of="2026-09-15")
    corp = next(a for a in analysis.assets if a.asset_id == "intl_corporates")
    assert corp.windows["5y"].sufficient
    assert not corp.windows["10y"].sufficient
    assert corp.windows["10y"].annualized_return is None
    assert corp.recent_daily_volatility == {"3m": None, "1y": None}


def test_point_in_time_excludes_returns_not_yet_available(store):
    analysis = run_historical_analysis(store, as_of="2026-07-31")
    assert analysis.data_end.isoformat() == "2026-06-30"


def test_correlation_rows_exclude_self(store):
    analysis = run_historical_analysis(store, as_of="2026-09-15")
    row = next(r for r in analysis.correlation_rows if r.asset_id == "gold")
    assert len(row.correlations["5y"]) == 17 and "gold" not in row.correlations["5y"]
    assert all(-1 <= v <= 1 for v in row.correlations["5y"].values())
    assert row.months["5y"] == 60
    assert analysis.stock_bond_correlation.window_months == 36


def test_regime_stats_when_labels_supplied(store):
    idx = pd.date_range("1995-01-31", "2026-07-31", freq="ME")
    labels = pd.Series(np.where(idx.year % 2 == 0, "expansion", "recession"), index=idx)
    analysis = run_historical_analysis(store, as_of="2026-09-15", regime_labels=labels)
    regimes = {s.regime for s in analysis.regime_stats["cash"]}
    assert regimes == {"expansion", "recession"}


def test_write_outputs_produce_strict_json(store, tmp_path):
    analysis = run_historical_analysis(store, as_of="2026-09-15")
    out = write_outputs(analysis, tmp_path / "ha")

    def reject(constant):
        raise ValueError(f"non-JSON constant {constant}")

    for path in [out / "historical_analysis.json", *out.glob("assets/*/*.json")]:
        json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)
    assert len(list(out.glob("assets/*/historical_stats.json"))) == 18
    assert "| US Large Cap (SPY) |" in (out / "summary.md").read_text(encoding="utf-8")

"""The signals skill: scoring, sign conventions and the composite."""

import numpy as np
import pandas as pd
import pytest

from saa.contracts import SignalCategory
from saa.skills.signals import (
    AssetSignals,
    composite,
    load_signal_settings,
    run_signals,
    score_against_history,
)
from tests.conftest import monthly, write_macro_lake


@pytest.fixture(scope="session")
def signal_settings(config):
    return load_signal_settings(config)


def signal(name, category, score):
    out = AssetSignals("x")
    out.add(name, category, score, "…")
    return out.signals[0]


# ---------------------------------------------------------------------------------- scoring
def test_a_reading_above_its_history_scores_positive():
    series = monthly([*([1.0] * 60), 5.0])
    assert score_against_history(series, lookback_years=20, min_months=36) > 0.5


def test_a_reading_below_its_history_scores_negative():
    series = monthly([*([5.0] * 60), 1.0])
    assert score_against_history(series, lookback_years=20, min_months=36) < -0.5


def test_scores_stay_inside_the_unit_interval():
    series = monthly([*np.random.default_rng(0).normal(0, 1, 60), 500.0])
    assert -1.0 <= score_against_history(series, lookback_years=20, min_months=36) <= 1.0


def test_too_little_history_scores_nothing_rather_than_guessing():
    assert score_against_history(monthly([1.0, 2.0, 3.0]), lookback_years=20, min_months=36) is None


def test_a_flat_series_carries_no_information():
    assert score_against_history(monthly([2.0] * 60), lookback_years=20, min_months=36) is None


def test_an_unscorable_signal_is_dropped_not_defaulted():
    out = AssetSignals("x")
    out.add("a", SignalCategory.TECHNICAL, None, "…")
    assert out.signals == []


# -------------------------------------------------------------------------------- composite
def test_composite_follows_its_members(signal_settings):
    bullish = [signal("momentum_12_1", SignalCategory.TECHNICAL, 0.8)]
    bearish = [signal("momentum_12_1", SignalCategory.TECHNICAL, -0.8)]
    assert composite(bullish, signal_settings) > 0
    assert composite(bearish, signal_settings) < 0
    assert composite([], signal_settings) == 0.0


def test_a_missing_category_renormalises_rather_than_diluting(signal_settings):
    """An asset with no valuation signal is scored on what it has, not dragged toward zero."""
    technical_only = [
        signal("momentum_12_1", SignalCategory.TECHNICAL, 1.0),
        signal("trend", SignalCategory.TECHNICAL, 1.0),
        signal("mean_reversion", SignalCategory.TECHNICAL, 1.0),
        signal("relative_momentum", SignalCategory.TECHNICAL, 1.0),
    ]
    assert composite(technical_only, signal_settings) == pytest.approx(1.0)


def test_composite_stays_inside_the_unit_interval(signal_settings):
    extreme = [
        signal("momentum_12_1", SignalCategory.TECHNICAL, 1.0),
        signal("cape", SignalCategory.VALUATION, 1.0),
        signal("regime_fit", SignalCategory.MACRO, 1.0),
    ]
    assert composite(extreme, signal_settings) == pytest.approx(1.0)


# ----------------------------------------------------------------------------- shipped config
def test_shipped_config_is_valid(signal_settings, config):
    assert set(signal_settings.category_weights) == {"technical", "valuation", "macro"}
    known = {a.id for a in config.universe.assets}
    assert set(signal_settings.yield_levels) <= known
    assert set(signal_settings.credit_spreads) <= known


def test_fixed_income_assets_all_have_a_yield_signal(config, signal_settings):
    """Yield level is the strongest valuation signal for a bond; none should be left without."""
    bonds = {a.id for a in config.universe.assets if a.group in {"fixed_income", "cash"}}
    assert bonds <= set(signal_settings.yield_levels)


def test_sentiment_is_absent_by_design(signal_settings):
    """Exhibit 3 step 5 sources it from web search, which the pipeline does not do yet."""
    assert "sentiment" not in signal_settings.category_weights


# ------------------------------------------------------------------------------ integration
def test_signals_run_over_a_synthetic_lake(tmp_config, signal_settings):
    rng = np.random.default_rng(3)
    assets = [a.id for a in tmp_config.universe.assets]
    months = pd.date_range("2000-01-31", periods=240, freq="ME")
    returns = pd.DataFrame(
        rng.normal(0.6, 3.5, (len(months), len(assets))), index=months, columns=assets
    )

    store = write_macro_lake(tmp_config, {"DGS10": monthly(rng.normal(3, 0.6, 240), "2000-01-31")})
    frame = returns.stack().rename("ret").reset_index()
    frame.columns = ["date", "asset_id", "ret"]
    frame["source"] = "test"
    frame["kind"] = "test"
    frame["priority"] = 1
    frame["available_from"] = frame["date"]
    store.lake.write_dataset("market/asset_returns_monthly", frame, run_id="r1", source="test")

    labels = pd.Series("expansion", index=months)
    scores = pd.DataFrame(
        {
            d: rng.normal(0, 0.3, len(months))
            for d in ("growth", "inflation", "monetary_policy", "financial_conditions")
        },
        index=months,
    )
    result = run_signals(
        store, regime_labels=labels, dimension_scores=scores, settings=signal_settings
    )

    assert set(result.bodies) == set(assets)
    for body in result.bodies.values():
        assert -1.0 <= body.composite_score <= 1.0
        assert all(-1.0 <= s.score <= 1.0 for s in body.signals)
    # Technical signals need only returns, so every asset should have some.
    assert all(
        any(s.category is SignalCategory.TECHNICAL for s in b.signals)
        for b in result.bodies.values()
    )


def test_relative_momentum_ranks_across_the_universe(tmp_config, signal_settings):
    """The one signal that compares assets with each other rather than with their own past."""
    assets = [a.id for a in tmp_config.universe.assets]
    months = pd.date_range("2000-01-31", periods=120, freq="ME")
    # A clean cross-sectional ordering: the first asset compounds fastest.
    returns = pd.DataFrame(
        {a: np.full(len(months), 0.2 * (len(assets) - i)) for i, a in enumerate(assets)},
        index=months,
    )
    store = write_macro_lake(tmp_config, {"DGS10": monthly(np.full(120, 3.0), "2000-01-31")})
    frame = returns.stack().rename("ret").reset_index()
    frame.columns = ["date", "asset_id", "ret"]
    frame["source"] = frame["kind"] = "test"
    frame["priority"] = 1
    frame["available_from"] = frame["date"]
    store.lake.write_dataset("market/asset_returns_monthly", frame, run_id="r1", source="test")

    result = run_signals(store, settings=signal_settings)

    def relative(asset_id):
        return next(
            s.score for s in result.bodies[asset_id].signals if s.name == "relative_momentum"
        )

    assert relative(assets[0]) == pytest.approx(1.0)
    assert relative(assets[-1]) < relative(assets[0])

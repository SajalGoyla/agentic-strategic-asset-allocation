"""The risk skill: the backtest, the metrics and the composite risk score."""

import numpy as np
import pandas as pd
import pytest

from saa.contracts import PcCategory
from saa.skills.risk import (
    MIN_BACKTEST_MONTHS,
    RISK_SCORE_WEIGHTS,
    backtest_returns,
    backtest_stats,
    factor_tilts,
    profile_portfolio,
    risk_score,
)
from tests.test_cma_judge import IDS, stage_inputs


def months(n, start="2000-01-31"):
    return pd.date_range(start, periods=n, freq="ME")


# ---------------------------------------------------------------------------------- backtest
def test_a_single_asset_portfolio_returns_that_asset():
    index = months(12)
    returns = pd.DataFrame({"a": np.full(12, 0.01), "b": np.full(12, -0.05)}, index=index)
    held = backtest_returns(pd.Series({"a": 1.0, "b": 0.0}), returns)
    assert held.to_numpy() == pytest.approx(np.full(12, 0.01))


def test_weights_drift_between_rebalances_and_snap_back_on_the_cadence():
    """The whole point of the cadence: a quarterly portfolio is not a monthly one."""
    index = months(6)
    # One asset compounds, the other is flat, so drift is visible in the portfolio return.
    returns = pd.DataFrame({"a": np.full(6, 0.10), "b": np.zeros(6)}, index=index)
    weights = pd.Series({"a": 0.5, "b": 0.5})

    quarterly = backtest_returns(weights, returns, rebalance_months=3)
    monthly_ = backtest_returns(weights, returns, rebalance_months=1)

    # Month 1 is identical; by month 3 the quarterly portfolio holds more of the winner.
    assert quarterly.iloc[0] == pytest.approx(monthly_.iloc[0])
    assert quarterly.iloc[2] > monthly_.iloc[2]
    # Month 4 follows a rebalance, so it matches the monthly portfolio again.
    assert quarterly.iloc[3] == pytest.approx(monthly_.iloc[3])


def test_buy_and_hold_never_rebalances():
    index = months(6)
    returns = pd.DataFrame({"a": np.full(6, 0.10), "b": np.zeros(6)}, index=index)
    weights = pd.Series({"a": 0.5, "b": 0.5})
    held = backtest_returns(weights, returns, rebalance_months=0)
    assert held.is_monotonic_increasing  # drifting ever further into the compounding asset


def test_a_portfolio_with_no_weight_in_the_panel_is_an_error():
    returns = pd.DataFrame({"a": [0.01, 0.02]}, index=months(2))
    with pytest.raises(ValueError, match="no weight on any asset"):
        backtest_returns(pd.Series({"b": 1.0}), returns)


# ------------------------------------------------------------------------------ backtest stats
def test_too_little_history_reports_nothing_rather_than_guessing():
    short = pd.Series(np.full(MIN_BACKTEST_MONTHS - 1, 0.01), index=months(MIN_BACKTEST_MONTHS - 1))
    assert backtest_stats(short) is None


def test_backtest_stats_are_annualised_percent_with_the_papers_signs():
    rng = np.random.default_rng(0)
    series = pd.Series(rng.normal(0.006, 0.04, 240), index=months(240))
    stats = backtest_stats(series, risk_free=0.03)

    assert stats.months == 240
    # 4% monthly volatility annualises to roughly 14%.
    assert 10 < stats.volatility_pct < 18
    assert stats.max_drawdown_pct < 0, "a drawdown is negative"
    assert stats.var_95_pct > 0, "VaR is a positive loss"
    assert stats.cvar_95_pct >= stats.var_95_pct, "expected shortfall is at least the quantile"


def test_beta_against_an_identical_benchmark_is_one():
    rng = np.random.default_rng(1)
    series = pd.Series(rng.normal(0.005, 0.03, 120), index=months(120))
    assert backtest_stats(series, benchmark=series).beta == pytest.approx(1.0)


def test_a_higher_risk_free_rate_lowers_the_sharpe():
    rng = np.random.default_rng(2)
    series = pd.Series(rng.normal(0.008, 0.03, 120), index=months(120))
    assert (
        backtest_stats(series, risk_free=0.0).sharpe > backtest_stats(series, risk_free=0.06).sharpe
    )


def test_the_risk_free_path_is_subtracted_month_by_month():
    """Cash yielded 5% in 2000 and 0% in 2010; a single rate would misstate both halves."""
    rng = np.random.default_rng(3)
    index = months(240)
    series = pd.Series(rng.normal(0.008, 0.03, 240), index=index)
    falling = pd.Series(np.linspace(0.005, 0.0, 240), index=index)  # mean 0.0025 monthly
    flat = 12 * float(falling.mean())  # the same average rate, as a single annual number

    path = backtest_stats(series, risk_free=falling)
    single = backtest_stats(series, risk_free=flat)
    # The means agree, so only the path differs -- and it changes the excess volatility.
    assert path.sharpe != pytest.approx(single.sharpe)


def test_a_portfolio_whose_worst_months_are_gains_has_a_negative_var():
    """Not an error: cash over much of 1993-2026. The contract must not force a positive loss."""
    series = pd.Series(np.full(120, 0.003) + np.linspace(0, 1e-4, 120), index=months(120))
    stats = backtest_stats(series)
    assert stats.var_95_pct < 0
    assert stats.cvar_95_pct >= stats.var_95_pct


# -------------------------------------------------------------------------------- factor tilts
def test_the_benchmark_has_no_tilt_against_itself(config):
    benchmark = pd.Series(config.ips.active_risk.benchmark.weights)
    tilts = factor_tilts(benchmark, benchmark, config)
    assert all(value == pytest.approx(0.0) for value in tilts.values())


def test_active_group_tilts_sum_to_zero(config):
    benchmark = pd.Series(config.ips.active_risk.benchmark.weights)
    portfolio = pd.Series({"gold": 0.5, "cash": 0.5})
    tilts = factor_tilts(portfolio, benchmark, config, beta=0.4)
    active = [v for k, v in tilts.items() if k.startswith("active_")]
    assert sum(active) == pytest.approx(0.0)
    assert tilts["active_real_assets"] == pytest.approx(0.5)
    assert tilts["active_equity"] == pytest.approx(-0.60)
    assert tilts["benchmark_beta"] == 0.4


def test_beta_is_absent_without_a_backtest(config):
    benchmark = pd.Series(config.ips.active_risk.benchmark.weights)
    assert "benchmark_beta" not in factor_tilts(benchmark, benchmark, config)


# ---------------------------------------------------------------------------------- risk score
def _score(config, **overrides):
    kwargs = {
        "ex_ante_volatility_pct": 10.0,
        "max_drawdown_pct": -12.0,
        "var_95_pct": 4.0,
        "tracking_error_pct": 3.0,
        "concentration_hhi": 0.2,
        "n_assets": 18,
    }
    kwargs.update(overrides)
    return risk_score(config.ips, **kwargs)


def test_the_score_rises_with_volatility(config):
    low, _ = _score(config, ex_ante_volatility_pct=8.0)
    high, _ = _score(config, ex_ante_volatility_pct=12.0)
    assert high > low


def test_a_portfolio_below_the_volatility_floor_is_not_scored_as_risky(config):
    """It is non-compliant, not dangerous. Conflating the two inverts the whole ranking."""
    floor, components = _score(config, ex_ante_volatility_pct=8.0)
    far_below, below_components = _score(config, ex_ante_volatility_pct=2.0)
    assert below_components["volatility"] == 0.0
    assert far_below == pytest.approx(floor)


def test_the_score_is_bounded_however_extreme_the_inputs(config):
    worst, _ = _score(
        config,
        ex_ante_volatility_pct=80.0,
        max_drawdown_pct=-95.0,
        var_95_pct=40.0,
        tracking_error_pct=50.0,
        concentration_hhi=1.0,
        n_assets=18,
    )
    best, _ = _score(
        config,
        ex_ante_volatility_pct=1.0,
        max_drawdown_pct=0.0,
        var_95_pct=0.0,
        tracking_error_pct=0.0,
        concentration_hhi=1 / 18,
    )
    assert worst == pytest.approx(1.0)
    assert best == pytest.approx(0.0)


def test_a_missing_component_renormalises_rather_than_reading_as_safe(config):
    """No backtest must not be worth a free pass on a quarter of the score."""
    with_backtest, full = _score(config)
    without, partial = _score(config, max_drawdown_pct=None, var_95_pct=None)

    assert set(full) == set(RISK_SCORE_WEIGHTS)
    assert set(partial) == {"volatility", "tracking_error", "concentration"}
    # The remaining components are identical, so the renormalised score equals their own blend.
    weight = sum(RISK_SCORE_WEIGHTS[name] for name in partial)
    expected = sum(RISK_SCORE_WEIGHTS[n] * partial[n] for n in partial) / weight
    assert without == pytest.approx(expected)
    assert without != pytest.approx(with_backtest)


def test_every_component_is_weighted_and_the_weights_sum_to_one():
    assert sum(RISK_SCORE_WEIGHTS.values()) == pytest.approx(1.0)


# -------------------------------------------------------------------------------- the profile
def test_a_profile_covers_every_metric_the_paper_lists(tmp_config):
    stage = stage_inputs(tmp_config)
    profile = profile_portfolio(
        "equal_weight",
        "Equal weight",
        PcCategory.HEURISTIC,
        pd.Series({asset: 1 / len(IDS) for asset in IDS}),
        config=tmp_config,
        covariance=stage.covariance,
        benchmark=stage.benchmark,
        inflation_pct=stage.inflation_pct,
        expected_return_pct=6.0,
        scenario_returns=stage.scenario_returns,
        risk_free_series=stage.scenario_returns["cash"],
    )

    assert profile.has_backtest
    assert profile.ex_ante_volatility_pct > 0
    assert profile.backtest_volatility_pct > 0
    assert profile.var_95_pct > 0
    assert profile.max_drawdown_pct < 0
    assert profile.effective_n == pytest.approx(len(IDS))
    assert profile.concentration_hhi == pytest.approx(1 / len(IDS))
    assert 0.0 <= profile.risk_score <= 1.0
    assert set(profile.risk_score_components) == set(RISK_SCORE_WEIGHTS)


def test_without_a_return_panel_the_backtest_figures_are_absent(tmp_config):
    stage = stage_inputs(tmp_config)
    profile = profile_portfolio(
        "cash_only",
        "Cash",
        PcCategory.HEURISTIC,
        pd.Series({"cash": 1.0}),
        config=tmp_config,
        covariance=stage.covariance,
        benchmark=stage.benchmark,
        scenario_returns=None,
    )
    assert not profile.has_backtest
    assert profile.max_drawdown_pct is None
    assert "drawdown" not in profile.risk_score_components
    # The ex-ante half still works, and the cash portfolio still breaches the volatility floor.
    assert not profile.compliance.compliant


def test_the_cro_checks_the_same_rules_the_proposal_did(tmp_config):
    """One `check_compliance`, so a report and the proposal it assesses cannot disagree."""
    from saa.skills.portfolio_construction import build_candidates

    stage = stage_inputs(tmp_config)
    candidates, _ = build_candidates(stage, tmp_config, method_ids=["equal_weight"])
    candidate = candidates["equal_weight"]
    profile = profile_portfolio(
        "equal_weight",
        candidate.method.name,
        PcCategory.HEURISTIC,
        candidate.weights,
        config=tmp_config,
        covariance=stage.covariance,
        benchmark=stage.benchmark,
        inflation_pct=stage.inflation_pct,
        expected_return_pct=candidate.stats.expected_return_pct,
        scenario_returns=None,
    )
    proposal_rules = {v.rule for v in candidate.compliance.violations}
    assert proposal_rules <= {v.rule for v in profile.compliance.violations}

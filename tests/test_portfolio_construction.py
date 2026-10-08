"""The portfolio-construction optimisers and the statistics derived from their weights.

Deterministic throughout: these need no lake and no API key.
"""

import numpy as np
import pandas as pd
import pytest

from saa.skills.portfolio_construction import (
    METHODS,
    PortfolioInputs,
    black_litterman,
    effective_number_of_assets,
    equal_weight,
    implied_equilibrium_returns,
    inverse_variance,
    inverse_volatility,
    max_sharpe,
    portfolio_stats,
)

IDS = ["equity", "credit", "bills"]

# Decimal-squared, as covariance.json stores it: 20%, 10% and 5% volatilities.
COV = pd.DataFrame(
    [[0.0400, 0.0040, 0.0010], [0.0040, 0.0100, 0.0005], [0.0010, 0.0005, 0.0025]],
    index=IDS,
    columns=IDS,
    dtype=float,
)
MU = pd.Series({"equity": 0.08, "credit": 0.05, "bills": 0.03})
MARKET = pd.Series({"equity": 0.60, "credit": 0.30, "bills": 0.10})


def inputs(**kw) -> PortfolioInputs:
    base = dict(
        asset_ids=IDS,
        covariance=COV,
        expected_returns=MU,
        risk_free=0.02,
        market_weights=MARKET,
    )
    return PortfolioInputs(**{**base, **kw})


ALL_METHODS = [equal_weight, inverse_volatility, inverse_variance, max_sharpe, black_litterman]


# ------------------------------------------------------------------------- shared invariants
@pytest.mark.parametrize("method", ALL_METHODS, ids=lambda f: f.__name__)
def test_every_method_is_long_only_and_fully_invested(method):
    """The ratified IPS permits no shorting and no leverage, so no optimiser may produce them."""
    weights = method(inputs())
    assert weights.sum() == pytest.approx(1.0)
    assert (weights >= 0).all()
    assert list(weights.index) == IDS


@pytest.mark.parametrize("method", ALL_METHODS, ids=lambda f: f.__name__)
def test_every_method_is_deterministic(method):
    pd.testing.assert_series_equal(method(inputs()), method(inputs()))


def test_the_registry_matches_the_implementations():
    assert set(METHODS) == {
        "equal_weight",
        "inverse_volatility",
        "inverse_variance",
        "max_sharpe",
        "black_litterman",
    }
    # §3.4 splits the families by whether they consume return forecasts.
    assert {m.id for m in METHODS.values() if m.uses_cmas} == {"max_sharpe", "black_litterman"}
    assert {m.category for m in METHODS.values()} == {"heuristic", "return_optimized"}


# -------------------------------------------------------------------------------- heuristic
def test_equal_weight_is_one_over_n():
    assert equal_weight(inputs()).tolist() == pytest.approx([1 / 3] * 3)


def test_heuristic_methods_ignore_expected_returns():
    """DeMiguel, Garlappi and Uppal (2009): the point of these methods is that they estimate
    nothing about returns, so a different CMA must not move them."""
    other = inputs(expected_returns=pd.Series({"equity": 0.30, "credit": -0.10, "bills": 0.01}))
    for method in (equal_weight, inverse_volatility, inverse_variance):
        pd.testing.assert_series_equal(method(inputs()), method(other))


def test_heuristic_methods_need_no_expected_returns_at_all():
    bare = PortfolioInputs(asset_ids=IDS, covariance=COV)
    for method in (equal_weight, inverse_volatility, inverse_variance):
        assert method(bare).sum() == pytest.approx(1.0)


def test_inverse_volatility_is_proportional_to_one_over_sigma():
    weights = inverse_volatility(inputs())
    vols = np.sqrt(np.diag(COV.to_numpy()))
    expected = (1 / vols) / (1 / vols).sum()
    assert weights.to_numpy() == pytest.approx(expected)


def test_inverse_variance_tilts_harder_than_inverse_volatility():
    """Squaring the denominator concentrates further into the lowest-volatility asset."""
    vol, var = inverse_volatility(inputs()), inverse_variance(inputs())
    assert var["bills"] > vol["bills"]
    assert var["equity"] < vol["equity"]
    assert effective_number_of_assets(var) < effective_number_of_assets(vol)


# -------------------------------------------------------------------------- return-optimized
def test_max_sharpe_beats_the_alternatives_on_sharpe():
    """It is the tangency portfolio, so by construction nothing else should score higher."""

    def sharpe(w):
        variance = float(w.to_numpy() @ COV.to_numpy() @ w.to_numpy())
        return (float(w @ MU) - 0.02) / np.sqrt(variance)

    best = sharpe(max_sharpe(inputs()))
    for method in (equal_weight, inverse_volatility, inverse_variance):
        assert best >= sharpe(method(inputs())) - 1e-6


def test_max_sharpe_responds_to_the_cmas():
    """The return-optimized family exists to use the forecasts, so it must move with them."""
    base = max_sharpe(inputs())
    bullish = max_sharpe(
        inputs(expected_returns=pd.Series({"equity": 0.25, "credit": 0.05, "bills": 0.03}))
    )
    assert bullish["equity"] > base["equity"]


def test_max_sharpe_needs_expected_returns():
    with pytest.raises(ValueError, match="needs expected returns"):
        max_sharpe(PortfolioInputs(asset_ids=IDS, covariance=COV))


def test_equilibrium_returns_are_plausible_percentages():
    """pi = delta * Sigma * w in decimals. A units slip here shows up as a 600% equity premium,
    which is how the original mistake was caught."""
    pi = implied_equilibrium_returns(inputs(), risk_aversion=2.5)
    assert (pi > 0).all()
    assert (pi < 0.25).all()
    assert pi["equity"] > pi["credit"] > pi["bills"]


def test_black_litterman_sits_between_the_market_and_the_views():
    """With no view strength it tends to the market portfolio; with strong views it tends to
    the view-driven optimum. The default must lie between the two."""
    market_like = black_litterman(inputs(), view_confidence=1e-6)
    view_like = black_litterman(inputs(), view_confidence=1e6)
    default = black_litterman(inputs())
    assert market_like["equity"] > default["equity"] > view_like["equity"] - 1e-9
    pd.testing.assert_series_equal(view_like, max_sharpe(inputs()), atol=0.02, check_exact=False)


def test_black_litterman_needs_market_weights():
    with pytest.raises(ValueError, match="needs market weights"):
        black_litterman(inputs(market_weights=None))


# ------------------------------------------------------------------------------- statistics
def test_effective_n_counts_diversification():
    """Meucci (2009), as §4.4 reports for the ensemble."""
    assert effective_number_of_assets(pd.Series([1 / 3] * 3, index=IDS)) == pytest.approx(3.0)
    assert effective_number_of_assets(pd.Series([1.0, 0.0, 0.0], index=IDS)) == pytest.approx(1.0)
    assert 1 < effective_number_of_assets(pd.Series([0.8, 0.1, 0.1], index=IDS)) < 2


def test_stats_are_reported_in_percent():
    """Inputs are decimals; everything a contract carries is percent."""
    weights = pd.Series([1 / 3] * 3, index=IDS)
    stats = portfolio_stats(weights, COV, MU, risk_free=0.02)
    assert stats.expected_return_pct == pytest.approx(100 * float(weights @ MU))
    assert 5 < stats.expected_volatility_pct < 15  # percent, not 0.08
    assert stats.sharpe_ratio == pytest.approx(
        (float(weights @ MU) - 0.02) / (stats.expected_volatility_pct / 100)
    )


def test_tracking_error_is_zero_against_itself():
    weights = pd.Series([0.6, 0.3, 0.1], index=IDS)
    stats = portfolio_stats(weights, COV, MU, risk_free=0.02, benchmark=weights)
    assert stats.tracking_error_pct == pytest.approx(0.0, abs=1e-9)


def test_tracking_error_grows_with_the_active_position():
    benchmark = pd.Series([0.6, 0.3, 0.1], index=IDS)
    near = portfolio_stats(
        pd.Series([0.55, 0.35, 0.10], index=IDS), COV, MU, risk_free=0.02, benchmark=benchmark
    )
    far = portfolio_stats(
        pd.Series([0.0, 0.0, 1.0], index=IDS), COV, MU, risk_free=0.02, benchmark=benchmark
    )
    assert far.tracking_error_pct > near.tracking_error_pct > 0


def test_concentration_is_the_herfindahl_index():
    assert portfolio_stats(
        pd.Series([1 / 3] * 3, index=IDS), COV, MU, risk_free=0.02
    ).concentration_hhi == pytest.approx(1 / 3)


def test_a_missing_asset_in_the_covariance_fails_loudly():
    with pytest.raises(ValueError, match="missing"):
        PortfolioInputs(asset_ids=[*IDS, "gold"], covariance=COV)

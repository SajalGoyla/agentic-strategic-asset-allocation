"""The portfolio-construction optimisers and the statistics derived from their weights.

Deterministic throughout: these need no lake and no API key.
"""

import numpy as np
import pandas as pd
import pytest

from saa.skills.portfolio_construction import (
    METHODS,
    RESEARCH_LIBRARY,
    PortfolioInputs,
    adversarial_diversifier,
    black_litterman,
    cvar_minimization,
    effective_number_of_assets,
    equal_weight,
    global_minimum_variance,
    hierarchical_risk_parity,
    implied_equilibrium_returns,
    inverse_variance,
    inverse_volatility,
    max_sharpe,
    maximum_diversification,
    maximum_entropy,
    portfolio_stats,
    risk_contributions,
    risk_parity,
    sharpe_ratio,
    tail_risk_parity,
)
from saa.skills.portfolio_construction.methods import downside_covariance

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


def scenarios(months=240, seed=0) -> pd.DataFrame:
    """Monthly returns drawn from COV/12, with an equity crash in a few months so the tails
    differ from what the covariance alone implies."""
    rng = np.random.default_rng(seed)
    r = rng.multivariate_normal(MU.to_numpy() / 12, COV.to_numpy() / 12, size=months)
    r[::40, 0] -= 0.15
    return pd.DataFrame(r, columns=IDS)


SCENARIOS = scenarios()


def inputs(**kw) -> PortfolioInputs:
    base = dict(
        asset_ids=IDS,
        covariance=COV,
        expected_returns=MU,
        risk_free=0.02,
        market_weights=MARKET,
        scenarios=SCENARIOS,
    )
    return PortfolioInputs(**{**base, **kw})


def adversarial_vs_equal(x: PortfolioInputs):
    return adversarial_diversifier(x, equal_weight(x))


ALL_METHODS = [
    equal_weight,
    inverse_volatility,
    inverse_variance,
    max_sharpe,
    black_litterman,
    risk_parity,
    hierarchical_risk_parity,
    cvar_minimization,
    tail_risk_parity,
    maximum_entropy,
    maximum_diversification,
    global_minimum_variance,
    adversarial_vs_equal,
]


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
        "risk_parity",
        "hierarchical_risk_parity",
        "cvar_minimization",
        "tail_risk_parity",
    }
    # §3.4 splits the families by whether they consume return forecasts.
    assert {m.id for m in METHODS.values() if m.uses_cmas} == {"max_sharpe", "black_litterman"}
    # All four of Exhibit 5's families are represented.
    assert {m.category for m in METHODS.values()} == {
        "heuristic",
        "return_optimized",
        "risk_structured",
        "non_traditional",
    }
    assert {m.id for m in METHODS.values() if m.needs_scenarios} == {
        "cvar_minimization",
        "tail_risk_parity",
    }


def test_the_research_library_is_not_already_in_the_registry():
    """§3.4: the researcher proposes "a novel method not spanned by the current registry"."""
    assert RESEARCH_LIBRARY
    assert not set(RESEARCH_LIBRARY) & set(METHODS)
    assert {m.category for m in RESEARCH_LIBRARY.values()} == {"pc_researcher"}


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


# -------------------------------------------------------------------------- risk-structured
def test_risk_parity_equalises_risk_contributions():
    w = risk_parity(inputs()).to_numpy()
    assert risk_contributions(w, COV.to_numpy()) == pytest.approx([1 / 3] * 3, abs=1e-6)


def test_risk_parity_without_correlation_is_inverse_volatility():
    """With a diagonal covariance, equal risk contribution reduces to w ∝ 1/σ."""
    diagonal = pd.DataFrame(np.diag(np.diag(COV)), index=IDS, columns=IDS)
    pd.testing.assert_series_equal(
        risk_parity(inputs(covariance=diagonal)),
        inverse_volatility(inputs(covariance=diagonal)),
        atol=1e-6,
    )


def test_hrp_without_correlation_is_inverse_variance():
    """López de Prado (2016): on a diagonal matrix the recursive bisection reproduces the
    inverse-variance allocation exactly."""
    diagonal = pd.DataFrame(np.diag(np.diag(COV)), index=IDS, columns=IDS)
    pd.testing.assert_series_equal(
        hierarchical_risk_parity(inputs(covariance=diagonal)),
        inverse_variance(inputs(covariance=diagonal)),
        atol=1e-12,
    )


def test_hrp_splits_the_budget_between_clusters_first():
    """Two tight pairs: the first bisection splits between the pairs, so a fourth asset that
    duplicates one pair halves that pair's members rather than taking from the other pair."""
    ids = ["a1", "a2", "b1", "b2"]
    block = np.array([[1.0, 0.9], [0.9, 1.0]]) * 0.04
    cov = pd.DataFrame(
        np.block([[block, np.zeros((2, 2))], [np.zeros((2, 2)), block]]), index=ids, columns=ids
    )
    w = hierarchical_risk_parity(PortfolioInputs(asset_ids=ids, covariance=cov))
    assert w[["a1", "a2"]].sum() == pytest.approx(0.5)
    assert w.to_numpy() == pytest.approx([0.25] * 4)


# -------------------------------------------------------------------------- non-traditional
def expected_shortfall(w: np.ndarray, r: np.ndarray, confidence: float = 0.95) -> float:
    losses = np.sort(-(r @ w))[::-1]
    return float(losses[: int(np.ceil((1 - confidence) * len(losses)))].mean())


def test_cvar_minimization_beats_every_other_method_on_cvar():
    r = SCENARIOS.to_numpy()
    best = expected_shortfall(cvar_minimization(inputs()).to_numpy(), r)
    for method in (equal_weight, inverse_volatility, risk_parity, global_minimum_variance):
        assert best <= expected_shortfall(method(inputs()).to_numpy(), r) + 1e-6


def test_cvar_minimization_moves_to_an_asset_that_never_loses():
    safe = SCENARIOS.copy()
    safe["bills"] = 0.001
    assert cvar_minimization(inputs(scenarios=safe))["bills"] == pytest.approx(1.0)


def test_downside_covariance_is_positive_semidefinite_and_shift_invariant():
    """Shortfalls are measured below each asset's own mean, so adding a constant return to an
    asset changes nothing; and the matrix is a Gram matrix, so never indefinite."""
    d = downside_covariance(SCENARIOS.to_numpy())
    assert np.linalg.eigvalsh(d).min() >= -1e-12
    shifted = SCENARIOS + np.array([0.01, -0.02, 0.005])
    assert downside_covariance(shifted.to_numpy()) == pytest.approx(d)


def test_tail_risk_parity_equalises_downside_contributions():
    w = tail_risk_parity(inputs()).to_numpy()
    d = downside_covariance(SCENARIOS.to_numpy())
    assert risk_contributions(w, d) == pytest.approx([1 / 3] * 3, abs=1e-6)


def test_scenario_methods_need_scenarios():
    for method in (cvar_minimization, tail_risk_parity):
        with pytest.raises(ValueError, match="scenarios"):
            method(inputs(scenarios=None))


# -------------------------------------------------------------------------- researcher library
def test_maximum_entropy_without_a_floor_is_equal_weight():
    w = maximum_entropy(inputs(), floor_fraction=0.0)
    assert w.to_numpy() == pytest.approx([1 / 3] * 3, abs=1e-4)


def test_maximum_entropy_respects_the_sharpe_floor():
    x = inputs()
    best = sharpe_ratio(max_sharpe(x).to_numpy(), x)
    w = maximum_entropy(x, floor_fraction=0.95)
    assert sharpe_ratio(w.to_numpy(), x) >= 0.95 * best - 1e-6
    assert effective_number_of_assets(w) > effective_number_of_assets(max_sharpe(x))


def test_maximum_diversification_without_correlation_is_inverse_volatility():
    diagonal = pd.DataFrame(np.diag(np.diag(COV)), index=IDS, columns=IDS)
    pd.testing.assert_series_equal(
        maximum_diversification(inputs(covariance=diagonal)),
        inverse_volatility(inputs(covariance=diagonal)),
        atol=1e-4,
    )


def test_global_minimum_variance_has_the_least_variance():
    sigma = COV.to_numpy()
    best = global_minimum_variance(inputs()).to_numpy()
    for method in ALL_METHODS:
        w = method(inputs()).to_numpy()
        assert best @ sigma @ best <= w @ sigma @ w + 1e-9


# -------------------------------------------------------------------------- adversarial
def test_adversarial_diversifier_respects_the_sharpe_floor():
    x = inputs()
    best = sharpe_ratio(max_sharpe(x).to_numpy(), x)
    w = adversarial_diversifier(x, equal_weight(x))
    assert sharpe_ratio(w.to_numpy(), x) >= 0.75 * best - 1e-6


def test_adversarial_diversifier_moves_furthest_from_the_centroid():
    x = inputs()
    others = [equal_weight(x), inverse_volatility(x), risk_parity(x), max_sharpe(x)]
    center = pd.concat(others, axis=1).mean(axis=1)
    sigma = COV.to_numpy()

    def distance(w):
        d = (w - center).to_numpy()
        return d @ sigma @ d

    adversarial = adversarial_diversifier(x, center)
    for w in others:
        assert distance(adversarial) >= distance(w) - 1e-9

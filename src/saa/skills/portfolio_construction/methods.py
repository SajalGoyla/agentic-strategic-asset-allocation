"""Portfolio-construction methods: the optimisers, with no LLM anywhere.

Ang, Azimbayev & Kim (2026) Exhibit 5 groups the methods into four families, all four of which
are implemented here, plus the PC-researcher's library and the adversarial diversifier:

* **Heuristic** — equal weight, inverse volatility, inverse variance. §3.4: these "avoid
  optimization-driven estimation error and dominate when expected returns are poorly measured"
  (DeMiguel, Garlappi and Uppal 2009). None of them reads a CMA.
* **Return-optimized** — maximum Sharpe ratio and Black–Litterman. These "explicitly use return
  forecasts from the asset class agents", so they are the methods that inherit whatever error is
  in the CMAs.
* **Risk-structured** — risk parity and hierarchical risk parity: "optimize risk metrics without
  explicit return forecasts, on the premise that the covariance matrix is more reliably
  estimated than expected returns".
* **Non-traditional** — CVaR minimisation and tail-risk parity, which "address limitations of
  variance-based frameworks". They read historical return scenarios, not just the covariance.
* **Researcher library** (``RESEARCH_LIBRARY``) — methods the PC-researcher may propose because
  the registry does not span them, and the **adversarial diversifier**, which needs every other
  proposal before it can run.

Every method returns long-only, fully invested weights, because the ratified IPS permits no
shorting and no leverage. The ratified IPS sets no per-asset or per-group caps, so a method may
concentrate; that is deliberate (docs/ips.md) and the risk limits are what binds.

**Units.** This module works in decimals, not percent: the covariance matrix arrives from
`covariance.json` in decimal-squared (a 20% volatility is a variance of 0.04), which is the form
the standard formulas assume, so Black-Litterman's pi = delta * Sigma * w needs no scaling
factor. Expected returns and the risk-free rate are decimals to match. `analysis.py` converts
once at the boundary and everything the pipeline writes is percent, per the project convention.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.optimize import linprog, minimize
from scipy.spatial.distance import squareform

log = logging.getLogger(__name__)

# Below this the weight is treated as zero, so a 1e-17 residue never reaches a contract.
WEIGHT_FLOOR = 1e-9


@dataclass(frozen=True)
class PortfolioInputs:
    """What every method may read. Heuristic methods ignore ``expected_returns``."""

    asset_ids: list[str]
    covariance: pd.DataFrame  # annualised, decimal-squared (0.04 == 20% volatility)
    expected_returns: pd.Series | None = None  # annualised decimal (0.07 == 7%)
    risk_free: float = 0.0  # annualised decimal
    market_weights: pd.Series | None = None  # for Black-Litterman equilibrium
    # Monthly decimal returns, months x assets, every asset present: the non-traditional
    # methods' scenarios.
    scenarios: pd.DataFrame | None = None

    def __post_init__(self) -> None:
        missing = [a for a in self.asset_ids if a not in self.covariance.index]
        if missing:
            raise ValueError(f"covariance matrix is missing {missing}")

    @property
    def sigma(self) -> np.ndarray:
        return self.covariance.loc[self.asset_ids, self.asset_ids].to_numpy(dtype=float)

    @property
    def volatilities(self) -> np.ndarray:
        return np.sqrt(np.diag(self.sigma))

    @property
    def scenario_matrix(self) -> np.ndarray:
        if self.scenarios is None or self.scenarios.empty:
            raise ValueError("this method needs historical return scenarios; none were supplied")
        return self.scenarios[self.asset_ids].to_numpy(dtype=float)

    @property
    def mu(self) -> np.ndarray:
        if self.expected_returns is None:
            raise ValueError("this method needs expected returns; none were supplied")
        return self.expected_returns.reindex(self.asset_ids).to_numpy(dtype=float)


def _normalise(weights: np.ndarray, asset_ids: list[str]) -> pd.Series:
    """Clip tiny residues, renormalise to 1, and return a labelled series."""
    w = np.where(np.abs(weights) < WEIGHT_FLOOR, 0.0, weights)
    w = np.clip(w, 0.0, None)
    total = w.sum()
    if total <= 0:
        raise ValueError("optimiser produced no positive weights")
    return pd.Series(w / total, index=asset_ids, dtype="float64")


# ------------------------------------------------------------------------------- heuristic
def equal_weight(inputs: PortfolioInputs) -> pd.Series:
    """1/N. DeMiguel, Garlappi and Uppal (2009): hard to beat out of sample precisely because
    it estimates nothing."""
    n = len(inputs.asset_ids)
    return _normalise(np.ones(n) / n, inputs.asset_ids)


def inverse_volatility(inputs: PortfolioInputs) -> pd.Series:
    """Weights proportional to 1/σ (Kirby and Ostdiek 2012). Uses only the diagonal, so it is
    immune to correlation estimation error."""
    vols = inputs.volatilities
    if np.any(vols <= 0):
        raise ValueError("inverse volatility needs positive volatilities")
    return _normalise(1.0 / vols, inputs.asset_ids)


def inverse_variance(inputs: PortfolioInputs) -> pd.Series:
    """Weights proportional to 1/σ². Tilts harder toward low-volatility assets than inverse
    volatility, and is the minimum-variance solution when correlations are assumed equal."""
    variances = np.diag(inputs.sigma)
    if np.any(variances <= 0):
        raise ValueError("inverse variance needs positive variances")
    return _normalise(1.0 / variances, inputs.asset_ids)


# ------------------------------------------------------------------------ return-optimized
def max_sharpe(inputs: PortfolioInputs) -> pd.Series:
    """Long-only tangency portfolio (Markowitz 1952).

    Maximising the Sharpe ratio is not convex in the weights, but minimising its negative under
    a simplex constraint is well behaved for 18 assets. SLSQP is started from equal weight and
    from inverse volatility, and the better solution wins: a single start can stop at a local
    optimum when the covariance matrix is close to singular.
    """
    sigma, mu = inputs.sigma, inputs.mu
    excess = mu - inputs.risk_free
    n = len(inputs.asset_ids)

    def negative_sharpe(w: np.ndarray) -> float:
        variance = float(w @ sigma @ w)
        if variance <= 0:
            return 0.0
        return -float(w @ excess) / np.sqrt(variance)

    constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
    bounds = [(0.0, 1.0)] * n
    starts = [np.ones(n) / n, inverse_volatility(inputs).to_numpy()]

    best, best_value = None, np.inf
    for start in starts:
        result = minimize(
            negative_sharpe,
            start,
            method="SLSQP",
            bounds=bounds,
            constraints=[constraints],
            options={"maxiter": 500, "ftol": 1e-10},
        )
        if result.success and result.fun < best_value:
            best, best_value = result.x, result.fun

    if best is None:
        raise ValueError("max Sharpe optimisation did not converge from either start")
    return _normalise(best, inputs.asset_ids)


def implied_equilibrium_returns(inputs: PortfolioInputs, *, risk_aversion: float) -> pd.Series:
    """Reverse-optimised returns π = δ Σ w_mkt (Black and Litterman 1992)."""
    if inputs.market_weights is None:
        raise ValueError("Black-Litterman needs market weights")
    weights = inputs.market_weights.reindex(inputs.asset_ids).fillna(0.0).to_numpy(dtype=float)
    total = weights.sum()
    if total <= 0:
        raise ValueError("market weights must be positive")
    pi = risk_aversion * inputs.sigma @ (weights / total)
    return pd.Series(pi + inputs.risk_free, index=inputs.asset_ids, dtype="float64")


def black_litterman(
    inputs: PortfolioInputs,
    *,
    risk_aversion: float = 2.5,
    tau: float = 0.05,
    view_confidence: float = 1.0,
) -> pd.Series:
    """Black and Litterman (1992), with the asset-class agents' CMAs as the views.

    The market portfolio is reverse-optimised into equilibrium returns, then blended with the
    judged CMAs. Each asset carries its own absolute view, so P is the identity and the
    posterior has the closed form

        μ_bl = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹ [(τΣ)⁻¹π + PᵀΩ⁻¹q]

    with Ω = diag(τΣ)/``view_confidence``: a view on a volatile asset is held less tightly than
    one on a stable asset, which is Black and Litterman's own proportional specification. The
    posterior then goes through the same long-only mean-variance step as ``max_sharpe``.

    This is why the method sits in the return-optimized family: without views it collapses to
    the market portfolio, and the whole point is that the CMAs move it away from that.
    """
    pi = implied_equilibrium_returns(inputs, risk_aversion=risk_aversion).to_numpy()
    q = inputs.mu
    sigma = inputs.sigma
    tau_sigma = tau * sigma

    omega = np.diag(np.maximum(np.diag(tau_sigma), 1e-12) / max(view_confidence, 1e-6))
    tau_sigma_inv = np.linalg.pinv(tau_sigma)
    omega_inv = np.linalg.pinv(omega)

    posterior_cov = np.linalg.pinv(tau_sigma_inv + omega_inv)
    posterior_mu = posterior_cov @ (tau_sigma_inv @ pi + omega_inv @ q)

    blended = PortfolioInputs(
        asset_ids=inputs.asset_ids,
        covariance=inputs.covariance,
        expected_returns=pd.Series(posterior_mu, index=inputs.asset_ids),
        risk_free=inputs.risk_free,
        market_weights=inputs.market_weights,
    )
    return max_sharpe(blended)


# ------------------------------------------------------------------------- shared helpers
def _simplex_minimize(objective, starts, n: int, constraints=(), gradient=None) -> np.ndarray:
    """Minimise over long-only, fully invested weights from several starts; keep the best."""
    bounds = [(0.0, 1.0)] * n
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}, *constraints]
    best, best_value = None, np.inf
    for start in starts:
        result = minimize(
            objective,
            start,
            jac=gradient,
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        feasible = all(
            (c["fun"](result.x) >= -1e-7) if c["type"] == "ineq" else abs(c["fun"](result.x)) < 1e-6
            for c in cons
        )
        if feasible and result.fun < best_value:
            best, best_value = result.x, result.fun
    if best is None:
        raise ValueError("optimisation found no feasible solution from any start")
    return best


def sharpe_ratio(weights: np.ndarray, inputs: PortfolioInputs) -> float:
    variance = float(weights @ inputs.sigma @ weights)
    if variance <= 0:
        return 0.0
    return float(weights @ (inputs.mu - inputs.risk_free)) / np.sqrt(variance)


def sharpe_floor_constraint(inputs: PortfolioInputs, fraction: float) -> list[dict]:
    """Sharpe(w) >= fraction x the maximum Sharpe ratio: the floor §3.4 puts under both the
    researcher's maximum-entropy portfolio and the adversarial diversifier. No floor when the
    best attainable Sharpe ratio is not positive, since a fraction of it would be no floor."""
    best = sharpe_ratio(max_sharpe(inputs).to_numpy(), inputs)
    if best <= 0:
        return []
    floor = fraction * best
    return [{"type": "ineq", "fun": lambda w: sharpe_ratio(w, inputs) - floor}]


def risk_contributions(weights: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Each asset's share of portfolio variance, w_i (Σw)_i / w'Σw; they sum to 1."""
    marginal = sigma @ weights
    return weights * marginal / float(weights @ marginal)


def equal_risk_contribution(sigma: np.ndarray) -> np.ndarray:
    """Long-only equal-risk-contribution weights for any positive semidefinite ``sigma``.

    Spinu (2013): minimise ½ y'Σy − (1/n) Σ log y over y > 0. The objective is strictly convex
    and its first-order condition is y_i (Σy)_i = 1/n for every i -- equal contributions -- so
    the solution exists, is unique, and normalising y gives the weights. This avoids the
    non-convex least-squares formulation, which stalls when risks differ by orders of
    magnitude, as they do between cash and equities here.
    """
    n = len(sigma)
    vols = np.sqrt(np.diag(sigma))
    start = 1.0 / vols / np.sqrt(n)

    def objective(y):
        return 0.5 * float(y @ sigma @ y) - float(np.log(y).sum()) / n

    def gradient(y):
        return sigma @ y - 1.0 / (n * y)

    result = minimize(
        objective,
        start,
        jac=gradient,
        method="L-BFGS-B",
        bounds=[(1e-12, None)] * n,
        options={"maxiter": 5000, "gtol": 1e-12, "ftol": 1e-15},
    )
    y = result.x
    return y / y.sum()


# ------------------------------------------------------------------------- risk-structured
def risk_parity(inputs: PortfolioInputs) -> pd.Series:
    """Equal risk contribution (Maillard, Roncalli and Teïletche 2010): every asset contributes
    the same share of portfolio variance. Uses the full covariance matrix but no returns."""
    return _normalise(equal_risk_contribution(inputs.sigma), inputs.asset_ids)


def _inverse_variance_weights(sigma: np.ndarray) -> np.ndarray:
    w = 1.0 / np.diag(sigma)
    return w / w.sum()


def hierarchical_order(sigma: np.ndarray) -> list[int]:
    """Quasi-diagonal order: single-linkage clustering on the correlation distance
    sqrt((1 - ρ) / 2), read off the dendrogram's leaves, so similar assets sit together."""
    vols = np.sqrt(np.diag(sigma))
    corr = np.clip(sigma / np.outer(vols, vols), -1.0, 1.0)
    distance = np.sqrt(np.clip((1.0 - corr) / 2.0, 0.0, None))
    np.fill_diagonal(distance, 0.0)
    tree = linkage(squareform(distance, checks=False), method="single")
    return [int(i) for i in leaves_list(tree)]


def hierarchical_risk_parity(inputs: PortfolioInputs) -> pd.Series:
    """López de Prado (2016). Order the assets by a correlation dendrogram, then bisect the
    ordering recursively, splitting each cluster's budget in inverse proportion to the variance
    of its two halves (each half held at inverse-variance weights). No matrix is inverted, so
    the result does not swing on a near-singular covariance matrix the way an optimiser does."""
    sigma = inputs.sigma
    order = hierarchical_order(sigma)
    weights = np.ones(len(sigma))
    clusters = [order]
    while clusters:
        nxt = []
        for cluster in clusters:
            if len(cluster) < 2:
                continue
            half = len(cluster) // 2
            left, right = cluster[:half], cluster[half:]
            variances = []
            for part in (left, right):
                sub = sigma[np.ix_(part, part)]
                w = _inverse_variance_weights(sub)
                variances.append(float(w @ sub @ w))
            alpha = 1.0 - variances[0] / (variances[0] + variances[1])
            weights[left] *= alpha
            weights[right] *= 1.0 - alpha
            nxt += [left, right]
        clusters = nxt
    return _normalise(weights, inputs.asset_ids)


# ------------------------------------------------------------------------- non-traditional
CVAR_CONFIDENCE = 0.95


def cvar_minimization(inputs: PortfolioInputs, *, confidence: float = CVAR_CONFIDENCE) -> pd.Series:
    """Minimise the historical expected shortfall of monthly returns (Rockafellar and Uryasev
    2000). Their auxiliary-variable form makes this a linear programme:

        min  α + 1/((1-β)T) Σ u_t   s.t.  u_t ≥ -r_t'w - α,  u_t ≥ 0,  Σw = 1,  w ≥ 0

    over the scenarios in ``inputs.scenarios``. At the optimum α is the VaR and the objective the
    CVaR. Uses the whole empirical distribution, so fat tails and asymmetry count, which a
    variance-based method cannot see.
    """
    r = inputs.scenario_matrix
    t, n = r.shape
    # Variables: w (n), alpha (1), u (t).
    cost = np.concatenate([np.zeros(n), [1.0], np.full(t, 1.0 / ((1.0 - confidence) * t))])
    # -r_t'w - alpha - u_t <= 0
    a_ub = np.hstack([-r, -np.ones((t, 1)), -np.eye(t)])
    b_ub = np.zeros(t)
    a_eq = np.concatenate([np.ones(n), [0.0], np.zeros(t)])[None, :]
    bounds = [(0.0, 1.0)] * n + [(None, None)] + [(0.0, None)] * t
    result = linprog(
        cost, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=[1.0], bounds=bounds, method="highs"
    )
    if not result.success:
        raise ValueError(f"CVaR programme failed: {result.message}")
    return _normalise(result.x[:n], inputs.asset_ids)


def downside_covariance(scenarios: np.ndarray) -> np.ndarray:
    """Annualised semicovariance below each asset's mean (Estrada 2008): the co-movement of
    shortfalls only. It is a Gram matrix, so always positive semidefinite."""
    shortfall = np.minimum(scenarios - scenarios.mean(axis=0), 0.0)
    return 12.0 * shortfall.T @ shortfall / len(scenarios)


def tail_risk_parity(inputs: PortfolioInputs) -> pd.Series:
    """Equal risk contribution measured on downside risk rather than variance.

    Exhibit 5 cites Spinu (2013), whose convex algorithm this reuses; the risk measure is the
    downside semicovariance, so an asset is charged for how it falls with the others and not for
    upside volatility. An expected-shortfall budget was rejected: a hedge whose tail
    contribution is negative (Treasuries in an equity sell-off) cannot be given an equal
    positive share, so a long-only solution need not exist.
    """
    return _normalise(
        equal_risk_contribution(downside_covariance(inputs.scenario_matrix)), inputs.asset_ids
    )


# ------------------------------------------------------------------------ researcher library
SHARPE_FLOOR_FRACTION = 0.75  # §3.4: "a Sharpe-ratio floor of 75% of the maximum Sharpe"


def maximum_entropy(
    inputs: PortfolioInputs, *, floor_fraction: float = SHARPE_FLOOR_FRACTION
) -> pd.Series:
    """Bera and Park (2008): the most spread-out weights -- maximum Shannon entropy -- that still
    reach the Sharpe floor. The PC-researcher's proposal in the paper's March 2026 run. Without
    the floor it is equal weight; the floor is what makes it use the CMAs."""
    n = len(inputs.asset_ids)

    def negative_entropy(w):
        w = np.clip(w, 1e-12, None)
        return float((w * np.log(w)).sum())

    starts = [max_sharpe(inputs).to_numpy(), np.ones(n) / n]
    best = _simplex_minimize(
        negative_entropy, starts, n, sharpe_floor_constraint(inputs, floor_fraction)
    )
    return _normalise(best, inputs.asset_ids)


def maximum_diversification(inputs: PortfolioInputs) -> pd.Series:
    """Choueifaty and Coignard (2008): maximise the diversification ratio w'σ / √(w'Σw), the
    weighted average volatility over the portfolio volatility. Ranked first by the paper's peer
    vote (§4.3)."""
    sigma, vols = inputs.sigma, inputs.volatilities
    n = len(vols)

    def negative_ratio(w):
        variance = float(w @ sigma @ w)
        return -float(w @ vols) / np.sqrt(variance) if variance > 0 else 0.0

    starts = [np.ones(n) / n, inverse_volatility(inputs).to_numpy()]
    return _normalise(_simplex_minimize(negative_ratio, starts, n), inputs.asset_ids)


def global_minimum_variance(inputs: PortfolioInputs) -> pd.Series:
    """Clarke, de Silva and Thorley (2006): the long-only portfolio of least variance."""
    sigma = inputs.sigma
    n = len(sigma)
    best = _simplex_minimize(
        lambda w: float(w @ sigma @ w),
        [np.ones(n) / n, inverse_variance(inputs).to_numpy()],
        n,
        gradient=lambda w: 2.0 * sigma @ w,
    )
    return _normalise(best, inputs.asset_ids)


# ------------------------------------------------------------------- adversarial diversifier
def adversarial_diversifier(
    inputs: PortfolioInputs,
    centroid: pd.Series,
    *,
    floor_fraction: float = SHARPE_FLOOR_FRACTION,
) -> pd.Series:
    """§3.4: "maximizes tracking variance relative to the ensemble centroid (the mean of all
    other PC weights), subject to a Sharpe-ratio floor of 75% of the maximum Sharpe portfolio".

    Maximising a convex function over the simplex has its optimum at or near a vertex, and
    SLSQP finds only local optima, so it starts from every single-asset portfolio as well as
    from maximum Sharpe and keeps the feasible start that moves furthest from the centroid.
    """
    sigma = inputs.sigma
    c = centroid.reindex(inputs.asset_ids).fillna(0.0).to_numpy(dtype=float)
    n = len(c)

    def negative_tracking_variance(w):
        d = w - c
        return -float(d @ sigma @ d)

    def gradient(w):
        return -2.0 * sigma @ (w - c)

    starts = [max_sharpe(inputs).to_numpy(), *np.eye(n)]
    best = _simplex_minimize(
        negative_tracking_variance,
        starts,
        n,
        sharpe_floor_constraint(inputs, floor_fraction),
        gradient=gradient,
    )
    return _normalise(best, inputs.asset_ids)


# --------------------------------------------------------------------------------- registry
@dataclass(frozen=True)
class Method:
    """One portfolio-construction method, as the PC agents see it."""

    id: str
    name: str
    category: str
    reference: str
    uses_cmas: bool
    build: object  # Callable[[PortfolioInputs], pd.Series]
    needs_scenarios: bool = False
    # Method-specific framing for the agent's prompt, where the generic one would mislead.
    prompt_note: str | None = None


METHODS: dict[str, Method] = {
    m.id: m
    for m in [
        Method(
            id="equal_weight",
            name="Equal weight (1/N)",
            category="heuristic",
            reference="DeMiguel, Garlappi and Uppal (2009)",
            uses_cmas=False,
            build=equal_weight,
        ),
        Method(
            id="inverse_volatility",
            name="Inverse volatility",
            category="heuristic",
            reference="Kirby and Ostdiek (2012)",
            uses_cmas=False,
            build=inverse_volatility,
        ),
        Method(
            id="inverse_variance",
            name="Inverse variance",
            category="heuristic",
            reference="Kirby and Ostdiek (2012)",
            uses_cmas=False,
            build=inverse_variance,
        ),
        Method(
            id="max_sharpe",
            name="Maximum Sharpe ratio",
            category="return_optimized",
            reference="Markowitz (1952)",
            uses_cmas=True,
            build=max_sharpe,
        ),
        Method(
            id="black_litterman",
            name="Black-Litterman",
            category="return_optimized",
            reference="Black and Litterman (1992)",
            uses_cmas=True,
            build=black_litterman,
        ),
        Method(
            id="risk_parity",
            name="Risk parity (equal risk contribution)",
            category="risk_structured",
            reference="Maillard, Roncalli and Teiletche (2010)",
            uses_cmas=False,
            build=risk_parity,
        ),
        Method(
            id="hierarchical_risk_parity",
            name="Hierarchical risk parity",
            category="risk_structured",
            reference="Lopez de Prado (2016)",
            uses_cmas=False,
            build=hierarchical_risk_parity,
        ),
        Method(
            id="cvar_minimization",
            name="CVaR minimisation",
            category="non_traditional",
            reference="Rockafellar and Uryasev (2000)",
            uses_cmas=False,
            build=cvar_minimization,
            needs_scenarios=True,
        ),
        Method(
            id="tail_risk_parity",
            name="Tail-risk parity",
            category="non_traditional",
            reference="Spinu (2013)",
            uses_cmas=False,
            build=tail_risk_parity,
            needs_scenarios=True,
        ),
    ]
}

# Methods the PC-researcher may propose (§3.4: "a novel method not spanned by the current
# registry"). They are implemented in advance so a proposal can be run, not just described;
# the researcher's judgment is which one the registry is missing and why.
RESEARCH_LIBRARY: dict[str, Method] = {
    m.id: m
    for m in [
        Method(
            id="maximum_entropy",
            name="Maximum entropy with a Sharpe floor",
            category="pc_researcher",
            reference="Bera and Park (2008)",
            uses_cmas=True,
            build=maximum_entropy,
        ),
        Method(
            id="maximum_diversification",
            name="Maximum diversification",
            category="pc_researcher",
            reference="Choueifaty and Coignard (2008)",
            uses_cmas=False,
            build=maximum_diversification,
        ),
        Method(
            id="global_minimum_variance",
            name="Global minimum variance",
            category="pc_researcher",
            reference="Clarke, de Silva and Thorley (2006)",
            uses_cmas=False,
            build=global_minimum_variance,
        ),
    ]
}

ADVERSARIAL = Method(
    id="adversarial_diversifier",
    name="Adversarial diversifier",
    category="non_traditional",
    reference="Ang, Azimbayev and Kim (2026), section 3.4",
    uses_cmas=True,
    build=adversarial_diversifier,  # also needs the centroid of the other proposals
    prompt_note=(
        "This portfolio is deliberately as far as the Sharpe floor allows from the average of "
        "every other proposal. The paper is explicit that it 'is not intended as a standalone "
        "recommendation; it surfaces allocation ideas that are overlooked by conventional "
        "methods'. Argue for what it surfaces and what it would add to the CIO's ensemble, not "
        "for holding it on its own."
    ),
)

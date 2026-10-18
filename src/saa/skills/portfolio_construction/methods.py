"""Portfolio-construction methods: the optimisers, with no LLM anywhere.

Ang, Azimbayev & Kim (2026) Exhibit 5 groups the methods into four families, all four of which
are implemented here, plus the PC-researcher's library and the adversarial diversifier:

* **Heuristic** — equal weight, inverse volatility, inverse variance, market-cap weight and
  volatility targeting. §3.4: these "avoid optimization-driven estimation error and dominate
  when expected returns are poorly measured" (DeMiguel, Garlappi and Uppal 2009). None of them
  reads a CMA.
* **Return-optimized** — maximum Sharpe ratio, Black–Litterman and the resampled efficient
  frontier. These "explicitly use return forecasts from the asset class agents", so they are
  the methods that inherit whatever error is in the CMAs.
* **Risk-structured** — risk parity, hierarchical risk parity and maximum diversification:
  "optimize risk metrics without explicit return forecasts, on the premise that the covariance
  matrix is more reliably estimated than expected returns".
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
    cash_id: str | None = None  # the asset volatility targeting de-risks into
    target_volatility: float = 0.10  # annualised decimal; the IPS band's midpoint

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


def market_cap_weight(inputs: PortfolioInputs) -> pd.Series:
    """Sharpe (1964): hold the market. Here the market is the 18 ETFs' market values, the same
    proxy Black-Litterman reverse-optimises -- ETF sizes, not asset-class sizes. The paper's CIO
    gave it the largest ensemble weight (11.1%, Exhibit 10)."""
    if inputs.market_weights is None:
        raise ValueError("market-cap weight needs market weights; none were supplied")
    weights = inputs.market_weights.reindex(inputs.asset_ids).fillna(0.0).to_numpy(dtype=float)
    return _normalise(weights, inputs.asset_ids)


VOL_TARGET_LOOKBACK_MONTHS = 12


def volatility_targeting(inputs: PortfolioInputs) -> pd.Series:
    """Moreira and Muir (2017): scale risk exposure inversely to recent volatility.

    The risky sleeve is equal weight across every asset except cash. Its volatility over the
    last ``VOL_TARGET_LOOKBACK_MONTHS`` of scenarios (the long-run covariance when there are no
    scenarios) sets the exposure: c = min(1, target / recent volatility), with 1 - c in cash.
    The IPS allows no leverage, so a calm market caps exposure at 100% rather than scaling up.
    The target is the IPS band's midpoint, so this is the one method aimed at the band.
    """
    if inputs.cash_id is None or inputs.cash_id not in inputs.asset_ids:
        raise ValueError("volatility targeting needs the cash asset to de-risk into")
    risky = [a for a in inputs.asset_ids if a != inputs.cash_id]
    sleeve = pd.Series(1.0 / len(risky), index=risky)
    if inputs.scenarios is not None and len(inputs.scenarios) >= VOL_TARGET_LOOKBACK_MONTHS:
        recent = inputs.scenarios[risky].iloc[-VOL_TARGET_LOOKBACK_MONTHS:] @ sleeve
        volatility = float(recent.std(ddof=1) * np.sqrt(12))
    else:
        sub = inputs.covariance.loc[risky, risky].to_numpy(dtype=float)
        volatility = float(np.sqrt(sleeve.to_numpy() @ sub @ sleeve.to_numpy()))
    exposure = min(1.0, inputs.target_volatility / volatility) if volatility > 0 else 1.0
    weights = (sleeve * exposure).reindex(inputs.asset_ids).fillna(0.0)
    weights[inputs.cash_id] = 1.0 - exposure
    return _normalise(weights.to_numpy(), inputs.asset_ids)


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


RESAMPLE_DRAWS = 200
RESAMPLE_MONTHS = 120
RESAMPLE_SEED = 20260930


def resampled_efficient_frontier(
    inputs: PortfolioInputs,
    *,
    draws: int = RESAMPLE_DRAWS,
    months: int = RESAMPLE_MONTHS,
    seed: int = RESAMPLE_SEED,
) -> pd.Series:
    """Michaud (1998): average the optimal portfolio over many plausible versions of the inputs.

    Draw ``months`` of monthly returns from N(μ/12, Σ/12), re-estimate μ and Σ from the draw,
    solve the long-only maximum-Sharpe problem on the re-estimate, and average the weights over
    ``draws`` draws. A tangency portfolio that depends on a small difference between two noisy
    expected returns flips between draws and averages out, so the result keeps what is robust in
    the CMAs and drops what is noise -- the remedy for maximum Sharpe's concentration. Ten years
    of data is the information the draw pretends the CMAs carry [proposed]; the seed is fixed so
    the method is deterministic.
    """
    mu, sigma = inputs.mu, inputs.sigma
    rng = np.random.default_rng(seed)
    total = np.zeros(len(mu))
    for _ in range(draws):
        sample = rng.multivariate_normal(mu / 12, sigma / 12, size=months, method="cholesky")
        draw = PortfolioInputs(
            asset_ids=inputs.asset_ids,
            covariance=pd.DataFrame(
                np.cov(sample, rowvar=False) * 12, index=inputs.asset_ids, columns=inputs.asset_ids
            ),
            expected_returns=pd.Series(sample.mean(axis=0) * 12, index=inputs.asset_ids),
            risk_free=inputs.risk_free,
        )
        try:
            total += max_sharpe(draw).to_numpy()
        except ValueError:
            continue  # a draw with no positive excess return has no tangency portfolio
    if total.sum() <= 0:
        raise ValueError("no resampled draw produced a tangency portfolio")
    return _normalise(total, inputs.asset_ids)


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


def downside_deviation(weights: np.ndarray, scenarios: np.ndarray, target: float) -> float:
    """Annualised root-mean-square shortfall of the portfolio below ``target`` per month."""
    shortfall = np.minimum(scenarios @ weights - target, 0.0)
    return float(np.sqrt(float((shortfall**2).mean()) * 12.0))


def mean_downside_risk(inputs: PortfolioInputs) -> pd.Series:
    """Maximise the Sortino ratio: excess expected return over downside deviation.

    Exhibit 5's "mean-downside risk" method, left out of the registry (decision 33) and kept
    here for the PC-researcher. It is the one objective in the library that asks for *return*
    per unit of downside risk: maximum entropy spreads weight and global minimum variance
    ignores returns, so both collapse toward the minimum-variance corner once the IPS
    volatility floor binds, while this one does not. The registry's CVaR minimisation and
    tail-risk parity also measure downside risk but neither trades it off against return.

    The shortfall target is the risk-free rate, so the denominator is the deviation below what
    cash would have returned -- the same reference the numerator uses.
    """
    scenarios = inputs.scenario_matrix
    monthly_target = inputs.risk_free / 12.0
    excess = inputs.mu - inputs.risk_free
    n = len(inputs.asset_ids)

    def negative_sortino(w: np.ndarray) -> float:
        risk = downside_deviation(w, scenarios, monthly_target)
        return -float(w @ excess) / risk if risk > 1e-12 else 0.0

    starts = [np.ones(n) / n, inverse_volatility(inputs).to_numpy()]
    return _normalise(_simplex_minimize(negative_sortino, starts, n), inputs.asset_ids)


def _objective_mean_downside_risk(w: np.ndarray, inputs: PortfolioInputs) -> float:
    risk = downside_deviation(w, inputs.scenario_matrix, inputs.risk_free / 12.0)
    excess = float(w @ (inputs.mu - inputs.risk_free))
    return -excess / risk if risk > 1e-12 else 0.0


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
# ------------------------------------------------------------------- the IPS band as policy
# Methods are compared with the band at this tolerance, so a 1e-12 residue is not a breach.
BAND_TOL = 1e-6


def _objective_max_sharpe(w: np.ndarray, inputs: PortfolioInputs) -> float:
    return -sharpe_ratio(w, inputs)


def _objective_min_cvar(w: np.ndarray, inputs: PortfolioInputs, confidence: float = 0.95) -> float:
    """Empirical expected shortfall of the scenarios: piecewise linear in the weights."""
    losses = np.sort(inputs.scenario_matrix @ w)
    tail = max(1, int(round((1.0 - confidence) * len(losses))))
    return -float(losses[:tail].mean())


def _risk_dispersion(w: np.ndarray, covariance: np.ndarray) -> float:
    """Squared distance of the risk contributions from equal. Zero at risk parity."""
    w = np.clip(w, 1e-12, None)
    marginal = covariance @ w
    contributions = w * marginal / float(w @ marginal)
    return float(((contributions - 1.0 / len(w)) ** 2).sum())


def _objective_risk_parity(w: np.ndarray, inputs: PortfolioInputs) -> float:
    return _risk_dispersion(w, inputs.sigma)


def _objective_tail_risk_parity(w: np.ndarray, inputs: PortfolioInputs) -> float:
    return _risk_dispersion(w, downside_covariance(inputs.scenario_matrix))


def _objective_max_diversification(w: np.ndarray, inputs: PortfolioInputs) -> float:
    variance = float(w @ inputs.sigma @ w)
    return -float(w @ inputs.volatilities) / np.sqrt(variance) if variance > 0 else 0.0


def _objective_max_entropy(w: np.ndarray, inputs: PortfolioInputs) -> float:
    w = np.clip(w, 1e-12, None)
    return float((w * np.log(w)).sum())


@dataclass(frozen=True)
class ExAnteLimits:
    """The IPS limits that can be imposed on a method without look-ahead: both come from the
    covariance matrix the method already consumed. Decimals."""

    floor: float
    cap: float
    benchmark: pd.Series | None = None
    tracking_error_cap: float | None = None

    def contains_volatility(self, volatility: float) -> bool:
        return self.floor - BAND_TOL <= volatility <= self.cap + BAND_TOL


def max_sharpe_within(inputs: PortfolioInputs, limits: ExAnteLimits) -> float:
    """The highest Sharpe ratio reachable without breaching the IPS's ex-ante limits."""
    sigma = inputs.sigma
    n = len(inputs.asset_ids)
    cons = [
        {"type": "eq", "fun": lambda w: w.sum() - 1.0},
        {"type": "ineq", "fun": lambda w: float(w @ sigma @ w) - limits.floor**2},
        {"type": "ineq", "fun": lambda w: limits.cap**2 - float(w @ sigma @ w)},
    ]
    if limits.benchmark is not None and limits.tracking_error_cap is not None:
        b = limits.benchmark.reindex(inputs.asset_ids).fillna(0.0).to_numpy(dtype=float)
        cons.append(
            {
                "type": "ineq",
                "fun": lambda w: (
                    limits.tracking_error_cap
                    - float(np.sqrt(max(float((w - b) @ sigma @ (w - b)), 0.0)))
                ),
            }
        )
    best = -np.inf
    for start in volatility_band_starts(inputs, np.ones(n) / n, limits.benchmark):
        result = minimize(
            lambda w: -sharpe_ratio(w, inputs),
            start,
            method="SLSQP",
            bounds=[(0.0, 1.0)] * n,
            constraints=cons,
            options={"maxiter": 1000, "ftol": 1e-10},
        )
        w = np.clip(result.x, 0.0, None)
        if w.sum() <= 0:
            continue
        w = w / w.sum()
        if limits.contains_volatility(float(np.sqrt(max(float(w @ sigma @ w), 0.0)))):
            best = max(best, sharpe_ratio(w, inputs))
    return best


def _sharpe_floor(inputs: PortfolioInputs, limits: ExAnteLimits | None = None) -> list[dict]:
    """§3.4's floor, measured against the best Sharpe ratio the *policy* allows.

    The paper puts the floor at "75% of the maximum Sharpe portfolio" in a setting where the
    IPS does not bind on candidates. Once it does, the unconstrained maximum is the wrong
    reference: here the unconstrained tangency portfolio is 90% short Treasuries at a Sharpe of
    0.66, 75% of which is 0.50 -- above the 0.505 best attainable anywhere inside the 8-12%
    volatility band. The floor would then admit exactly one portfolio, and the adversarial
    diversifier and the maximum-entropy researcher both collapsed onto it (decision 37). Taking
    75% of the best Sharpe the IPS permits keeps the floor doing its job: stopping an
    indefensible proposal, not dictating a single one.
    """
    reference = max_sharpe_within(inputs, limits) if limits else None
    if reference is None or not np.isfinite(reference) or reference <= 0:
        return sharpe_floor_constraint(inputs, SHARPE_FLOOR_FRACTION)
    floor = SHARPE_FLOOR_FRACTION * reference
    return [{"type": "ineq", "fun": lambda w: sharpe_ratio(w, inputs) - floor}]


def volatility_band_starts(
    inputs: PortfolioInputs, target: np.ndarray, benchmark: pd.Series | None = None
) -> list[np.ndarray]:
    """Starting points spanning the volatility range, derived only from ``inputs``.

    The band is usually imposed on a portfolio that sits well below the floor, so a search
    started only from that portfolio stays there. Weights proportional to volatility, and the
    single most volatile asset, give the solver somewhere high to come down from.
    """
    n = len(inputs.asset_ids)
    vols = inputs.volatilities
    highest = np.zeros(n)
    highest[int(np.argmax(vols))] = 1.0
    candidates = [
        np.ones(n) / n,
        vols / vols.sum(),
        vols**2 / (vols**2).sum(),
        highest,
        0.5 * target + 0.5 * vols / vols.sum(),
        target,
    ]
    # The benchmark is inside the tracking-error budget by construction, so it is the one start
    # guaranteed feasible when that budget is what the method is breaching.
    if benchmark is not None:
        b = benchmark.reindex(inputs.asset_ids).fillna(0.0).to_numpy(dtype=float)
        if b.sum() > 0:
            b = b / b.sum()
            candidates += [b, 0.5 * target + 0.5 * b]
    return [np.clip(c, 0.0, 1.0) for c in candidates]


def enforce_ex_ante_limits(
    weights: pd.Series,
    inputs: PortfolioInputs,
    limits: ExAnteLimits,
    *,
    objective=None,
    constraints=(),
) -> tuple[pd.Series, float | None]:
    """Re-solve a method inside the IPS's *ex-ante* limits, or return it untouched if already in.

    §3.1 makes the IPS the governing document that every agent reads, so a method that cannot
    reach the policy on its own is solved again *subject to* it rather than left outside it
    (decision 37). The method keeps its own objective: maximum Sharpe is still the best
    risk-adjusted portfolio, risk parity is still the flattest risk contributions -- each now
    over the portfolios the policy permits. A closed-form rule and an algorithm like HRP have no
    objective to re-run, so ``objective=None`` projects to the nearest permitted portfolio by
    squared weight distance instead.

    **Only the ex-ante limits are imposed**: the volatility band and the tracking-error budget,
    both computed from the covariance matrix the method already consumed. The drawdown limit is
    deliberately left out, because constraining a *realised* drawdown chooses weights to suit
    the 1993-2026 path and is the look-ahead bias §5.1 warns about; the CRO measures it and it
    binds on the CIO's recommendation (decisions 32 and 37). The return objective is likewise
    reported rather than imposed.

    ``floor``, ``cap`` and ``tracking_error_cap`` are decimals. Returns the weights and, when
    they were adjusted, the volatility the method produced on its own -- which the agent has to
    disclose.
    """
    ids = inputs.asset_ids
    sigma = inputs.sigma
    floor, cap = limits.floor, limits.cap
    benchmark, tracking_error_cap = limits.benchmark, limits.tracking_error_cap
    target = weights.reindex(ids).fillna(0.0).to_numpy(dtype=float)
    original = float(np.sqrt(max(float(target @ sigma @ target), 0.0)))

    active = None
    if benchmark is not None and tracking_error_cap is not None:
        active = benchmark.reindex(ids).fillna(0.0).to_numpy(dtype=float)

    def tracking_error(w: np.ndarray) -> float:
        d = w - active
        return float(np.sqrt(max(float(d @ sigma @ d), 0.0)))

    inside_band = floor - BAND_TOL <= original <= cap + BAND_TOL
    inside_te = active is None or tracking_error(target) <= tracking_error_cap + BAND_TOL
    if inside_band and inside_te:
        return weights, None

    goal = objective or (lambda w, _inputs: float(((w - target) ** 2).sum()))
    cons = [
        {"type": "eq", "fun": lambda w: w.sum() - 1.0},
        {"type": "ineq", "fun": lambda w: float(w @ sigma @ w) - floor**2},
        {"type": "ineq", "fun": lambda w: cap**2 - float(w @ sigma @ w)},
        *constraints,
    ]
    if active is not None:
        cons.append({"type": "ineq", "fun": lambda w: tracking_error_cap - tracking_error(w)})
    best, best_value = None, np.inf
    for start in volatility_band_starts(inputs, target, benchmark):
        result = minimize(
            lambda w: goal(w, inputs),
            start,
            method="SLSQP",
            bounds=[(0.0, 1.0)] * len(ids),
            constraints=cons,
            options={"maxiter": 2000, "ftol": 1e-12},
        )
        w = np.clip(result.x, 0.0, None)
        if w.sum() <= 0:
            continue
        w = w / w.sum()
        volatility = float(np.sqrt(max(float(w @ sigma @ w), 0.0)))
        if not floor - BAND_TOL <= volatility <= cap + BAND_TOL:
            continue
        if active is not None and tracking_error(w) > tracking_error_cap + BAND_TOL:
            continue
        if any(
            (c["fun"](w) < -1e-6) if c["type"] == "ineq" else abs(c["fun"](w)) > 1e-6 for c in cons
        ):
            continue
        value = goal(w, inputs)
        if value < best_value:
            best, best_value = w, value
    if best is None:
        limits = f"the {floor:.1%}-{cap:.1%} volatility band"
        if active is not None:
            limits += f" and the {tracking_error_cap:.1%} tracking-error budget"
        raise ValueError(f"no portfolio inside {limits} satisfies this method's own constraints")
    return _normalise(best, ids), 100 * original


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
    # The method's own objective, re-minimised when the IPS volatility band has to be imposed
    # (decision 37). None projects to the nearest in-band portfolio instead, which is all a
    # closed-form rule or an algorithm like HRP admits.
    objective: object | None = None  # Callable[[np.ndarray, PortfolioInputs], float]
    # Constraints the method carries in its own right and which must survive the re-solve.
    # Called as `band_constraints(inputs, limits)`.
    band_constraints: object | None = None


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
            id="market_cap_weight",
            name="Market-cap weight",
            category="heuristic",
            reference="Sharpe (1964)",
            uses_cmas=False,
            build=market_cap_weight,
        ),
        Method(
            id="volatility_targeting",
            name="Volatility targeting",
            category="heuristic",
            reference="Moreira and Muir (2017)",
            uses_cmas=False,
            build=volatility_targeting,
        ),
        Method(
            id="max_sharpe",
            name="Maximum Sharpe ratio",
            category="return_optimized",
            reference="Markowitz (1952)",
            uses_cmas=True,
            build=max_sharpe,
            objective=_objective_max_sharpe,
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
            id="resampled_efficient_frontier",
            name="Resampled efficient frontier",
            category="return_optimized",
            reference="Michaud (1998)",
            uses_cmas=True,
            build=resampled_efficient_frontier,
        ),
        Method(
            id="risk_parity",
            name="Risk parity (equal risk contribution)",
            category="risk_structured",
            reference="Maillard, Roncalli and Teiletche (2010)",
            uses_cmas=False,
            build=risk_parity,
            objective=_objective_risk_parity,
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
            id="maximum_diversification",
            name="Maximum diversification",
            category="risk_structured",
            reference="Choueifaty and Coignard (2008)",
            uses_cmas=False,
            build=maximum_diversification,
            objective=_objective_max_diversification,
        ),
        Method(
            id="cvar_minimization",
            name="CVaR minimisation",
            category="non_traditional",
            reference="Rockafellar and Uryasev (2000)",
            uses_cmas=False,
            build=cvar_minimization,
            needs_scenarios=True,
            objective=_objective_min_cvar,
        ),
        Method(
            id="tail_risk_parity",
            name="Tail-risk parity",
            category="non_traditional",
            reference="Spinu (2013)",
            uses_cmas=False,
            build=tail_risk_parity,
            needs_scenarios=True,
            objective=_objective_tail_risk_parity,
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
            objective=_objective_max_entropy,
            band_constraints=_sharpe_floor,
        ),
        Method(
            id="global_minimum_variance",
            name="Global minimum variance",
            category="pc_researcher",
            reference="Clarke, de Silva and Thorley (2006)",
            uses_cmas=False,
            build=global_minimum_variance,
            objective=lambda w, inputs: float(w @ inputs.sigma @ w),
        ),
        Method(
            id="mean_downside_risk",
            name="Mean-downside risk (maximum Sortino)",
            category="pc_researcher",
            reference="Sortino and Price (1994); Exhibit 5",
            uses_cmas=True,
            build=mean_downside_risk,
            needs_scenarios=True,
            objective=_objective_mean_downside_risk,
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
    band_constraints=_sharpe_floor,
    prompt_note=(
        "This portfolio is deliberately as far as the Sharpe floor allows from the average of "
        "every other proposal. The paper is explicit that it 'is not intended as a standalone "
        "recommendation; it surfaces allocation ideas that are overlooked by conventional "
        "methods'. Argue for what it surfaces and what it would add to the CIO's ensemble, not "
        "for holding it on its own."
    ),
)

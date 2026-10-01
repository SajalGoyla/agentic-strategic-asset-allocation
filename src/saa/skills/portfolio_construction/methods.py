"""Portfolio-construction methods: the optimisers, with no LLM anywhere.

Ang, Azimbayev & Kim (2026) Exhibit 5 groups the methods into four families. This module holds
the two families on Shambhawi's side of the Phase 2 split:

* **Heuristic** — equal weight, inverse volatility, inverse variance. §3.4: these "avoid
  optimization-driven estimation error and dominate when expected returns are poorly measured"
  (DeMiguel, Garlappi and Uppal 2009). None of them reads a CMA.
* **Return-optimized** — maximum Sharpe ratio and Black–Litterman. These "explicitly use return
  forecasts from the asset class agents", so they are the methods that inherit whatever error is
  in the CMAs.

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
from scipy.optimize import minimize

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
    ]
}

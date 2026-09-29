"""Covariance estimators on monthly returns (decimals in, decimal-squared out).

Pure numpy: no data access, no I/O. Each function takes a complete T x N frame (no missing
values) and returns a *monthly* covariance; annualise with ``annualise``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MONTHS_PER_YEAR = 12


def annualise(monthly: np.ndarray) -> np.ndarray:
    return monthly * MONTHS_PER_YEAR


def sample_covariance(returns: pd.DataFrame) -> np.ndarray:
    """Unbiased sample covariance (divisor T - 1)."""
    return returns.cov(ddof=1).to_numpy()


def ledoit_wolf(returns: pd.DataFrame) -> tuple[np.ndarray, float]:
    """Shrink the sample covariance toward a constant-correlation target.

    Ledoit & Wolf (2004), "Honey, I Shrunk the Sample Covariance Matrix". The target keeps every
    asset's own variance and replaces each correlation with the average one, so shrinkage pulls
    correlations together without distorting volatilities -- the right target for asset classes
    whose volatilities range from 0.5% (cash) to 20% (equities). The intensity is the analytic
    optimum, not a tuned parameter. Returns (covariance, shrinkage in [0, 1]); both use the
    maximum-likelihood divisor T, as in the paper.
    """
    x = returns.to_numpy(dtype=float)
    t, n = x.shape
    x = x - x.mean(axis=0)
    s = x.T @ x / t
    var = np.diag(s)
    std = np.sqrt(var)
    corr = s / np.outer(std, std)
    r_bar = (corr.sum() - n) / (n * (n - 1))

    target = r_bar * np.outer(std, std)
    np.fill_diagonal(target, var)

    # pi: sum of asymptotic variances of the sample covariance entries
    pi_mat = (x**2).T @ (x**2) / t - s**2
    pi_hat = pi_mat.sum()
    # rho: asymptotic covariance between target and sample entries
    theta = (x**3).T @ x / t - var[:, None] * s  # theta[i, j] = theta_{ii,ij}
    ratio = std[None, :] / std[:, None]  # ratio[i, j] = sqrt(s_jj / s_ii)
    off = ratio * theta + ratio.T * theta.T
    np.fill_diagonal(off, 0.0)
    rho_hat = np.trace(pi_mat) + r_bar / 2 * off.sum()
    # gamma: misspecification of the target
    gamma_hat = ((target - s) ** 2).sum()

    if gamma_hat <= 0:
        return s, 0.0
    shrinkage = float(np.clip((pi_hat - rho_hat) / gamma_hat / t, 0.0, 1.0))
    return shrinkage * target + (1 - shrinkage) * s, shrinkage


def exponential_covariance(returns: pd.DataFrame, halflife_months: float) -> np.ndarray:
    """Exponentially weighted covariance: a month ``halflife_months`` old counts half as much
    as the latest one. Reacts to volatility regimes faster than an equal-weighted window."""
    if halflife_months <= 0:
        raise ValueError("halflife_months must be positive")
    x = returns.to_numpy(dtype=float)
    t = len(x)
    decay = 0.5 ** (1.0 / halflife_months)
    weights = decay ** np.arange(t - 1, -1, -1)
    weights /= weights.sum()
    centred = x - weights @ x
    cov = (centred * weights[:, None]).T @ centred
    # Reliability-weights correction, the weighted analogue of the T - 1 divisor.
    return cov / (1.0 - (weights**2).sum())


def correlation_from(cov: np.ndarray) -> np.ndarray:
    std = np.sqrt(np.diag(cov))
    return cov / np.outer(std, std)


def average_correlation(cov: np.ndarray) -> float:
    corr = correlation_from(cov)
    n = len(corr)
    return float((corr.sum() - n) / (n * (n - 1)))


def condition_number(cov: np.ndarray) -> float:
    """Ratio of largest to smallest eigenvalue; large values make optimisers unstable."""
    eigenvalues = np.linalg.eigvalsh(cov)
    return float(eigenvalues[-1] / eigenvalues[0]) if eigenvalues[0] > 0 else float("inf")


def is_positive_definite(cov: np.ndarray, rtol: float = 1e-10) -> bool:
    """Numerically positive definite: the smallest eigenvalue is a meaningful fraction of the
    largest. A rank-deficient matrix often shows a smallest eigenvalue of 1e-20 rather than 0,
    which a plain ``> 0`` test would accept and an optimiser would then fail to invert."""
    eigenvalues = np.linalg.eigvalsh(cov)
    return bool(eigenvalues[0] > rtol * eigenvalues[-1])

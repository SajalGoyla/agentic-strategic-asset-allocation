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


def recent_volatility_covariance(
    returns: pd.DataFrame, halflife_months: float
) -> tuple[np.ndarray, float]:
    """Long-run correlations with recent volatilities (decision 65).

    The RiskMetrics practice: volatility clusters and so is forecastable from the recent past,
    while correlations need a long sample to estimate. Correlations come from Ledoit-Wolf over
    the whole frame; each asset's volatility from an exponentially weighted variance with the
    given half-life. Returns (covariance, the Ledoit-Wolf shrinkage behind the correlations).
    """
    long_run, shrinkage = ledoit_wolf(returns)
    recent = np.sqrt(np.diag(exponential_covariance(returns, halflife_months)))
    corr = correlation_from(long_run)
    return corr * np.outer(recent, recent), shrinkage


def regime_blend_covariance(
    returns: pd.DataFrame,
    labels: pd.Series,
    weights: dict[str, float],
    min_months: int,
) -> tuple[np.ndarray, dict[str, float]]:
    """A probability-weighted mixture of the regimes' covariances (decision 65).

    Each regime's covariance is Ledoit-Wolf on the months labelled with it; regimes with fewer
    than ``min_months`` are dropped and the weights renormalised. By the law of total covariance
    the mixture is the weighted average of the regime covariances plus the spread of the regime
    means around their weighted average, so a recession weight also brings in how far a
    recession's returns sit from the others'. ``labels`` is aligned to ``returns``' rows.
    Returns (covariance, the weights actually used).
    """
    x = returns.to_numpy(dtype=float)
    lab = np.asarray(labels, dtype=object)
    covs, means, used = [], [], {}
    for regime, w in weights.items():
        mask = lab == regime
        if w <= 0 or mask.sum() < min_months:
            continue
        cov, _ = ledoit_wolf(returns[mask])
        covs.append(cov)
        means.append(x[mask].mean(axis=0))
        used[regime] = float(w)
    if not used:
        raise ValueError(f"no regime has {min_months} labelled months to blend")
    total = sum(used.values())
    pis = np.array([w / total for w in used.values()])
    mean = pis @ np.array(means)
    within = sum(p * c for p, c in zip(pis, covs, strict=True))
    between = sum(p * np.outer(m - mean, m - mean) for p, m in zip(pis, means, strict=True))
    return within + between, {r: float(p) for r, p in zip(used, pis, strict=True)}


def blend_weights(
    labels: pd.Series,
    current: str | None,
    confidence: float | None,
    recession_probability: float | None = None,
) -> dict[str, float]:
    """The regime probabilities the blend uses (decision 65).

    The macro agent's confidence goes to its current regime and the rest is spread by how often
    each regime has occurred (``labels``' base rates). If the agent gave a recession probability
    (a fraction), recession gets exactly that and the others share the remainder in proportion.
    """
    base = labels.value_counts(normalize=True).to_dict()
    c = 0.0 if confidence is None or current is None else float(np.clip(confidence, 0.0, 1.0))
    pi = {r: (1.0 - c) * f for r, f in base.items()}
    if current is not None:
        pi[current] = pi.get(current, 0.0) + c
    if recession_probability is not None:
        p = float(np.clip(recession_probability, 0.0, 1.0))
        rest = sum(v for r, v in pi.items() if r != "recession")
        pi = (
            {r: (v / rest) * (1.0 - p) for r, v in pi.items() if r != "recession"}
            if rest > 0
            else {}
        )
        pi["recession"] = p
    total = sum(pi.values())
    return {r: v / total for r, v in pi.items() if v > 0}


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

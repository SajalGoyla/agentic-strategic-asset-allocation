"""Return-series statistics for the historical-analysis skill.

Pure functions on simple returns in decimals (0.01 = 1%), monthly unless stated. They return NaN
when there is too little data; callers convert NaN to null in outputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

MONTHS_PER_YEAR = 12
TRADING_DAYS_PER_YEAR = 252
_NAN = float("nan")


def _clean(returns: pd.Series) -> pd.Series:
    return returns.dropna().astype(float)


def _aligned(a: pd.Series, b: pd.Series) -> pd.DataFrame:
    return pd.concat([a, b], axis=1, keys=["a", "b"]).dropna()


# --------------------------------------------------------------------------- return and risk
def annualized_return(returns: pd.Series) -> float:
    """Geometric (compound) annual return."""
    r = _clean(returns)
    if r.empty:
        return _NAN
    return float((1 + r).prod() ** (MONTHS_PER_YEAR / len(r)) - 1)


def cumulative_return(returns: pd.Series) -> float:
    r = _clean(returns)
    return float((1 + r).prod() - 1) if len(r) else _NAN


def annualized_volatility(returns: pd.Series) -> float:
    r = _clean(returns)
    return float(r.std(ddof=1) * math.sqrt(MONTHS_PER_YEAR)) if len(r) >= 2 else _NAN


def excess_returns(returns: pd.Series, risk_free: pd.Series) -> pd.Series:
    both = _aligned(returns, risk_free)
    return both["a"] - both["b"]


def sharpe_ratio(returns: pd.Series, risk_free: pd.Series) -> float:
    """Annualised mean excess return divided by annualised volatility of excess returns."""
    ex = excess_returns(returns, risk_free)
    if len(ex) < 2 or ex.std(ddof=1) == 0:
        return _NAN
    return float(ex.mean() * MONTHS_PER_YEAR / (ex.std(ddof=1) * math.sqrt(MONTHS_PER_YEAR)))


def sortino_ratio(returns: pd.Series, risk_free: pd.Series) -> float:
    """Annualised mean excess return divided by annualised downside deviation (target = risk-free)."""
    ex = excess_returns(returns, risk_free)
    if len(ex) < 2:
        return _NAN
    downside = math.sqrt(float((np.minimum(ex, 0.0) ** 2).mean())) * math.sqrt(MONTHS_PER_YEAR)
    return float(ex.mean() * MONTHS_PER_YEAR / downside) if downside > 0 else _NAN


def realized_volatility(daily_returns: pd.Series, days: int) -> float:
    """Annualised volatility of the last ``days`` daily returns (needs 90% of them present)."""
    r = _clean(daily_returns).tail(days)
    if len(r) < 0.9 * days:
        return _NAN
    return float(r.std(ddof=1) * math.sqrt(TRADING_DAYS_PER_YEAR))


# --------------------------------------------------------------------------- drawdowns
@dataclass(frozen=True)
class Drawdown:
    depth: float  # most negative peak-to-trough decline, e.g. -0.35; 0.0 if none
    peak: pd.Timestamp | None  # month-end of the peak; None if the peak was the window start
    trough: pd.Timestamp | None
    recovery: pd.Timestamp | None  # first month-end back at the peak; None if not recovered
    duration_months: int | None  # peak to recovery, or peak to window end if not recovered


def drawdown_series(returns: pd.Series) -> pd.Series:
    """Decline from the running peak of wealth, where wealth starts at 1 before the first return."""
    wealth = (1 + _clean(returns)).cumprod()
    return wealth / np.maximum(wealth.cummax(), 1.0) - 1


def max_drawdown(returns: pd.Series) -> Drawdown:
    r = _clean(returns)
    if r.empty:
        return Drawdown(_NAN, None, None, None, None)
    wealth = (1 + r).cumprod()
    running_peak = np.maximum(wealth.cummax(), 1.0)
    dd = wealth / running_peak - 1
    trough = dd.idxmin()
    depth = float(dd.loc[trough])
    if depth >= 0:
        return Drawdown(0.0, None, None, None, None)
    peak_level = float(running_peak.loc[trough])
    tolerance = 1e-12
    at_peak = wealth.loc[:trough][wealth.loc[:trough] >= peak_level - tolerance]
    peak = at_peak.index[-1] if len(at_peak) else None
    recovered = wealth.loc[trough:][wealth.loc[trough:] >= peak_level - tolerance]
    recovery = recovered.index[0] if len(recovered) else None
    start = r.index.get_loc(peak) if peak is not None else -1
    end = r.index.get_loc(recovery) if recovery is not None else len(r) - 1
    return Drawdown(depth, peak, trough, recovery, int(end - start))


def current_drawdown(returns: pd.Series) -> float:
    dd = drawdown_series(returns)
    return float(dd.iloc[-1]) if len(dd) else _NAN


# --------------------------------------------------------------------------- distribution
def value_at_risk(returns: pd.Series, level: float = 0.95) -> float:
    """Historical VaR as a positive loss: the (1 - level) quantile of returns, sign flipped."""
    r = _clean(returns)
    return float(-r.quantile(1 - level)) if len(r) >= 12 else _NAN


def conditional_value_at_risk(returns: pd.Series, level: float = 0.95) -> float:
    """Expected shortfall as a positive loss: mean of returns at or below the VaR quantile."""
    r = _clean(returns)
    if len(r) < 12:
        return _NAN
    return float(-r[r <= r.quantile(1 - level)].mean())


def skewness(returns: pd.Series) -> float:
    r = _clean(returns)
    return float(r.skew()) if len(r) >= 3 else _NAN


def excess_kurtosis(returns: pd.Series) -> float:
    r = _clean(returns)
    return float(r.kurt()) if len(r) >= 4 else _NAN


def hit_rate(returns: pd.Series) -> float:
    r = _clean(returns)
    return float((r > 0).mean()) if len(r) else _NAN


# --------------------------------------------------------------------------- co-movement
def correlation(a: pd.Series, b: pd.Series, min_periods: int = 12) -> float:
    both = _aligned(a, b)
    return float(both["a"].corr(both["b"])) if len(both) >= min_periods else _NAN


def beta(returns: pd.Series, benchmark: pd.Series, min_periods: int = 12) -> float:
    both = _aligned(returns, benchmark)
    if len(both) < min_periods or both["b"].var(ddof=1) == 0:
        return _NAN
    return float(both["a"].cov(both["b"]) / both["b"].var(ddof=1))


def correlation_matrix(returns: pd.DataFrame, min_periods: int = 12) -> pd.DataFrame:
    """Pairwise correlations using the months both assets have data."""
    return returns.corr(min_periods=min_periods)


def rolling_correlation(a: pd.Series, b: pd.Series, window: int = 36) -> pd.Series:
    both = _aligned(a, b)
    return both["a"].rolling(window).corr(both["b"])


def conditional_stats(returns: pd.Series, risk_free: pd.Series, labels: pd.Series) -> pd.DataFrame:
    """Return statistics grouped by a label per month (e.g. the macro regime at that time).
    Mean returns are arithmetic, which is what a regime-conditional premium averages."""
    df = pd.concat([returns, risk_free, labels], axis=1, keys=["r", "rf", "label"])
    df = df.dropna(subset=["r", "label"])
    rows = []
    for label, g in df.groupby("label", sort=True):
        r = g["r"]
        rows.append(
            {
                "regime": str(label),
                "months": len(r),
                "annualized_mean_return": float(r.mean() * MONTHS_PER_YEAR),
                "annualized_volatility": annualized_volatility(r),
                "sharpe_ratio": sharpe_ratio(r, g["rf"]),
                "hit_rate": hit_rate(r),
            }
        )
    return pd.DataFrame(rows)

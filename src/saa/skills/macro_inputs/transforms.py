"""Turning a raw FRED series into the comparable value a macro dimension is scored on.

The transforms are exactly ``saa.contracts.macro.Transform``: level, year-over-year,
month-over-month annualised, difference, z-score and percentile. They work on any native
frequency (daily, weekly, monthly, quarterly) because every lag is taken by date rather than by
row count, so a quarterly series is compared with the same quarter a year earlier and a daily
one with the nearest earlier observation.
"""

from __future__ import annotations

import pandas as pd

from saa.contracts.macro import Transform

DEFAULT_LOOKBACK_YEARS = 20
DEFAULT_DIFF_MONTHS = 12


def _clean(series: pd.Series) -> pd.Series:
    return series.dropna().astype(float).sort_index()


def lagged(series: pd.Series, offset: pd.DateOffset) -> pd.Series:
    """The value one ``offset`` earlier, carried forward from the nearest earlier observation."""
    series = _clean(series)
    prior = series.reindex(series.index - offset, method="ffill")
    prior.index = series.index
    return prior


def level(series: pd.Series) -> pd.Series:
    return _clean(series)


def _positive_base(prior: pd.Series) -> pd.Series:
    """Proportional change is undefined against a zero or negative base. Series centred on zero
    (CFNAI, the Sahm gap) would otherwise produce huge meaningless ratios, so those months
    become NaN and the caller is told to use `diff` or `level` instead."""
    return prior.where(prior > 0)


def yoy(series: pd.Series) -> pd.Series:
    """Proportional change over 12 months (0.03 = +3%). For index levels, not for rates."""
    series = _clean(series)
    return series / _positive_base(lagged(series, pd.DateOffset(years=1))) - 1


def mom_annualised(series: pd.Series) -> pd.Series:
    """One month's proportional change, compounded to a year."""
    series = _clean(series)
    return (series / _positive_base(lagged(series, pd.DateOffset(months=1)))) ** 12 - 1


def diff(series: pd.Series, months: int = DEFAULT_DIFF_MONTHS) -> pd.Series:
    """Absolute change over ``months``: the right transform for rates, spreads and indices
    that are already in percentage points or standard deviations."""
    series = _clean(series)
    return series - lagged(series, pd.DateOffset(months=months))


def zscore(series: pd.Series, lookback_years: int = DEFAULT_LOOKBACK_YEARS) -> pd.Series:
    """Standard deviations from the trailing mean, over a time-based window so that a
    quarterly and a daily series get the same amount of history."""
    series = _clean(series)
    window = f"{int(lookback_years * 365.25)}D"
    rolling = series.rolling(window, min_periods=12)
    return (series - rolling.mean()) / rolling.std(ddof=1)


def percentile(series: pd.Series, lookback_years: int = DEFAULT_LOOKBACK_YEARS) -> pd.Series:
    """Rank of the current value within the trailing window, 0 (lowest) to 1 (highest)."""
    series = _clean(series)
    window = f"{int(lookback_years * 365.25)}D"
    return series.rolling(window, min_periods=12).rank(pct=True)


def apply(
    series: pd.Series,
    transform: Transform | str,
    *,
    lookback_years: int = DEFAULT_LOOKBACK_YEARS,
    diff_months: int = DEFAULT_DIFF_MONTHS,
) -> pd.Series:
    """Apply one transform by name."""
    transform = Transform(transform)
    if transform is Transform.LEVEL:
        return level(series)
    if transform is Transform.YOY:
        return yoy(series)
    if transform is Transform.MOM_ANNUALISED:
        return mom_annualised(series)
    if transform is Transform.DIFF:
        return diff(series, months=diff_months)
    if transform is Transform.ZSCORE:
        return zscore(series, lookback_years=lookback_years)
    return percentile(series, lookback_years=lookback_years)

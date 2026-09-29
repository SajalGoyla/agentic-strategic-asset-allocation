"""Covariance skill: the 18-asset covariance matrix, point-in-time, as ``covariance.json``.

Ang, Azimbayev & Kim (2026) §3.1 step 3: "A covariance agent estimates the asset class
covariance matrix using historical data and macro forecasts." This is the deterministic half:
it computes every candidate estimator on the same window and writes the chosen one; the
regime-conditional estimator is the "macro forecasts" route, using the macro agent's labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from saa.contracts.base import Producer
from saa.contracts.portfolio import COVARIANCE_CONTRACT, CovarianceBody, CovarianceMethod
from saa.contracts.registry import read
from saa.data.store import DataStore
from saa.run import RunContext
from saa.skills.covariance import estimators as est

AGENT = "covariance"
REPORT = "covariance.md"
MIN_MONTHS = 36


@dataclass(frozen=True)
class CovarianceSettings:
    """Defaults chosen by an out-of-sample test on 1993-2026 data (see SKILL.md): Ledoit-Wolf
    over all available history was never singular, gave the best-conditioned matrices and the
    most accurate benchmark-volatility forecast. ``window_years=None`` means all history."""

    method: CovarianceMethod = CovarianceMethod.LEDOIT_WOLF
    window_years: float | None = None
    halflife_months: float = 60.0  # exponential estimator only; beat 12, 24 and 36
    min_regime_months: int = 24  # regime-conditional estimator only


@dataclass(frozen=True)
class CovarianceEstimate:
    """One estimator's result: the contract body plus diagnostics for the report."""

    body: CovarianceBody
    start: date
    end: date
    months: int
    average_correlation: float
    condition_number: float
    positive_definite: bool


def regime_labels_from(path: Path | str) -> pd.Series:
    """Month-end regime labels from a ``regime_history.json`` the macro agent wrote."""
    history = read("regime_history", path)
    return pd.Series(
        [m.regime.value for m in history.body.months],
        index=pd.DatetimeIndex([m.date for m in history.body.months]),
        name="regime",
    )


def _common_history(store: DataStore, as_of: pd.Timestamp) -> pd.DataFrame:
    """Months where every asset has a return. All 18 overlap from 1993-06."""
    returns = store.asset_returns(as_of=as_of).dropna(how="any")
    if len(returns) < MIN_MONTHS:
        raise ValueError(
            f"only {len(returns)} months with all assets present on {as_of.date()}; "
            f"need at least {MIN_MONTHS}"
        )
    return returns


def _month_key(index: pd.Index) -> pd.PeriodIndex:
    return pd.DatetimeIndex(index).to_period("M")


def _build(
    window: pd.DataFrame,
    monthly: np.ndarray,
    method: CovarianceMethod,
    shrinkage: float | None,
    regime: str | None,
) -> CovarianceEstimate:
    annual = est.annualise(monthly)
    annual = (annual + annual.T) / 2  # remove floating-point asymmetry before validation
    ids = list(window.columns)
    body = CovarianceBody(
        asset_ids=ids,
        method=method,
        window_years=round(len(window) / est.MONTHS_PER_YEAR, 2),
        matrix=annual.tolist(),
        volatilities_pct={a: float(100 * np.sqrt(annual[i, i])) for i, a in enumerate(ids)},
        regime=regime,
        shrinkage=shrinkage,
    )
    return CovarianceEstimate(
        body=body,
        start=window.index[0].date(),
        end=window.index[-1].date(),
        months=len(window),
        average_correlation=est.average_correlation(annual),
        condition_number=est.condition_number(annual),
        positive_definite=est.is_positive_definite(annual),
    )


def estimate_covariance(
    store: DataStore,
    *,
    as_of: str | date | pd.Timestamp | None = None,
    method: CovarianceMethod | str | None = None,
    settings: CovarianceSettings | None = None,
    regime: str | None = None,
    regime_labels: pd.Series | None = None,
) -> CovarianceEstimate:
    """One estimator, using only returns available on ``as_of`` (default: today).

    The regime-conditional estimator pools every month since 1993 whose label equals
    ``regime`` and shrinks with Ledoit-Wolf, because a single regime rarely has enough months
    for 18 assets on its own.
    """
    settings = settings or CovarianceSettings()
    method = CovarianceMethod(method or settings.method)
    as_of_ts = pd.Timestamp(as_of if as_of is not None else date.today()).normalize()
    returns = _common_history(store, as_of_ts)

    if method is CovarianceMethod.REGIME_CONDITIONAL:
        if regime is None or regime_labels is None:
            raise ValueError("regime_conditional needs both a regime and regime_labels")
        labels = pd.Series(regime_labels.to_numpy(), index=_month_key(regime_labels.index))
        in_regime = _month_key(returns.index).map(labels.to_dict()) == regime
        window = returns[np.asarray(in_regime, dtype=bool)]
        if len(window) < settings.min_regime_months:
            raise ValueError(
                f"only {len(window)} months labelled {regime!r} before {as_of_ts.date()}; "
                f"need {settings.min_regime_months}"
            )
        monthly, shrinkage = est.ledoit_wolf(window)
        return _build(window, monthly, method, shrinkage, regime)

    if settings.window_years is None:
        window = returns
    else:
        window = returns.iloc[-int(round(settings.window_years * est.MONTHS_PER_YEAR)) :]
    if len(window) < MIN_MONTHS:
        raise ValueError(f"window has {len(window)} months; need at least {MIN_MONTHS}")
    if method is CovarianceMethod.SAMPLE:
        return _build(window, est.sample_covariance(window), method, None, None)
    if method is CovarianceMethod.LEDOIT_WOLF:
        monthly, shrinkage = est.ledoit_wolf(window)
        return _build(window, monthly, method, shrinkage, None)
    return _build(
        window,
        est.exponential_covariance(window, settings.halflife_months),
        method,
        None,
        None,
    )


def compare_estimators(
    store: DataStore,
    *,
    as_of: str | date | pd.Timestamp | None = None,
    settings: CovarianceSettings | None = None,
    regime: str | None = None,
    regime_labels: pd.Series | None = None,
) -> dict[CovarianceMethod, CovarianceEstimate]:
    """Every estimator on the same data; regime-conditional only when labels are supplied."""
    methods = [CovarianceMethod.SAMPLE, CovarianceMethod.LEDOIT_WOLF, CovarianceMethod.EXPONENTIAL]
    if regime is not None and regime_labels is not None:
        methods.append(CovarianceMethod.REGIME_CONDITIONAL)
    return {
        m: estimate_covariance(
            store,
            as_of=as_of,
            method=m,
            settings=settings,
            regime=regime,
            regime_labels=regime_labels,
        )
        for m in methods
    }


# --------------------------------------------------------------------------- outputs
def render_report(
    chosen: CovarianceMethod, estimates: dict[CovarianceMethod, CovarianceEstimate], as_of: date
) -> str:
    """Markdown comparing the estimators, so the choice is auditable (§3.2)."""
    pick = estimates[chosen]
    methods = list(estimates)
    lines = [
        f"# Covariance as of {as_of}",
        "",
        f"Chosen estimator: **{chosen.value}**, {pick.months} months "
        f"({pick.start} to {pick.end})"
        + (f", shrinkage {pick.body.shrinkage:.2f}" if pick.body.shrinkage is not None else "")
        + (f", regime `{pick.body.regime}`" if pick.body.regime else "")
        + ".",
        "",
        "| Estimator | Months | Avg correlation | Condition number | Positive definite |",
        "|---|---|---|---|---|",
    ]
    for m in methods:
        e = estimates[m]
        lines.append(
            f"| {m.value} | {e.months} | {e.average_correlation:.2f} | "
            f"{e.condition_number:,.0f} | {'yes' if e.positive_definite else 'NO'} |"
        )
    lines += [
        "",
        "## Annualised volatility by estimator (%)",
        "",
        "| Asset | " + " | ".join(m.value for m in methods) + " |",
        "|---|" + "---|" * len(methods),
    ]
    for asset in pick.body.asset_ids:
        vols = " | ".join(f"{estimates[m].body.volatilities_pct[asset]:.1f}" for m in methods)
        lines.append(f"| {asset} | {vols} |")
    lines += [
        "",
        "Ledoit-Wolf shrinks correlations toward their average while keeping each asset's own "
        "variance; exponential weighting reacts faster to a change in volatility regime; "
        "regime-conditional pools only the months the macro agent labelled with the current "
        "regime. See `src/saa/skills/covariance/SKILL.md`.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(
    chosen: CovarianceMethod,
    estimates: dict[CovarianceMethod, CovarianceEstimate],
    run: RunContext,
    provenance: dict[str, dict],
) -> list[Path]:
    """Write ``pc/covariance.json`` (the chosen estimator) and ``reports/covariance.md``.

    Refuses a matrix that is not numerically positive definite: every PC optimiser would fail
    to invert it or produce extreme weights. The usual cause is two assets sharing a proxy
    (International Sovereigns and Corporates are identical before 2007), which Ledoit-Wolf
    shrinkage repairs and the sample and exponential estimators do not.
    """
    if not estimates[chosen].positive_definite:
        raise ValueError(
            f"{chosen.value} covariance is singular for this window (likely two assets sharing "
            "a pre-ETF proxy); use ledoit_wolf, which shrinks it to a usable matrix"
        )
    report = run.write_report(render_report(chosen, estimates, run.as_of), REPORT)
    path = run.write(
        COVARIANCE_CONTRACT,
        AGENT,
        estimates[chosen].body,
        produced_by=Producer.SCRIPT,
        provenance=provenance,
        report_path=report,
    )
    return [path, report]

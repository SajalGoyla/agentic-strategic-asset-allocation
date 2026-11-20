"""Out-of-sample validation of the covariance estimators (decision 63).

Decision 17 chose Ledoit-Wolf by comparing estimators with each other; this asks of each one
whether its forecasts came true. At every year-end the estimator is fitted on data up to that
date only, and two of its forecasts are compared with what followed:

- the volatility of the IPS benchmark and of equal weight, against the volatility realised over
  the next 12 months (monthly returns, annualised the same way the forecast is);
- the US large cap / intermediate Treasuries correlation, against the one realised over the
  next 36 months -- the single number that most moves the benchmark and risk parity, and the
  one a long window is slowest to update (it missed the post-2020 sign change).

The record is what the covariance agent weighs when it chooses an estimator for the current
regime. Deterministic; no LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from saa.contracts.portfolio import CovarianceMethod, EstimatorValidation
from saa.data.store import DataStore
from saa.skills.covariance import estimators as est

# The estimators the covariance agent may choose between. The sample estimator is excluded:
# it was singular in every year before 2008 (decision 17).
VALIDATED = (
    CovarianceMethod.LEDOIT_WOLF,
    CovarianceMethod.EXPONENTIAL,
    CovarianceMethod.REGIME_CONDITIONAL,
    CovarianceMethod.RECENT_VOLATILITY,
    CovarianceMethod.REGIME_BLEND,
)
STOCK, BOND = "us_large_cap", "intermediate_treasuries"
FIRST_YEAR = 1999  # six years of the 1993-06 panel behind the first forecast
VOL_HORIZON_MONTHS = 12
CORRELATION_HORIZON_MONTHS = 36


@dataclass(frozen=True)
class ValidationSettings:
    halflife_months: float = 60.0
    volatility_halflife_months: float = 6.0
    min_regime_months: int = 24
    first_year: int = FIRST_YEAR
    # The blend's confidence in the label current at each past year-end. The macro agent's own
    # confidence is not on record for past dates, so the record uses a neutral 0.5 and no
    # recession override; the live blend uses the agent's figures.
    blend_confidence: float = 0.5


def _fit(
    method: CovarianceMethod,
    train: pd.DataFrame,
    settings: ValidationSettings,
    labels: pd.Series | None,
) -> np.ndarray | None:
    """Monthly covariance from ``train``, or None where the estimator cannot be fitted."""
    if method is CovarianceMethod.LEDOIT_WOLF:
        return est.ledoit_wolf(train)[0]
    if method is CovarianceMethod.EXPONENTIAL:
        return est.exponential_covariance(train, settings.halflife_months)
    if method is CovarianceMethod.RECENT_VOLATILITY:
        return est.recent_volatility_covariance(train, settings.volatility_halflife_months)[0]
    if labels is None:
        return None
    months = train.index.to_period("M")
    known = labels[labels.index <= months[-1]]
    if known.empty:
        return None
    aligned = months.map(known.to_dict())
    if method is CovarianceMethod.REGIME_BLEND:
        has = np.asarray(aligned.notna(), dtype=bool)
        weights = est.blend_weights(known, str(known.iloc[-1]), settings.blend_confidence)
        try:
            return est.regime_blend_covariance(
                train[has],
                pd.Series(np.asarray(aligned)[has]),
                weights,
                settings.min_regime_months,
            )[0]
        except ValueError:
            return None
    window = train[np.asarray(aligned == known.iloc[-1], dtype=bool)]
    if len(window) < settings.min_regime_months:
        return None
    return est.ledoit_wolf(window)[0]


def validate_estimators(
    store: DataStore,
    *,
    as_of: str | date | pd.Timestamp,
    benchmark: pd.Series,
    regime_labels: pd.Series | None = None,
    settings: ValidationSettings | None = None,
) -> list[EstimatorValidation]:
    """Each validated estimator's record over the year-ends whose following 12 months are known
    by ``as_of``. ``regime_labels`` (month-end labels) enables the regime-conditional estimator,
    which at each year-end conditions on the label then current."""
    settings = settings or ValidationSettings()
    returns = store.asset_returns(as_of=pd.Timestamp(as_of)).dropna(how="any")
    ids = list(returns.columns)
    portfolios = {
        "benchmark": benchmark.reindex(ids).fillna(0.0).to_numpy(dtype=float),
        "equal_weight": np.full(len(ids), 1.0 / len(ids)),
    }
    labels = None
    if regime_labels is not None and not regime_labels.empty:
        labels = pd.Series(
            regime_labels.to_numpy(), index=pd.DatetimeIndex(regime_labels.index).to_period("M")
        )
    pair = (ids.index(STOCK), ids.index(BOND)) if {STOCK, BOND} <= set(ids) else None

    records: dict[CovarianceMethod, dict[str, list[float]]] = {
        m: {"ratio": [], "log": [], "corr": []} for m in VALIDATED
    }
    year = settings.first_year
    while True:
        end = pd.Timestamp(f"{year}-12-31")
        train = returns[returns.index <= end]
        test = returns[returns.index > end]
        if len(test) < VOL_HORIZON_MONTHS:
            break
        year += 1
        if len(train) < 36:
            continue
        vol_test = test.iloc[:VOL_HORIZON_MONTHS].to_numpy()
        corr_test = test.iloc[:CORRELATION_HORIZON_MONTHS]
        for method in VALIDATED:
            monthly = _fit(method, train, settings, labels)
            if monthly is None:
                continue
            annual = est.annualise(monthly)
            rec = records[method]
            for name, w in portfolios.items():
                forecast = float(np.sqrt(max(float(w @ annual @ w), 0.0)))
                realised = float((vol_test @ w).std(ddof=1) * np.sqrt(est.MONTHS_PER_YEAR))
                if forecast <= 0 or realised <= 0:
                    continue
                rec["log"].append(abs(np.log(realised / forecast)))
                if name == "benchmark":
                    rec["ratio"].append(realised / forecast)
            if pair is not None and len(corr_test) == CORRELATION_HORIZON_MONTHS:
                i, j = pair
                forecast_corr = annual[i, j] / np.sqrt(annual[i, i] * annual[j, j])
                realised_corr = float(corr_test.iloc[:, [i, j]].corr().iloc[0, 1])
                rec["corr"].append(abs(forecast_corr - realised_corr))

    out = []
    for method, rec in records.items():
        if not rec["ratio"]:
            continue
        out.append(
            EstimatorValidation(
                method=method,
                years=len(rec["ratio"]),
                realised_to_forecast=float(np.median(rec["ratio"])),
                abs_log_error=float(np.mean(rec["log"])),
                stock_bond_correlation_error=float(np.mean(rec["corr"])) if rec["corr"] else None,
            )
        )
    return out


def render_validation(records: list[EstimatorValidation]) -> str:
    lines = [
        "## Out-of-sample record (decision 63)",
        "",
        "Fitted at each year-end on data to that date only. *Realised / forecast* is the median "
        "ratio for the IPS benchmark's volatility over the next 12 months (1.0 is unbiased; "
        "below 1 the estimator forecast too much risk). *Error* is the mean |log(realised / "
        "forecast)| over the benchmark and equal weight. *Stock-bond error* is the mean absolute "
        "error of the US large cap / intermediate Treasuries correlation over the next 36 months.",
        "",
        "| Estimator | Years | Realised / forecast | Error | Stock-bond error |",
        "|---|---|---|---|---|",
    ]
    for r in records:
        corr = (
            "-"
            if r.stock_bond_correlation_error is None
            else f"{r.stock_bond_correlation_error:.2f}"
        )
        lines.append(
            f"| {r.method.value} | {r.years} | {r.realised_to_forecast:.2f} | "
            f"{r.abs_log_error:.3f} | {corr} |"
        )
    return "\n".join(lines) + "\n"

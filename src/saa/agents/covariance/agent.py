"""Covariance agent (stage 3, decision 63): choose the estimator the PC agents receive.

Ang, Azimbayev & Kim (2026) §3.1 step 3: "A covariance agent estimates the asset class
covariance matrix using historical data and macro forecasts." The arithmetic is the covariance
skill's: every estimator on the same point-in-time data, and each one's out-of-sample record.
The judgment is the agent's: which of the validated estimators suits the macro regime now, and
why. The model chooses among computed matrices; it never writes one.

`--no-llm` keeps decision 17's default, Ledoit-Wolf over all history.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import create_model

from saa.config import Config, load_config
from saa.contracts.base import ModelCall, Producer
from saa.contracts.portfolio import (
    COVARIANCE_CONTRACT,
    CovarianceBody,
    CovarianceJudgment,
    CovarianceMethod,
    EstimatorValidation,
)
from saa.contracts.registry import read
from saa.data.store import DataStore
from saa.llm import LlmClient, tier_for
from saa.run import RunContext
from saa.skills.covariance import (
    VALIDATED,
    CovarianceEstimate,
    compare_estimators,
    render_report,
    render_validation,
    validate_estimators,
)
from saa.skills.covariance.analysis import REPORT
from saa.skills.covariance.estimators import blend_weights
from saa.skills.covariance.validation import BOND, STOCK
from saa.skills.portfolio_construction import PortfolioInputs, risk_parity
from saa.skills.portfolio_construction.analysis import benchmark_weights

log = logging.getLogger(__name__)

AGENT = "covariance"
AGENT_DIR = Path(__file__).parent
DEFAULT = CovarianceMethod.LEDOIT_WOLF
MIN_RATIONALE_CHARS = 200
# Assets whose volatility the prompt shows per estimator: the cash-like pair, the benchmark's
# legs, and the riskiest classes.
SHOWN = [
    "cash",
    "short_treasuries",
    "intermediate_treasuries",
    "ig_corporates",
    "us_large_cap",
    "emerging_markets",
    "gold",
    "commodities",
]


@dataclass
class CovarianceResult:
    body: CovarianceBody
    estimates: dict[CovarianceMethod, CovarianceEstimate]
    validation: list[EstimatorValidation]
    path: Path
    call: ModelCall | None = None

    @property
    def cost_usd(self) -> float:
        return (self.call.cost_usd or 0.0) if self.call else 0.0


def system_prompt() -> str:
    return (AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")


def judgment_model(eligible: list[CovarianceMethod]) -> type[CovarianceJudgment]:
    """``CovarianceJudgment`` narrowed to the estimators on offer."""
    choice = StrEnum("EligibleEstimator", {m.name: m.value for m in eligible})
    return create_model("CovarianceJudgmentFor", __base__=CovarianceJudgment, method=(choice, ...))


def _macro(run: RunContext) -> tuple[str | None, float | None, str | None, float | None]:
    """The macro agent's regime, confidence, qualifier and recession probability (the midpoint
    of its range, as a fraction), if this run has a macro view."""
    path = run.path("macro_view")
    if not path.exists():
        return None, None, None, None
    j = read("macro_view", path).body.judgment
    rp = j.recession_probability
    return (
        j.regime.value,
        j.confidence_score,
        getattr(j, "regime_qualifier", None),
        (rp.low_pct + rp.high_pct) / 200.0,
    )


def risk_parity_volatility(body: CovarianceBody, cash_like: list[str]) -> float:
    """What the risk-only PC methods will see: the volatility of equal-risk-contribution over
    the non-cash-like assets (decision 61) under this matrix. Below the 8% floor, the CIO's
    repair has to make up the difference (decisions 62, 64)."""
    ids = [a for a in body.asset_ids if a not in cash_like]
    cov = pd.DataFrame(body.matrix, index=body.asset_ids, columns=body.asset_ids)
    w = risk_parity(PortfolioInputs(asset_ids=ids, covariance=cov))
    return _volatility(body, w)


def _correlation(body: CovarianceBody, a: str, b: str) -> float | None:
    if a not in body.asset_ids or b not in body.asset_ids:
        return None
    m = np.asarray(body.matrix)
    i, j = body.asset_ids.index(a), body.asset_ids.index(b)
    return float(m[i, j] / np.sqrt(m[i, i] * m[j, j]))


def _volatility(body: CovarianceBody, weights: pd.Series) -> float:
    w = weights.reindex(body.asset_ids).fillna(0.0).to_numpy(dtype=float)
    return 100 * float(np.sqrt(max(float(w @ np.asarray(body.matrix) @ w), 0.0)))


def build_prompt(
    estimates: dict[CovarianceMethod, CovarianceEstimate],
    validation: list[EstimatorValidation],
    *,
    benchmark: pd.Series,
    regime: str | None,
    confidence: float | None,
    qualifier: str | None,
    as_of,
    ips_status: str,
    cash_like: list[str] | None = None,
) -> str:
    eligible = list(estimates)
    rows = [
        "| Estimator | Months | Shrinkage | Avg corr | Stock-bond corr | Benchmark vol % | "
        "Risk parity vol % | Condition no. |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m, e in estimates.items():
        b = e.body
        corr = _correlation(b, STOCK, BOND)
        rows.append(
            f"| {m.value} | {e.months} | "
            + (f"{b.shrinkage:.2f}" if b.shrinkage is not None else "-")
            + f" | {e.average_correlation:.2f} | "
            + ("-" if corr is None else f"{corr:+.2f}")
            + f" | {_volatility(b, benchmark):.2f} | "
            + f"{risk_parity_volatility(b, cash_like or []):.2f} | {e.condition_number:,.0f} |"
        )
    vols = [
        "| Asset | " + " | ".join(m.value for m in eligible) + " |",
        "|---|" + "---|" * len(eligible),
    ]
    for asset in SHOWN:
        if all(asset in estimates[m].body.volatilities_pct for m in eligible):
            vols.append(
                f"| {asset} | "
                + " | ".join(f"{estimates[m].body.volatilities_pct[asset]:.1f}" for m in eligible)
                + " |"
            )
    record = [r for r in validation if r.method in estimates]
    regime_line = (
        f"**{regime}**"
        + (f" ({qualifier})" if qualifier else "")
        + (f", confidence {confidence:.2f}" if confidence is not None else "")
        if regime
        else "unknown (no macro view in this run)"
    )
    regime_note = (
        f"The regime-conditional estimator uses only the {estimates[CovarianceMethod.REGIME_CONDITIONAL].months} "
        f"months labelled `{regime}` since 1993."
        if CovarianceMethod.REGIME_CONDITIONAL in estimates
        else "The regime-conditional estimator is not on offer: there is no regime call, or too "
        "few months carry its label."
    )
    blend = estimates.get(CovarianceMethod.REGIME_BLEND)
    if blend is not None and blend.body.regime_weights:
        regime_note += (
            " The regime blend mixes the regimes' matrices with probabilities "
            + ", ".join(
                f"{r} {w:.0%}"
                for r, w in sorted(blend.body.regime_weights.items(), key=lambda x: -x[1])
            )
            + " (your confidence on the current regime, the rest by how often each regime has "
            + ("occurred, and recession at the macro agent's probability).")
        )
    return f"""Choose the covariance estimator the portfolio-construction agents will receive.

As-of date: {as_of}
Macro regime: {regime_line}
Governing IPS status: {ips_status}

{regime_note}

## The estimators now
{chr(10).join(rows)}

## Annualised volatility by estimator (%)
{chr(10).join(vols)}

{render_validation(record)}
Choose one of: {", ".join(m.value for m in eligible)}.
"""


def fallback_judgment(
    validation: list[EstimatorValidation], regime: str | None
) -> CovarianceJudgment:
    lw = next((r for r in validation if r.method is DEFAULT), None)
    record = (
        f" Its out-of-sample record over {lw.years} year-ends: realised benchmark volatility "
        f"{lw.realised_to_forecast:.2f}x the forecast at the median, mean log error "
        f"{lw.abs_log_error:.3f}."
        if lw
        else ""
    )
    return CovarianceJudgment(
        method=DEFAULT,
        rationale=(
            "No model was consulted (--no-llm), so the estimator is decision 17's default: "
            "Ledoit-Wolf shrinkage over all history, which was never singular, gave the best-"
            "conditioned matrices and the most accurate benchmark-volatility forecast of the "
            f"estimators compared.{record}"
            + (f" The regime call ({regime}) was not used." if regime else "")
        ),
        what_would_change_it=(
            "A model-backed run weighs the regime and the estimators' records and may choose "
            "another validated estimator instead."
        ),
    )


def run_covariance(
    run: RunContext,
    store: DataStore,
    *,
    config: Config | None = None,
    llm: LlmClient | None = None,
    regime_labels: pd.Series | None = None,
) -> CovarianceResult:
    """Compute and validate every estimator, choose one, and write ``pc/covariance.json``."""
    config = config or load_config()
    regime, confidence, qualifier, recession = _macro(run)
    if regime is None and regime_labels is not None and not regime_labels.empty:
        regime = str(regime_labels.iloc[-1])
    weights = None
    if regime_labels is not None and not regime_labels.empty:
        known = regime_labels[pd.DatetimeIndex(regime_labels.index) <= pd.Timestamp(run.as_of)]
        weights = blend_weights(known, regime, confidence, recession)
    estimates_all = compare_estimators(
        store,
        as_of=run.as_of,
        regime=regime,
        regime_labels=regime_labels,
        regime_weights=weights,
    )
    estimates = {
        m: estimates_all[m]
        for m in VALIDATED
        if m in estimates_all and estimates_all[m].positive_definite
    }
    if DEFAULT not in estimates:
        raise ValueError("the Ledoit-Wolf estimate is not positive definite; see decision 17")
    benchmark = benchmark_weights(config)
    validation = validate_estimators(
        store, as_of=run.as_of, benchmark=benchmark, regime_labels=regime_labels
    )

    call = None
    if llm is None:
        judgment = fallback_judgment(validation, regime)
        producer = Producer.SCRIPT
    else:

        def check(j) -> None:
            if len(j.rationale) < MIN_RATIONALE_CHARS:
                raise ValueError(
                    f"rationale is {len(j.rationale)} characters; say why this estimator suits "
                    f"the regime against the others' records (minimum {MIN_RATIONALE_CHARS})"
                )

        result = llm.judge(
            judgment_model(list(estimates)),
            system=system_prompt(),
            prompt=build_prompt(
                estimates,
                validation,
                benchmark=benchmark,
                regime=regime,
                confidence=confidence,
                qualifier=qualifier,
                as_of=run.as_of,
                ips_status=run.ips_status,
                cash_like=config.universe.cash_like_ids,
            ),
            tier=tier_for(AGENT),
            effort="medium",
            check=check,
        )
        parsed, call = result.value, result.call
        judgment = CovarianceJudgment(
            method=CovarianceMethod(str(parsed.method)),
            rationale=parsed.rationale,
            what_would_change_it=parsed.what_would_change_it,
        )
        producer = Producer.HYBRID

    chosen = estimates[judgment.method]
    body = chosen.body.model_copy(update={"judgment": judgment, "validation": validation})
    report_text = (
        render_report(judgment.method, estimates_all, run.as_of)
        + "\n"
        + render_validation(validation)
        + f"\n## Choice\n\n**{judgment.method.value}**. {judgment.rationale}\n\n"
        f"*What would change it:* {judgment.what_would_change_it}\n"
    )
    report = run.write_report(report_text, REPORT)
    path = run.write(
        COVARIANCE_CONTRACT,
        AGENT,
        body,
        produced_by=producer,
        provenance=store.provenance(),
        report_path=report,
        model_calls=[call] if call is not None else None,
    )
    return CovarianceResult(
        body=body, estimates=estimates, validation=validation, path=path, call=call
    )


def render_summary(result: CovarianceResult) -> str:
    b = result.body
    return (
        f"Covariance: {b.method.value}"
        + (f" (regime {b.regime})" if b.regime else "")
        + f", {b.window_years:.1f} years; chosen by "
        + ("the model" if result.call else "the default (--no-llm)")
        + f".\n  output   {result.path}"
    )

"""The Investment Policy Statement: typed model and the single compliance check.

Ang, Azimbayev & Kim (2026) make the IPS the governing document of the whole pipeline (§3.1):
humans write it, every agent reads it, the CRO agent checks every candidate portfolio against
it, and the CIO agent is bound by it -- compliance is "non-negotiable" (§3.6).

``check_compliance`` is deliberately the *only* implementation of those rules. The CRO agent
(Phase 3) and the CIO agent (Phase 3) both call it, so the two cannot drift apart and a rule
change lands in one place.

Two design points worth knowing before reading the code:

* **Hard vs. soft.** A hard violation disqualifies a portfolio; a soft one is recorded and
  surfaced in the board memo. The return target is soft because a portfolio cannot *guarantee*
  a return -- the risk limits are what the IPS can actually bind.
* **Unevaluated is not compliant.** Metrics arrive at different pipeline stages (ex-ante
  volatility exists at portfolio construction, realised drawdown only after a backtest). A
  missing metric is reported in ``not_evaluated`` rather than silently passing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:  # pragma: no cover - import cycle guard; annotations are lazy
    from saa.config import Universe

Severity = Literal["hard", "soft"]

HARD, SOFT = "hard", "soft"

# Weights are floats coming out of optimisers; compare with a tolerance rather than exactly.
_TOL = 1e-9
_SUM_TOL = 1e-6


# --------------------------------------------------------------------------- policy model
class Bound(BaseModel):
    min: float = 0.0
    max: float = 1.0

    @model_validator(mode="after")
    def _ordered(self) -> Bound:
        if self.min > self.max:
            raise ValueError(f"bound min {self.min} exceeds max {self.max}")
        return self

    def contains(self, value: float) -> bool:
        return self.min - _TOL <= value <= self.max + _TOL


class Permitted(BaseModel):
    long_only: bool = True
    leverage: bool = False
    derivatives: bool = False


class UniverseBounds(BaseModel):
    per_asset: Bound = Field(default_factory=Bound)
    per_group: dict[str, Bound] = Field(default_factory=dict)


class UniversePolicy(BaseModel):
    source: str
    permitted: Permitted = Field(default_factory=Permitted)
    bounds: UniverseBounds = Field(default_factory=UniverseBounds)


class ReturnObjective(BaseModel):
    type: Literal["real_cpi_plus"]
    min_pct: float
    max_pct: float
    inflation_series: str
    severity: Severity = SOFT

    @model_validator(mode="after")
    def _ordered(self) -> ReturnObjective:
        if self.min_pct > self.max_pct:
            raise ValueError(f"return target min {self.min_pct} exceeds max {self.max_pct}")
        return self


class VolatilityObjective(BaseModel):
    min_pct: float
    max_pct: float
    severity: Severity = HARD

    @model_validator(mode="after")
    def _ordered(self) -> VolatilityObjective:
        if self.min_pct > self.max_pct:
            raise ValueError(f"volatility band min {self.min_pct} exceeds max {self.max_pct}")
        return self


class DrawdownObjective(BaseModel):
    limit_pct: float
    severity: Severity = HARD

    @model_validator(mode="after")
    def _negative(self) -> DrawdownObjective:
        if self.limit_pct >= 0:
            raise ValueError(f"drawdown limit must be negative, got {self.limit_pct}")
        return self


class Objectives(BaseModel):
    return_: ReturnObjective = Field(alias="return")
    volatility: VolatilityObjective
    max_drawdown: DrawdownObjective
    cma_horizon_years: int

    model_config = {"populate_by_name": True}


class Benchmark(BaseModel):
    id: str
    name: str
    weights: dict[str, float]
    rebalance: str = "quarterly"

    @model_validator(mode="after")
    def _sums_to_one(self) -> Benchmark:
        total = sum(self.weights.values())
        if abs(total - 1.0) > _SUM_TOL:
            raise ValueError(f"benchmark {self.id} weights sum to {total:.6f}, expected 1.0")
        return self


class TrackingError(BaseModel):
    max_ex_ante_pct: float
    severity: Severity = HARD


class ActiveRisk(BaseModel):
    benchmark: Benchmark
    tracking_error: TrackingError


class Rebalancing(BaseModel):
    cadence: str
    drift_trigger_pct: float


class EscalationTrigger(BaseModel):
    condition: str
    action: str
    threshold: float | None = None
    note: str | None = None


class IPS(BaseModel):
    version: float
    status: Literal["draft", "ratified"] = "draft"
    ratified_by: str | None = None
    ratified_on: date | None = None
    universe: UniversePolicy
    objectives: Objectives
    active_risk: ActiveRisk
    rebalancing: Rebalancing
    escalation: list[EscalationTrigger] = Field(default_factory=list)

    @model_validator(mode="after")
    def _ratification(self) -> IPS:
        if self.status == "ratified" and not (self.ratified_by and self.ratified_on):
            raise ValueError("a ratified IPS needs both ratified_by and ratified_on")
        return self

    @property
    def is_draft(self) -> bool:
        """Agents should state in their output when they ran against an unratified IPS."""
        return self.status == "draft"

    def group_bound(self, group: str) -> Bound | None:
        return self.universe.bounds.per_group.get(group)


# ------------------------------------------------------------------------ compliance check
class PortfolioMetrics(BaseModel):
    """Risk and return metrics for one candidate portfolio, in percent.

    Every field is optional because metrics become available at different pipeline stages.
    Whatever is missing is reported as ``not_evaluated``, never as a pass.
    """

    expected_return_pct: float | None = None  # nominal, over objectives.cma_horizon_years
    expected_inflation_pct: float | None = None  # to convert the above to real
    expected_volatility_pct: float | None = None  # ex-ante, from the covariance matrix
    max_drawdown_pct: float | None = None  # backtest, negative
    ex_ante_tracking_error_pct: float | None = None  # vs. active_risk.benchmark


@dataclass(frozen=True)
class Violation:
    rule: str
    severity: str
    message: str
    observed: float | None = None
    limit: float | None = None
    entity: str | None = None


@dataclass
class ComplianceReport:
    """Result of checking one portfolio. ``compliant`` means no *hard* violations."""

    violations: list[Violation] = field(default_factory=list)
    not_evaluated: list[str] = field(default_factory=list)

    @property
    def compliant(self) -> bool:
        return not any(v.severity == HARD for v in self.violations)

    @property
    def hard(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == HARD]

    @property
    def soft(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == SOFT]

    def add(self, rule: str, severity: str, message: str, **kw) -> None:
        self.violations.append(Violation(rule, severity, message, **kw))

    def to_dict(self) -> dict:
        """Shape embedded in risk_report.json and cio_decision.json."""
        return {
            "compliant": self.compliant,
            "violations": [asdict(v) for v in self.violations],
            "not_evaluated": list(self.not_evaluated),
        }

    def summary(self) -> str:
        if self.compliant and not self.violations:
            return "compliant"
        parts = [f"{len(self.hard)} hard", f"{len(self.soft)} soft"]
        if self.not_evaluated:
            parts.append(f"{len(self.not_evaluated)} not evaluated")
        return ", ".join(parts)


def real_return_pct(nominal_pct: float, inflation_pct: float) -> float:
    """Fisher-exact real return, in percent."""
    return ((1 + nominal_pct / 100) / (1 + inflation_pct / 100) - 1) * 100


def check_compliance(
    weights: dict[str, float],
    metrics: PortfolioMetrics | None,
    ips: IPS,
    universe: Universe,
) -> ComplianceReport:
    """Check one candidate portfolio against every IPS rule.

    ``weights`` maps asset id (as in ``config/universe.yaml``) to portfolio weight. Assets the
    portfolio does not hold may be omitted or given a zero weight.
    """
    report = ComplianceReport()
    metrics = metrics or PortfolioMetrics()
    _check_structure(weights, ips, universe, report)
    _check_objectives(metrics, ips, report)
    _check_active_risk(metrics, ips, report)
    return report


def _check_structure(
    weights: dict[str, float], ips: IPS, universe: Universe, report: ComplianceReport
) -> None:
    known = {a.id: a for a in universe.assets}
    permitted = ips.universe.permitted

    unknown = sorted(set(weights) - set(known))
    for asset_id in unknown:
        report.add(
            "universe.membership",
            HARD,
            f"{asset_id!r} is not in the IPS universe",
            entity=asset_id,
            observed=weights[asset_id],
        )

    held = {k: v for k, v in weights.items() if k in known}

    total = sum(held.values())
    if abs(total - 1.0) > _SUM_TOL:
        report.add(
            "universe.fully_invested",
            HARD,
            f"weights sum to {total:.4f}, expected 1.0",
            observed=total,
            limit=1.0,
        )

    if permitted.long_only:
        for asset_id, weight in sorted(held.items()):
            if weight < -_TOL:
                report.add(
                    "universe.long_only",
                    HARD,
                    f"{asset_id} has a short position ({weight:.4f}); the IPS is long-only",
                    entity=asset_id,
                    observed=weight,
                    limit=0.0,
                )

    if not permitted.leverage:
        gross = sum(abs(w) for w in held.values())
        if gross > 1.0 + _SUM_TOL:
            report.add(
                "universe.leverage",
                HARD,
                f"gross exposure {gross:.4f} exceeds 1.0; the IPS permits no leverage",
                observed=gross,
                limit=1.0,
            )

    per_asset = ips.universe.bounds.per_asset
    for asset_id, weight in sorted(held.items()):
        if not per_asset.contains(weight):
            report.add(
                "bounds.per_asset",
                HARD,
                f"{asset_id} weight {weight:.4f} outside "
                f"[{per_asset.min:.2f}, {per_asset.max:.2f}]",
                entity=asset_id,
                observed=weight,
                limit=per_asset.max if weight > per_asset.max else per_asset.min,
            )

    by_group: dict[str, float] = {}
    for asset_id, weight in held.items():
        by_group[known[asset_id].group] = by_group.get(known[asset_id].group, 0.0) + weight
    for group, bound in sorted(ips.universe.bounds.per_group.items()):
        weight = by_group.get(group, 0.0)
        if not bound.contains(weight):
            report.add(
                "bounds.per_group",
                HARD,
                f"{group} weight {weight:.4f} outside [{bound.min:.2f}, {bound.max:.2f}]",
                entity=group,
                observed=weight,
                limit=bound.max if weight > bound.max else bound.min,
            )


def _check_objectives(metrics: PortfolioMetrics, ips: IPS, report: ComplianceReport) -> None:
    target = ips.objectives.return_
    if metrics.expected_return_pct is None or metrics.expected_inflation_pct is None:
        report.not_evaluated.append("objectives.return")
    else:
        real = real_return_pct(metrics.expected_return_pct, metrics.expected_inflation_pct)
        if real < target.min_pct - _TOL:
            report.add(
                "objectives.return",
                target.severity,
                f"expected real return {real:.2f}% is below the CPI + {target.min_pct:.1f}% target",
                observed=real,
                limit=target.min_pct,
            )
        elif real > target.max_pct + _TOL:
            report.add(
                "objectives.return",
                target.severity,
                f"expected real return {real:.2f}% is above the CPI + "
                f"{target.max_pct:.1f}% target band",
                observed=real,
                limit=target.max_pct,
            )

    vol = ips.objectives.volatility
    if metrics.expected_volatility_pct is None:
        report.not_evaluated.append("objectives.volatility")
    elif not vol.min_pct - _TOL <= metrics.expected_volatility_pct <= vol.max_pct + _TOL:
        report.add(
            "objectives.volatility",
            vol.severity,
            f"expected volatility {metrics.expected_volatility_pct:.2f}% outside the "
            f"{vol.min_pct:.1f}-{vol.max_pct:.1f}% band",
            observed=metrics.expected_volatility_pct,
            limit=(vol.max_pct if metrics.expected_volatility_pct > vol.max_pct else vol.min_pct),
        )

    drawdown = ips.objectives.max_drawdown
    if metrics.max_drawdown_pct is None:
        report.not_evaluated.append("objectives.max_drawdown")
    elif metrics.max_drawdown_pct < drawdown.limit_pct - _TOL:
        report.add(
            "objectives.max_drawdown",
            drawdown.severity,
            f"maximum drawdown {metrics.max_drawdown_pct:.2f}% breaches the "
            f"{drawdown.limit_pct:.1f}% limit",
            observed=metrics.max_drawdown_pct,
            limit=drawdown.limit_pct,
        )


def _check_active_risk(metrics: PortfolioMetrics, ips: IPS, report: ComplianceReport) -> None:
    limit = ips.active_risk.tracking_error
    if metrics.ex_ante_tracking_error_pct is None:
        report.not_evaluated.append("active_risk.tracking_error")
    elif metrics.ex_ante_tracking_error_pct > limit.max_ex_ante_pct + _TOL:
        report.add(
            "active_risk.tracking_error",
            limit.severity,
            f"ex-ante tracking error {metrics.ex_ante_tracking_error_pct:.2f}% exceeds the "
            f"{limit.max_ex_ante_pct:.1f}% budget vs. {ips.active_risk.benchmark.name}",
            observed=metrics.ex_ante_tracking_error_pct,
            limit=limit.max_ex_ante_pct,
        )

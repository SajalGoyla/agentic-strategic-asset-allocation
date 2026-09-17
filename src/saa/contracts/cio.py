"""The CIO agent's decision and board memo (Ang et al. 2026 §3.6, §4.4).

"The CIO-agent receives the strategy review output ... and constructs the final recommended
allocation operating as a LLM-as-judge. In addition to being able to choose a given portfolio
method, it has access to several ensemble techniques."

§4.4 gives the scoring rubric explicitly: "scores each of the 21 PC methods on six
dimensions -- backtest Sharpe (25%), IPS compliance (15%), diversification (15%), regime fit
(20%), estimation robustness (15%), and CMA utilization (10%)".

§3.6 also sets out what the memo must cover, so ``BoardMemoBody`` has a field per required
section rather than one free-text blob -- a memo missing its IPS compliance statement should
fail validation, not review.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from saa.contracts.base import WEIGHT_SUM_TOL, AgentOutput, Contract, IpsCompliance

DECISION_CONTRACT = "cio_decision"
DECISION_FILENAME = "cio_decision.json"

# §4.4's six dimensions and their weights.
SCORE_WEIGHTS = {
    "backtest_sharpe": 0.25,
    "ips_compliance": 0.15,
    "diversification": 0.15,
    "regime_fit": 0.20,
    "estimation_robustness": 0.15,
    "cma_utilization": 0.10,
}


class EnsembleMethod(StrEnum):
    """§3.6's seven combination techniques, plus picking a single method outright."""

    SINGLE_METHOD = "single_method"
    SIMPLE_AVERAGE = "simple_average"
    INVERSE_TRACKING_ERROR = "inverse_tracking_error"
    BACKTEST_SHARPE_WEIGHTED = "backtest_sharpe_weighted"
    META_OPTIMIZATION = "meta_optimization"
    REGIME_CONDITIONAL = "regime_conditional"
    COMPOSITE_SCORE = "composite_score"
    TRIMMED_MEAN = "trimmed_mean"


class MethodScore(Contract):
    """One PC method scored on the six dimensions. Each score is 0-1."""

    agent_id: str
    backtest_sharpe: float = Field(ge=0.0, le=1.0)
    ips_compliance: float = Field(ge=0.0, le=1.0)
    diversification: float = Field(ge=0.0, le=1.0)
    regime_fit: float = Field(ge=0.0, le=1.0)
    estimation_robustness: float = Field(ge=0.0, le=1.0)
    cma_utilization: float = Field(ge=0.0, le=1.0)
    composite: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _composite_matches_rubric(self) -> MethodScore:
        expected = sum(getattr(self, dim) * w for dim, w in SCORE_WEIGHTS.items())
        if abs(expected - self.composite) > 1e-3:
            raise ValueError(
                f"{self.agent_id}: composite {self.composite:.4f} does not match the §4.4 "
                f"weighted rubric ({expected:.4f})"
            )
        return self


class BoardMemo(Contract):
    """§3.6: "a governance document written for non-technical stakeholders". One field per
    section the paper requires."""

    recommendation: str
    expected_performance_vs_benchmark: str
    macro_rationale: str
    largest_positions: str
    changes_since_last_review: str
    key_risks: list[str]
    rebalancing_plan: str
    ips_compliance_statement: str


class CioDecisionBody(Contract):
    ensemble_method: EnsembleMethod
    # Weight given to each PC agent's portfolio in the ensemble (Exhibit 10).
    ensemble_weights: dict[str, float]
    # The resulting allocation across the 18 asset classes (Exhibit 11).
    final_weights: dict[str, float]

    method_scores: list[MethodScore]

    expected_return_pct: float
    expected_volatility_pct: float
    sharpe_ratio: float
    effective_n: float | None = None
    ex_ante_tracking_error_pct: float | None = None

    ips_compliance: IpsCompliance
    # §3.6: the memo summarises "the recommendation, the reasoning, and the dissenting views".
    dissenting_views: list[str] = Field(default_factory=list)
    # §3.6: "what would cause the portfolio to no longer be valid".
    invalidation_conditions: list[str]
    rationale: str
    board_memo: BoardMemo

    @model_validator(mode="after")
    def _weights_and_compliance(self) -> CioDecisionBody:
        for label, weights in (
            ("ensemble_weights", self.ensemble_weights),
            ("final_weights", self.final_weights),
        ):
            total = sum(weights.values())
            if abs(total - 1.0) > WEIGHT_SUM_TOL:
                raise ValueError(f"{label} sum to {total:.6f}, expected 1.0")
            if any(w < 0 for w in weights.values()):
                raise ValueError(f"{label} contains a negative weight")

        if self.ensemble_method == EnsembleMethod.SINGLE_METHOD:
            chosen = [a for a, w in self.ensemble_weights.items() if w > 0]
            if len(chosen) != 1:
                raise ValueError(f"single_method ensemble has {len(chosen)} weighted methods")

        # §3.6: "checking IPS compliance (which is non-negotiable)". The CIO may not ship an
        # allocation that fails a hard rule.
        if not self.ips_compliance.compliant:
            raise ValueError(
                "CIO decision breaches a hard IPS rule, which §3.6 makes non-negotiable: "
                f"{[v.message for v in self.ips_compliance.violations if v.severity == 'hard']}"
            )
        return self


CioDecision = AgentOutput[CioDecisionBody]

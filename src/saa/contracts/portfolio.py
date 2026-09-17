"""Covariance and portfolio-construction contracts (Ang et al. 2026 §3.1 step 3, §3.4).

The covariance agent "estimates the asset class covariance matrix using historical data and
macro forecasts". The PC agents "take the CMAs from step (2) and the covariance matrix from
step (3) to independently construct a proposed portfolio".

Exhibit 5 organises the 20 canonical methods into four categories, plus the PC-researcher
agent that proposes a method "not spanned by the current registry" and the adversarial
diversifier, which runs last because it maximises tracking variance against the others'
centroid.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from saa.contracts.base import WEIGHT_SUM_TOL, AgentOutput, Contract, IpsCompliance

# ----------------------------------------------------------------------------- covariance
COVARIANCE_CONTRACT = "covariance"
COVARIANCE_FILENAME = "covariance.json"


class CovarianceMethod(StrEnum):
    SAMPLE = "sample"
    LEDOIT_WOLF = "ledoit_wolf"
    EXPONENTIAL = "exponential"
    REGIME_CONDITIONAL = "regime_conditional"


class CovarianceBody(Contract):
    """Annualised covariance matrix over the universe, row/column order given by ``asset_ids``."""

    asset_ids: list[str]
    method: CovarianceMethod
    window_years: float
    matrix: list[list[float]]
    volatilities_pct: dict[str, float]
    # Set when the estimate was conditioned on the macro agent's regime call.
    regime: str | None = None
    shrinkage: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _well_formed(self) -> CovarianceBody:
        n = len(self.asset_ids)
        if len(set(self.asset_ids)) != n:
            raise ValueError("duplicate asset ids in covariance matrix")
        if len(self.matrix) != n or any(len(row) != n for row in self.matrix):
            raise ValueError(f"covariance matrix is not {n}x{n}")
        for i in range(n):
            if self.matrix[i][i] <= 0:
                raise ValueError(f"non-positive variance for {self.asset_ids[i]}")
            for j in range(i + 1, n):
                a, b = self.matrix[i][j], self.matrix[j][i]
                if abs(a - b) > 1e-9 * max(1.0, abs(a)):
                    raise ValueError(
                        f"covariance matrix is not symmetric at "
                        f"({self.asset_ids[i]}, {self.asset_ids[j]})"
                    )
        missing = set(self.asset_ids) - set(self.volatilities_pct)
        if missing:
            raise ValueError(f"no volatility reported for {sorted(missing)}")
        return self


Covariance = AgentOutput[CovarianceBody]


# --------------------------------------------------------------------------- pc_proposal
PROPOSAL_CONTRACT = "pc_proposal"
PROPOSAL_FILENAME = "pc_proposal.json"


class PcCategory(StrEnum):
    """Exhibit 5's four families, plus the researcher's own slot (Exhibit 9 lists it as
    "E: PC-Researcher")."""

    HEURISTIC = "heuristic"
    RETURN_OPTIMIZED = "return_optimized"
    RISK_STRUCTURED = "risk_structured"
    NON_TRADITIONAL = "non_traditional"
    PC_RESEARCHER = "pc_researcher"


class PcProposalBody(Contract):
    """One candidate portfolio.

    ``revision_of`` is set on the second pass: §3.5 has the top-five agents revise their
    proposals after reading the peer reviews and the CRO report, and both versions are kept so
    the audit trail shows what the deliberation actually changed.
    """

    agent_id: str
    method: str
    category: PcCategory
    weights: dict[str, float]

    expected_return_pct: float
    expected_volatility_pct: float
    sharpe_ratio: float
    # Meucci (2009) effective number of assets, reported for the ensemble in §4.4.
    effective_n: float | None = None
    ex_ante_tracking_error_pct: float | None = None

    ips_compliance: IpsCompliance
    rationale: str
    revision_of: str | None = None
    # The adversarial diversifier and the researcher agent carry extra context.
    notes: str | None = None

    @model_validator(mode="after")
    def _fully_invested(self) -> PcProposalBody:
        total = sum(self.weights.values())
        if abs(total - 1.0) > WEIGHT_SUM_TOL:
            raise ValueError(f"{self.agent_id}: weights sum to {total:.6f}, expected 1.0")
        return self


PcProposal = AgentOutput[PcProposalBody]


# ------------------------------------------------------------------- researcher proposal
RESEARCH_CONTRACT = "pc_research"
RESEARCH_FILENAME = "pc_research.json"


class PcResearchBody(Contract):
    """§3.4: the PC-researcher "explores the literature on portfolio construction methods,
    identifies objectives not yet represented in the pipeline, and proposes a novel method not
    spanned by the current registry". In the March 2026 run it proposed maximum entropy.

    Kept as its own contract because the proposal is a *method*, not a portfolio: the pipeline
    may promote it into the agent registry in later runs.
    """

    method_name: str
    objective: str
    reference: str | None = None
    not_spanned_by: list[str] = Field(default_factory=list)
    implementation_notes: str
    rationale: str


PcResearch = AgentOutput[PcResearchBody]

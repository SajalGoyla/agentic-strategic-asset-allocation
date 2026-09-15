"""The PC strategy review: CRO report, peer review, votes and tally (Ang et al. 2026 §3.5).

"First, a Chief Risk Officer (CRO) agent produces a standardized risk report for each candidate
portfolio, which covers standard risk metrics like ex-ante and back-test volatility,
value-at-risk, maximum drawdown, concentration metrics, factor tilts, and IPS compliance. The
CRO-agent is a neutral assessor: it scores risk and produces commentary, but does not vote."

"Each PC agent reviews exactly two peers -- one from its own category ... and one from a
different category ... Assignments are randomized with a recorded seed."

"Voting follows a modified Borda count. Each agent submits a top-five ranking (awarding 5, 4,
3, 2, and 1 points) and a bottom flag (-2 points), excluding itself."
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from saa.contracts.base import AgentOutput, Contract, IpsCompliance
from saa.contracts.portfolio import PcCategory

# ----------------------------------------------------------------------------- cro_report
CRO_CONTRACT = "cro_report"
CRO_FILENAME = "cro_report.json"

# §3.5 "awarding 5, 4, 3, 2, and 1 points" and a bottom flag at -2.
BORDA_POINTS = (5, 4, 3, 2, 1)
BOTTOM_FLAG_POINTS = -2
TOP_N = len(BORDA_POINTS)


class CroReportBody(Contract):
    """One standardised risk report. The CRO scores and comments; it never votes."""

    portfolio_agent_id: str

    ex_ante_volatility_pct: float
    backtest_volatility_pct: float | None = None
    var_95_pct: float | None = None
    max_drawdown_pct: float | None = None
    backtest_sharpe: float | None = None
    ex_ante_tracking_error_pct: float | None = None

    # Concentration: Meucci effective N and the Herfindahl index of the weights.
    effective_n: float | None = None
    concentration_hhi: float | None = Field(default=None, ge=0.0, le=1.0)
    factor_tilts: dict[str, float] = Field(default_factory=dict)

    ips_compliance: IpsCompliance
    risk_score: float = Field(ge=0.0, le=1.0)  # higher is riskier
    commentary: str


CroReport = AgentOutput[CroReportBody]


# ---------------------------------------------------------------------------- peer_review
REVIEW_CONTRACT = "peer_review"
REVIEW_FILENAME = "peer_review.json"


class ReviewKind(StrEnum):
    """Intra-category review "is more likely to identify technical errors within a shared
    framework"; inter-category review "can challenge foundational assumptions"."""

    INTRA_CATEGORY = "intra_category"
    INTER_CATEGORY = "inter_category"


class PeerReviewBody(Contract):
    reviewer_agent_id: str
    reviewer_category: PcCategory
    reviewed_agent_id: str
    reviewed_category: PcCategory
    kind: ReviewKind

    strengths: list[str]
    weaknesses: list[str]
    technical_errors: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    rationale: str

    @model_validator(mode="after")
    def _consistent(self) -> PeerReviewBody:
        if self.reviewer_agent_id == self.reviewed_agent_id:
            raise ValueError(f"{self.reviewer_agent_id} cannot review itself")
        same = self.reviewer_category == self.reviewed_category
        expected = ReviewKind.INTRA_CATEGORY if same else ReviewKind.INTER_CATEGORY
        if self.kind != expected:
            raise ValueError(
                f"review of {self.reviewed_agent_id} by {self.reviewer_agent_id} is marked "
                f"{self.kind.value} but the categories say {expected.value}"
            )
        return self


PeerReview = AgentOutput[PeerReviewBody]


# ----------------------------------------------------------------------------------- vote
VOTE_CONTRACT = "vote"
VOTE_FILENAME = "vote.json"


class VoteBody(Contract):
    """One agent's modified-Borda ballot."""

    voter_agent_id: str
    top_five: list[str]  # ordered best first; 5, 4, 3, 2, 1 points
    bottom_flag: str | None = None  # -2 points
    rationale: str

    @model_validator(mode="after")
    def _well_formed_ballot(self) -> VoteBody:
        if len(self.top_five) != TOP_N:
            raise ValueError(f"top_five has {len(self.top_five)} entries, expected {TOP_N}")
        if len(set(self.top_five)) != TOP_N:
            raise ValueError("top_five contains duplicates")
        if self.voter_agent_id in self.top_five:
            raise ValueError(f"{self.voter_agent_id} ranked itself; ballots exclude the voter")
        if self.bottom_flag == self.voter_agent_id:
            raise ValueError(f"{self.voter_agent_id} bottom-flagged itself")
        if self.bottom_flag in self.top_five:
            raise ValueError(f"{self.bottom_flag} is both top-five and bottom-flagged")
        return self

    def points(self) -> dict[str, int]:
        tally = dict(zip(self.top_five, BORDA_POINTS, strict=True))
        if self.bottom_flag:
            tally[self.bottom_flag] = BOTTOM_FLAG_POINTS
        return tally


Vote = AgentOutput[VoteBody]


# ----------------------------------------------------------------------------- vote_tally
TALLY_CONTRACT = "vote_tally"
TALLY_FILENAME = "vote_tally.json"


class TallyRow(Contract):
    """One row of Exhibit 9."""

    agent_id: str
    method: str
    category: PcCategory
    vote_points: int
    metric_score: float = Field(ge=0.0, le=1.0)
    composite: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)


class VoteTallyBody(Contract):
    """§3.5: vote totals "blended with a quantitative metric score ... using a regime-dependent
    weight", then a diversity constraint on the shortlist.

    "A diversity constraint requires the top-five shortlist to include representation from at
    least three of the four families" -- enforced here rather than left to a prompt.
    """

    rows: list[TallyRow]
    shortlist: list[str]
    regime: str
    vote_weight: float = Field(ge=0.0, le=1.0)
    metric_weight: float = Field(ge=0.0, le=1.0)
    diversity_categories: int = Field(ge=0)

    @model_validator(mode="after")
    def _protocol(self) -> VoteTallyBody:
        if abs(self.vote_weight + self.metric_weight - 1.0) > 1e-6:
            raise ValueError("vote_weight and metric_weight must sum to 1.0")
        ranks = sorted(r.rank for r in self.rows)
        if ranks != list(range(1, len(self.rows) + 1)):
            raise ValueError("ranks must be a permutation of 1..n")
        if len(self.shortlist) != TOP_N:
            raise ValueError(f"shortlist has {len(self.shortlist)} entries, expected {TOP_N}")

        by_id = {r.agent_id: r for r in self.rows}
        unknown = [a for a in self.shortlist if a not in by_id]
        if unknown:
            raise ValueError(f"shortlist references unknown agents {unknown}")

        # The four canonical families; a PC-researcher entry does not count toward diversity.
        families = {
            by_id[a].category
            for a in self.shortlist
            if by_id[a].category != PcCategory.PC_RESEARCHER
        }
        if len(families) != self.diversity_categories:
            raise ValueError(
                f"diversity_categories says {self.diversity_categories} but the shortlist "
                f"spans {len(families)}"
            )
        if self.diversity_categories < 3:
            raise ValueError(
                f"shortlist spans {self.diversity_categories} of 4 categories; §3.5 requires "
                "at least 3"
            )
        return self


VoteTally = AgentOutput[VoteTallyBody]

"""The revision agent (Ang et al. 2026 §3.5, the last step of stage 5).

"The top five ranking PC agents then revise their proposals, taking into account the peer
reviews and the CRO report."

The shortlist comes from ``review/vote_tally.json``. Each shortlisted agent reads its proposal,
its CRO report, the two reviews it received and its vote result, and answers with levers
(``skills/portfolio_construction/revision``) rather than weights: exclude assets, cap a weight,
shrink toward equal weight, or keep the portfolio. The script applies them and nothing else
(decision 49), and files the result beside the original as ``pc_proposal-revised.json``. If the
levers would create a hard IPS breach the original did not have, the agent is shown the revised
portfolio's figures once and may keep or change them (decision 50).

``--no-llm`` keeps every portfolio unchanged and says so, so the CIO stage can read a revised
proposal for every shortlisted agent in a free run.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

from pydantic import Field, create_model, model_validator

from saa.config import Config, load_config
from saa.contracts import (
    Contract,
    CroReportBody,
    IpsCompliance,
    ModelCall,
    PcProposalBody,
    PeerReviewBody,
    Producer,
    read,
)
from saa.contracts.portfolio import PROPOSAL_CONTRACT
from saa.contracts.review import TALLY_CONTRACT, VoteTallyBody
from saa.data.store import DataStore
from saa.llm import LlmClient, tier_for
from saa.run import RunContext
from saa.skills.method_scoring import load_cro_reports, load_proposals
from saa.skills.portfolio_construction import StageInputs, gather_inputs
from saa.skills.portfolio_construction.revision import (
    MAX_SHRINK,
    RevisionLevers,
    revise,
    turnover,
)

log = logging.getLogger(__name__)

AGENT_PREFIX = "revise"
AGENT_DIR = Path(__file__).parent
SUMMARY_REPORT = "revisions.md"
DEFAULT_WORKERS = 4
MIN_RATIONALE_CHARS = 200
MIN_RESPONSE_CHARS = 40


class ReviewResponse(Contract):
    reviewer: str
    response: str


class RevisionJudgment(Contract):
    """The shortlisted agent's LLM half: levers and the case, never weights."""

    revise: bool
    exclude: list[str] = Field(default_factory=list)
    max_weight_pct: float | None = Field(default=None, ge=5.0, le=100.0)
    shrink_to_equal: float = Field(default=0.0, ge=0.0, le=MAX_SHRINK)
    response_to_reviews: list[ReviewResponse]
    rationale: str

    @model_validator(mode="after")
    def _levers_match_the_decision(self) -> RevisionJudgment:
        moved = bool(self.exclude) or self.max_weight_pct is not None or self.shrink_to_equal > 0
        if moved and not self.revise:
            raise ValueError("a lever moved but revise is false")
        if self.revise and not moved:
            raise ValueError("revise is true but no lever moved")
        return self

    def levers(self) -> RevisionLevers:
        return RevisionLevers(
            exclude=tuple(str(a) for a in self.exclude),
            max_weight=None if self.max_weight_pct is None else self.max_weight_pct / 100.0,
            shrink_to_equal=self.shrink_to_equal,
        )


def judgment_model(asset_ids: list[str], reviewers: list[str]) -> type[RevisionJudgment]:
    """``RevisionJudgment`` narrowed to this run's assets and this agent's reviewers."""
    asset = StrEnum("Asset", {a.upper(): a for a in asset_ids})
    reviewer = StrEnum("Reviewer", {r.upper(): r for r in sorted(reviewers)})
    response = create_model("ReviewResponseFor", __base__=ReviewResponse, reviewer=(reviewer, ...))
    return create_model(
        "RevisionJudgmentFor",
        __base__=RevisionJudgment,
        exclude=(list[asset], Field(default_factory=list)),
        response_to_reviews=(list[response], ...),
    )


@dataclass
class Revision:
    agent_id: str
    original: PcProposalBody
    body: PcProposalBody
    levers: RevisionLevers
    turnover: float
    call: ModelCall | None = None

    @property
    def cost_usd(self) -> float:
        return (self.call.cost_usd or 0.0) if self.call else 0.0


@dataclass
class RevisionResult:
    as_of: date
    shortlist: list[str]
    revisions: dict[str, Revision]
    skipped: dict[str, str]

    @property
    def cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.revisions.values())


def agent_slug(agent_id: str) -> str:
    return f"{AGENT_PREFIX}-{agent_id.replace('_', '-')}"


def system_prompt() -> str:
    return (AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")


def load_reviews_of(run: RunContext, agent_id: str) -> list[PeerReviewBody]:
    from saa.agents.vote import load_reviews

    return [r for r in load_reviews(run) if r.reviewed_agent_id == agent_id]


def build_prompt(
    proposal: PcProposalBody,
    report: CroReportBody | None,
    reviews: list[PeerReviewBody],
    tally: VoteTallyBody,
    *,
    asset_ids: list[str],
    ips_status: str,
) -> str:
    row = next(r for r in tally.rows if r.agent_id == proposal.agent_id)
    weights = "\n".join(
        f"| {a} | {proposal.weights.get(a, 0.0):.1%} |"
        for a in asset_ids
        if proposal.weights.get(a, 0.0) > 0.0005
    )
    hard = (
        "\n".join(
            f"- {v.rule}: {v.message}"
            for v in proposal.ips_compliance.violations
            if v.severity == "hard"
        )
        or "None."
    )
    risk = (
        "No CRO report."
        if report is None
        else (
            f"Backtest Sharpe {report.backtest_sharpe}, max drawdown {report.max_drawdown_pct}%, "
            f"risk score {report.risk_score:.2f}. CRO: {report.judgment.commentary}"
        )
    )
    blocks = []
    for r in reviews:
        errors = "; ".join(r.technical_errors) or "none"
        blocks.append(
            f"### Review by `{r.reviewer_agent_id}` ({r.kind.value.replace('_', '-')}, "
            f"score {r.score:.2f})\n- strengths: {'; '.join(r.strengths) or 'none'}\n"
            f"- weaknesses: {'; '.join(r.weaknesses)}\n- technical errors: {errors}\n"
            f"- rationale: {r.rationale}"
        )
    return f"""Revise your proposal, or explain why you will not.

You are `{proposal.agent_id}` (**{proposal.method}**, {proposal.category.value} family). You
ranked {row.rank} of {len(tally.rows)} in the vote ({row.vote_points} points, composite
{row.composite:.3f}) and are on the shortlist the CIO builds from.
Governing IPS status: {ips_status}

## Your proposal
Expected return {proposal.expected_return_pct:.2f}%, volatility
{proposal.expected_volatility_pct:.2f}%, Sharpe {proposal.sharpe_ratio:.2f}, effective assets
{proposal.effective_n if proposal.effective_n is not None else "–"}.

| asset | weight |
|---|---|
{weights}

Hard IPS breaches: {hard}

Your case: {proposal.rationale}

## The CRO's report
{risk}

## The reviews you received
{chr(10).join(blocks)}

## What to write
- `revise`, and the levers if true: `exclude` (asset ids), `max_weight_pct` (5-100),
  `shrink_to_equal` (0-{MAX_SHRINK}).
- `response_to_reviews`: one entry per reviewer above, by id.
- `rationale`: the case for the revised portfolio (or the unrevised one).
"""


def new_breaches(before: IpsCompliance, after: IpsCompliance) -> list[str]:
    """Hard IPS breaches the revision has and the original did not."""
    had = {v.rule for v in before.violations if v.severity == "hard"}
    return [v.message for v in after.violations if v.severity == "hard" and v.rule not in had]


def consequence_note(
    proposal: PcProposalBody, levers: RevisionLevers, stage: StageInputs, config: Config
) -> str | None:
    """What the levers do to the portfolio, when they create a hard IPS breach it did not have.
    Information, not a refusal: the agent may answer with the same levers."""
    revised = revise(proposal, levers, stage, config)
    new = new_breaches(proposal.ips_compliance, revised.compliance)
    if not new:
        return None
    s = revised.stats
    return (
        f"Before your revision is filed, here is what your levers ({levers.describe()}) do. "
        f"The revised portfolio has expected return {s.expected_return_pct:.2f}%, volatility "
        f"{s.expected_volatility_pct:.2f}% (was {proposal.expected_volatility_pct:.2f}%), Sharpe "
        f"{s.sharpe_ratio:.2f} and {s.effective_n:.1f} effective assets, and it newly breaches "
        f"the IPS: {'; '.join(new)}. This is shown once and is not a rule: keep the same levers "
        "and say in the rationale why the trade is worth it, or change them."
    )


def fallback_judgment(reviews: list[PeerReviewBody]) -> RevisionJudgment:
    return RevisionJudgment(
        revise=False,
        response_to_reviews=[
            ReviewResponse(
                reviewer=r.reviewer_agent_id,
                response="Not assessed: generated without a model (--no-llm).",
            )
            for r in reviews
        ],
        rationale=(
            "Revision generated without a model (--no-llm): the portfolio is unchanged. The "
            "reviews and the CRO report were not read, so no lever was moved; the revised "
            "proposal exists so the CIO stage reads a revised proposal for every shortlisted "
            "agent, as it will after a paid run."
        ),
    )


def revise_agent(
    agent_id: str,
    proposal: PcProposalBody,
    report: CroReportBody | None,
    reviews: list[PeerReviewBody],
    tally: VoteTallyBody,
    stage: StageInputs,
    config: Config,
    llm: LlmClient | None,
    *,
    ips_status: str,
    system: str,
) -> Revision:
    call = None
    if llm is None:
        judgment = fallback_judgment(reviews)
    else:
        model = judgment_model(stage.asset_ids, [r.reviewer_agent_id for r in reviews])
        shown = False

        def check(judgment) -> None:
            nonlocal shown
            answered = {str(r.reviewer) for r in judgment.response_to_reviews}
            unanswered = sorted({r.reviewer_agent_id for r in reviews} - answered)
            if unanswered:
                raise ValueError(f"{agent_id}: no response to the review by {unanswered}")
            thin = [
                str(r.reviewer)
                for r in judgment.response_to_reviews
                if len(r.response) < MIN_RESPONSE_CHARS
            ]
            if thin or len(judgment.rationale) < MIN_RATIONALE_CHARS:
                raise ValueError(
                    f"{agent_id}: revision too thin to audit (responses to {thin}, rationale "
                    f"{len(judgment.rationale)} characters)"
                )
            # §3.5 has the agent revise "taking into account ... the CRO report"; a lever can
            # create a breach the agent never sees. Shown once, then whatever it answers stands.
            if not shown:
                note = consequence_note(proposal, judgment.levers(), stage, config)
                if note:
                    shown = True
                    raise ValueError(note)

        result = llm.judge(
            model,
            system=system,
            prompt=build_prompt(
                proposal, report, reviews, tally, asset_ids=stage.asset_ids, ips_status=ips_status
            ),
            tier=tier_for("revision"),
            check=check,
        )
        judgment, call = result.value, result.call

    levers = judgment.levers()
    candidate = revise(proposal, levers, stage, config)
    moved = turnover(proposal.weights, candidate.weights)
    responses = " ".join(f"{r.reviewer}: {r.response}" for r in judgment.response_to_reviews)
    body = candidate.body(
        judgment.rationale,
        notes=(
            f"Revision: {levers.describe()}; one-way turnover {moved:.1%}. "
            f"Responses to reviews -- {responses}"
        ),
    ).model_copy(update={"revision_of": f"pc/{agent_id}/pc_proposal.json"})
    return Revision(
        agent_id=agent_id,
        original=proposal,
        body=PcProposalBody.model_validate(body.model_dump()),
        levers=levers,
        turnover=moved,
        call=call,
    )


def run_revisions(
    run: RunContext,
    store: DataStore | None,
    *,
    config: Config | None = None,
    llm: LlmClient | None = None,
    workers: int = DEFAULT_WORKERS,
    stage: StageInputs | None = None,
) -> RevisionResult:
    """Revise every shortlisted proposal; write ``pc/<agent>/pc_proposal-revised.json``."""
    config = config or load_config()
    tally_path = run.path(TALLY_CONTRACT)
    if not tally_path.exists():
        raise FileNotFoundError(
            f"{tally_path} not found; run `uv run saa-agent vote --run-id {run.run_id}` first"
        )
    tally: VoteTallyBody = read(TALLY_CONTRACT, tally_path).body
    proposals = load_proposals(run)
    reports = load_cro_reports(run)
    stage = stage or gather_inputs(run, store, config=config)
    system = system_prompt() if llm is not None else ""

    def work(agent_id: str):
        try:
            return agent_id, revise_agent(
                agent_id,
                proposals[agent_id],
                reports.get(agent_id),
                load_reviews_of(run, agent_id),
                tally,
                stage,
                config,
                llm,
                ips_status=run.ips_status,
                system=system,
            )
        except Exception as exc:
            return agent_id, exc

    revisions: dict[str, Revision] = {}
    skipped: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for agent_id, outcome in pool.map(work, tally.shortlist):
            if isinstance(outcome, Exception):
                log.error("revision of %s failed (%s)", agent_id, outcome)
                skipped[agent_id] = repr(outcome)
            else:
                revisions[agent_id] = outcome

    for agent_id, item in revisions.items():
        inputs = list(stage.inputs) + [run.input_ref(TALLY_CONTRACT, tally_path)]
        original = run.path(PROPOSAL_CONTRACT, agent_id=agent_id)
        if original.exists():
            inputs.append(run.input_ref(PROPOSAL_CONTRACT, original))
        run.write(
            PROPOSAL_CONTRACT,
            agent_slug(agent_id),
            item.body,
            produced_by=Producer.HYBRID if item.call else Producer.SCRIPT,
            agent_id=agent_id,
            revision=True,
            provenance=stage.provenance,
            inputs=inputs,
            model_calls=[item.call] if item.call else [],
        )
    log.info(
        "revision: %d revised, %d skipped, $%.4f",
        len(revisions),
        len(skipped),
        sum(r.cost_usd for r in revisions.values()),
    )
    return RevisionResult(
        as_of=run.as_of, shortlist=list(tally.shortlist), revisions=revisions, skipped=skipped
    )


def render_summary(result: RevisionResult) -> str:
    lines = [
        "# Revisions of the shortlist",
        "",
        f"As of {result.as_of}. Shortlist: {', '.join(result.shortlist)}.",
        "",
        "| agent | levers | turnover | vol % before → after | Sharpe before → after | eff. N "
        "before → after | IPS after |",
        "|---|---|---|---|---|---|---|",
    ]
    for agent_id, r in result.revisions.items():
        o, b = r.original, r.body

        def eff(x):
            return "–" if x is None else f"{x:.1f}"

        lines.append(
            f"| {agent_id} | {r.levers.describe()} | {r.turnover:.1%} | "
            f"{o.expected_volatility_pct:.2f} → {b.expected_volatility_pct:.2f} | "
            f"{o.sharpe_ratio:.2f} → {b.sharpe_ratio:.2f} | {eff(o.effective_n)} → "
            f"{eff(b.effective_n)} | {'pass' if b.ips_compliance.compliant else 'FAIL'} |"
        )
    if result.skipped:
        lines += ["", "## Failed", ""] + [f"- **{k}**: {v}" for k, v in result.skipped.items()]
    return "\n".join(lines) + "\n"


def write_summary(result: RevisionResult, run: RunContext) -> Path:
    return run.write_report(render_summary(result), SUMMARY_REPORT)

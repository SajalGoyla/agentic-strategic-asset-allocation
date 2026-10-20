"""The peer-review agent (Ang et al. 2026 §3.5, stage 5).

"Each PC agent reviews exactly two peers -- one from its own category ... and one from a
different category ... Assignments are randomized with a recorded seed, producing 42 reviews
across the 21 candidates. All reviews are released simultaneously."

The pairing comes from ``skills/peer_review`` (seeded from the run id), the prompt from its
templates, and the model writes only the assessment (``ReviewJudgment``). Who reviewed whom and
the review kind are filled in from the plan, so a review cannot rewrite the protocol. Every
review carries the seed in its header.

``--no-llm`` writes a review from the numbers instead -- the reviewed proposal's six-dimension
metric score (``skills/method_scoring``), its strongest and weakest dimensions and its IPS
breaches -- so the stage runs end to end for free and the vote has something to read.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from saa.config import Config, load_config
from saa.contracts import (
    CroReportBody,
    ModelCall,
    PcProposalBody,
    PeerReviewBody,
    Producer,
    ReviewJudgment,
    Tier,
)
from saa.contracts.cio import MethodScore
from saa.contracts.review import REVIEW_CONTRACT
from saa.data.store import DataStore
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.method_scoring import (
    load_cro_reports,
    load_proposals,
    load_scoring_settings,
    score_candidates,
)
from saa.skills.peer_review import (
    Assignment,
    AssignmentPlan,
    assign_reviews,
    render_review_prompt,
    seed_for,
    validate_plan,
)
from saa.skills.portfolio_construction import StageInputs, gather_inputs

log = logging.getLogger(__name__)

AGENT_PREFIX = "review"
AGENT_DIR = Path(__file__).parent
SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"
SUMMARY_REPORT = "peer_reviews.md"
DEFAULT_WORKERS = 4

# A review's reasoning shorter than this restates the score; it gives the vote nothing to weigh.
MIN_RATIONALE_CHARS = 200

_DIMENSION_LABEL = {
    "backtest_sharpe": "backtest Sharpe",
    "ips_compliance": "IPS compliance",
    "diversification": "diversification",
    "regime_fit": "regime fit",
    "estimation_robustness": "estimation robustness",
    "cma_utilization": "CMA utilization",
}


@dataclass
class Review:
    assignment: Assignment
    body: PeerReviewBody
    call: ModelCall | None = None

    @property
    def cost_usd(self) -> float:
        return (self.call.cost_usd or 0.0) if self.call else 0.0


@dataclass
class ReviewResult:
    as_of: date
    plan: AssignmentPlan
    reviews: dict[tuple[str, str], Review]
    skipped: dict[tuple[str, str], str]

    @property
    def cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.reviews.values())

    def received(self, agent_id: str) -> list[Review]:
        """The reviews written about one proposal, as the vote and the revision step read them."""
        return [r for (_, reviewed), r in self.reviews.items() if reviewed == agent_id]


def system_prompt() -> str:
    parts = [(AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")]
    skill = SKILLS_DIR / "peer_review" / "SKILL.md"
    if skill.exists():
        parts.append("\n\n---\n\n" + skill.read_text(encoding="utf-8"))
    return "".join(parts)


def agent_slug(reviewer: str) -> str:
    return f"{AGENT_PREFIX}-{reviewer.replace('_', '-')}"


def body_from(assignment: Assignment, judgment: ReviewJudgment) -> PeerReviewBody:
    return PeerReviewBody(
        reviewer_agent_id=assignment.reviewer,
        reviewer_category=assignment.reviewer_category,
        reviewed_agent_id=assignment.reviewed,
        reviewed_category=assignment.reviewed_category,
        kind=assignment.kind,
        strengths=judgment.strengths,
        weaknesses=judgment.weaknesses,
        technical_errors=judgment.technical_errors,
        score=judgment.score,
        rationale=judgment.rationale,
    )


def fallback_judgment(
    assignment: Assignment, proposal: PcProposalBody, score: MethodScore
) -> ReviewJudgment:
    """Used by ``--no-llm``: the reviewed proposal's metric profile, stated plainly.

    The score is the six-dimension composite, the same number the vote's metric blend and the
    CIO read, so a free run's reviews agree with the rest of the free run. Strengths and
    weaknesses are its two best and two worst dimensions, plus any hard IPS breach. Nothing
    here is a judgment, and the rationale says so.
    """
    dims = {d: getattr(score, d) for d in _DIMENSION_LABEL}
    ranked = sorted(dims, key=lambda d: (-dims[d], d))
    strengths = [f"{_DIMENSION_LABEL[d]} scores {dims[d]:.2f} of 1" for d in ranked[:2]]
    weaknesses = [f"{_DIMENSION_LABEL[d]} scores {dims[d]:.2f} of 1" for d in ranked[-2:][::-1]]
    weaknesses += [
        f"breaches {v.rule}: {v.message}"
        for v in proposal.ips_compliance.violations
        if v.severity == "hard"
    ]
    return ReviewJudgment(
        strengths=strengths,
        weaknesses=weaknesses,
        technical_errors=[],
        score=score.composite,
        rationale=(
            f"{assignment.kind.value.replace('_', '-').capitalize()} review of "
            f"{proposal.method} by {assignment.reviewer}, generated without a model (--no-llm). "
            f"The score is the proposal's six-dimension metric composite ({score.composite:.3f}),"
            " and the strengths and weaknesses are its best and worst dimensions. No judgment "
            "has been applied: neither the execution nor the premise has been assessed."
        ),
    )


def review(
    assignment: Assignment,
    proposals: dict[str, PcProposalBody],
    reports: dict[str, CroReportBody],
    stage: StageInputs,
    llm: LlmClient | None,
    *,
    scores: dict[str, MethodScore],
    ips_status: str,
    system: str,
) -> Review:
    """One review: the assignment and the reviewed proposal in, a peer review out."""
    reviewed = proposals[assignment.reviewed]
    if llm is None:
        judgment = fallback_judgment(assignment, reviewed, scores[assignment.reviewed])
        return Review(assignment=assignment, body=body_from(assignment, judgment))

    prompt = render_review_prompt(
        assignment,
        reviewed,
        asset_ids=stage.asset_ids,
        as_of=stage.as_of,
        regime=stage.regime,
        ips_status=ips_status,
        benchmark=stage.benchmark,
        cro_report=reports.get(assignment.reviewed),
        reviewer_method=proposals[assignment.reviewer].method,
    )

    def check(judgment: ReviewJudgment) -> None:
        if len(judgment.rationale) < MIN_RATIONALE_CHARS:
            raise ValueError(
                f"{assignment.reviewer} -> {assignment.reviewed}: rationale is "
                f"{len(judgment.rationale)} characters, too thin for the vote to weigh "
                f"(minimum {MIN_RATIONALE_CHARS})"
            )

    result = llm.judge(
        ReviewJudgment, system=system, prompt=prompt, tier=Tier.FLAGSHIP, check=check
    )
    judgment: ReviewJudgment = result.value
    return Review(assignment=assignment, body=body_from(assignment, judgment), call=result.call)


def run_peer_reviews(
    run: RunContext,
    store: DataStore | None,
    *,
    config: Config | None = None,
    llm: LlmClient | None = None,
    seed: int | None = None,
    workers: int = DEFAULT_WORKERS,
    stage: StageInputs | None = None,
    regime_labels: pd.Series | None = None,
) -> ReviewResult:
    """Pair every PC agent with two peers and write ``review/<reviewer>/peer_review-<x>.json``.

    The seed defaults to the one derived from the run id, so the pairing reproduces from the
    run's name. ``llm=None`` writes metric-based reviews instead of calling a model.
    """
    config = config or load_config()
    proposals = load_proposals(run)
    if not proposals:
        raise FileNotFoundError(
            f"no pc_proposal.json under {run.root / 'pc'}; run `uv run saa-agent pc` first"
        )
    reports = load_cro_reports(run)
    missing = sorted(set(proposals) - set(reports))
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} proposals have no CRO report ({', '.join(missing)}); run "
            f"`uv run saa-agent cro --run-id {run.run_id}` first -- §3.5 has the CRO report "
            "precede the reviews"
        )
    stage = stage or gather_inputs(run, store, config=config)
    categories = {agent_id: body.category for agent_id, body in proposals.items()}
    plan = assign_reviews(categories, seed=seed if seed is not None else seed_for(run.run_id))
    validate_plan(plan, categories)

    scores = {}
    if llm is None:
        scores = score_candidates(
            proposals, reports, stage, load_scoring_settings(config), labels=regime_labels
        ).scores
    system = system_prompt() if llm is not None else ""

    def work(assignment: Assignment):
        try:
            return assignment, review(
                assignment,
                proposals,
                reports,
                stage,
                llm,
                scores=scores,
                ips_status=run.ips_status,
                system=system,
            )
        except Exception as exc:
            return assignment, exc

    reviews: dict[tuple[str, str], Review] = {}
    skipped: dict[tuple[str, str], str] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for assignment, outcome in pool.map(work, plan.assignments):
            if isinstance(outcome, Exception):
                log.error("review %s -> %s failed (%s)", *assignment.pair, outcome)
                skipped[assignment.pair] = repr(outcome)
            else:
                reviews[assignment.pair] = outcome

    for (reviewer, reviewed), item in reviews.items():
        # The proposal and risk report this review read belong in the run DAG.
        inputs = list(stage.inputs)
        for contract in ("pc_proposal", "cro_report"):
            path = run.path(contract, agent_id=reviewed)
            if path.exists():
                inputs.append(run.input_ref(contract, path))
        run.write(
            REVIEW_CONTRACT,
            agent_slug(reviewer),
            item.body,
            produced_by=Producer.LLM if item.call else Producer.SCRIPT,
            agent_id=reviewer,
            reviewed=reviewed,
            provenance=stage.provenance,
            inputs=inputs,
            model_calls=[item.call] if item.call else [],
            seed=plan.seed,
        )

    log.info(
        "peer review: %d reviews, %d skipped, seed %d, $%.4f",
        len(reviews),
        len(skipped),
        plan.seed,
        sum(r.cost_usd for r in reviews.values()),
    )
    return ReviewResult(as_of=run.as_of, plan=plan, reviews=reviews, skipped=skipped)


# --------------------------------------------------------------------------------- report
def render_summary(result: ReviewResult) -> str:
    plan = result.plan
    kinds = ", ".join(
        f"{count} {kind.replace('_', '-')}" for kind, count in plan.counts_by_kind().items()
    )
    lines = [
        "# Peer Reviews",
        "",
        f"As of {result.as_of}. {len(result.reviews)} reviews, seed **{plan.seed}** ({kinds}).",
        "",
        "| reviewed | reviews | mean score | reviewers (score) | technical errors |",
        "|---|---|---|---|---|",
    ]
    for agent_id in sorted({reviewed for _, reviewed in result.reviews}):
        received = result.received(agent_id)
        mean = sum(r.body.score for r in received) / len(received)
        who = ", ".join(
            f"{r.assignment.reviewer} ({r.body.score:.2f}, {r.assignment.kind.value[:5]})"
            for r in received
        )
        errors = sum(len(r.body.technical_errors) for r in received)
        lines.append(f"| {agent_id} | {len(received)} | {mean:.2f} | {who} | {errors} |")
    if plan.fallbacks:
        lines += ["", "## Substitutions", ""]
        lines += [f"- **{k}**: {v}" for k, v in plan.fallbacks.items()]
    if result.skipped:
        lines += ["", "## Failed", ""]
        lines += [f"- **{a} -> {b}**: {why}" for (a, b), why in result.skipped.items()]
    return "\n".join(lines) + "\n"


def write_summary(result: ReviewResult, run: RunContext) -> Path:
    return run.write_report(render_summary(result), SUMMARY_REPORT)

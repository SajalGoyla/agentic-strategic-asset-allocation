"""The vote agent and the tally (Ang et al. 2026 §3.5, stage 5).

"All reviews are released simultaneously so that every agent can read every review before
voting. Voting follows a modified Borda count. Each agent submits a top-five ranking (awarding
5, 4, 3, 2, and 1 points) and a bottom flag (-2 points), excluding itself."

Every PC agent votes over the rest of the field, having read all of it. The briefing -- every
proposal, its CRO figures and its two reviews -- is identical for every voter, so it goes in the
cached system prompt and only the voter's identity varies. Each voter's output schema offers
only the candidates it may name, so a ballot that ranks itself or an unknown agent cannot be
produced. The tally (``skills/voting``) is arithmetic.

``--no-llm`` ballots rank the field by the six-dimension metric score, with a small bonus for
the voter's own family, so the whole review-and-vote cycle runs for free.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

import pandas as pd
from pydantic import Field, create_model

from saa.config import Config, load_config
from saa.contracts import (
    BallotJudgment,
    CroReportBody,
    ModelCall,
    PcProposalBody,
    PeerReviewBody,
    Producer,
    Tier,
    read,
)
from saa.contracts.cio import MethodScore
from saa.contracts.review import (
    REVIEW_CONTRACT,
    REVIEW_FILENAME,
    TALLY_CONTRACT,
    TOP_N,
    VOTE_CONTRACT,
    VoteBody,
)
from saa.data.store import DataStore
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.method_scoring import (
    load_cro_reports,
    load_proposals,
    load_scoring_settings,
    score_candidates,
)
from saa.skills.portfolio_construction import StageInputs, gather_inputs
from saa.skills.voting import Tally, VotingSettings, load_voting_settings, render_report, tally

log = logging.getLogger(__name__)

AGENT_PREFIX = "vote"
AGENT_DIR = Path(__file__).parent
SUMMARY_REPORT = "vote_tally.md"
DEFAULT_WORKERS = 4
MIN_RATIONALE_CHARS = 150
_TEXT_LIMIT = 280  # characters of each review point carried into the briefing


@dataclass
class Ballot:
    body: VoteBody
    call: ModelCall | None = None

    @property
    def cost_usd(self) -> float:
        return (self.call.cost_usd or 0.0) if self.call else 0.0


@dataclass
class VoteResult:
    as_of: date
    ballots: dict[str, Ballot]
    skipped: dict[str, str]
    tally: Tally

    @property
    def cost_usd(self) -> float:
        return sum(b.cost_usd for b in self.ballots.values())


def agent_slug(voter: str) -> str:
    return f"{AGENT_PREFIX}-{voter.replace('_', '-')}"


def load_reviews(run: RunContext) -> list[PeerReviewBody]:
    stem = Path(REVIEW_FILENAME).stem
    return [
        read(REVIEW_CONTRACT, path).body
        for path in sorted((run.root / "review").glob(f"*/{stem}-*.json"))
    ]


def ballot_model(voter: str, choices: list[str]) -> type[BallotJudgment]:
    """``BallotJudgment`` narrowed to the candidates ``voter`` may name: every other one."""
    if voter in choices:
        raise ValueError(f"{voter} cannot be offered itself")
    choice = StrEnum(f"Candidate_{voter}", {c.upper(): c for c in sorted(choices)})
    return create_model(
        f"Ballot_{voter}",
        __base__=BallotJudgment,
        top_five=(list[choice], Field(min_length=TOP_N, max_length=TOP_N)),
        bottom_flag=(choice | None, None),
    )


def _clip(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _TEXT_LIMIT else text[: _TEXT_LIMIT - 1] + "…"


def field_briefing(
    proposals: dict[str, PcProposalBody],
    reports: dict[str, CroReportBody],
    reviews: list[PeerReviewBody],
) -> str:
    """Everything every voter reads, the same for all of them (so it can be cached)."""
    lines = [
        "# The field",
        "",
        "| agent | method | family | return % | vol % | Sharpe | eff. N | TE % | backtest "
        "Sharpe | max DD % | CRO risk | IPS hard breaches |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for agent_id in sorted(proposals):
        p, r = proposals[agent_id], reports.get(agent_id)
        hard = [v.rule.split(".")[-1] for v in p.ips_compliance.violations if v.severity == "hard"]
        te = "–" if p.ex_ante_tracking_error_pct is None else f"{p.ex_ante_tracking_error_pct:.2f}"
        eff = "–" if p.effective_n is None else f"{p.effective_n:.1f}"
        bs = "–" if r is None or r.backtest_sharpe is None else f"{r.backtest_sharpe:.2f}"
        dd = "–" if r is None or r.max_drawdown_pct is None else f"{r.max_drawdown_pct:.1f}"
        risk = "–" if r is None else f"{r.risk_score:.2f}"
        lines.append(
            f"| {agent_id} | {p.method} | {p.category.value} | {p.expected_return_pct:.2f} | "
            f"{p.expected_volatility_pct:.2f} | {p.sharpe_ratio:.2f} | {eff} | {te} | {bs} | "
            f"{dd} | {risk} | {', '.join(hard) or 'none'} |"
        )
    lines += ["", "# The reviews", ""]
    by_target: dict[str, list[PeerReviewBody]] = {}
    for review in reviews:
        by_target.setdefault(review.reviewed_agent_id, []).append(review)
    for agent_id in sorted(proposals):
        lines.append(f"## {agent_id}")
        for review in sorted(by_target.get(agent_id, []), key=lambda r: r.reviewer_agent_id):
            lines.append(
                f"- **{review.reviewer_agent_id}** ({review.kind.value.replace('_', '-')}, "
                f"score {review.score:.2f})"
            )
            if review.strengths:
                lines.append(f"  - strength: {_clip(review.strengths[0])}")
            lines.append(f"  - weakness: {_clip(review.weaknesses[0])}")
            for error in review.technical_errors:
                lines.append(f"  - technical error: {_clip(error)}")
        if agent_id not in by_target:
            lines.append("- no reviews")
        lines.append("")
    return "\n".join(lines)


def system_prompt(briefing: str) -> str:
    return (AGENT_DIR / "AGENT.md").read_text(encoding="utf-8") + "\n\n---\n\n" + briefing


def build_prompt(voter: str, proposals: dict[str, PcProposalBody], *, ips_status: str) -> str:
    own = proposals[voter]
    others = [a for a in sorted(proposals) if a != voter]
    return f"""Cast your ballot.

You are `{voter}` (**{own.method}**, {own.category.value} family). The field and every review
are in your instructions above. Rank five of the other {len(others)} candidates, best first, and
optionally flag one at the bottom. You may name only: {", ".join(others)}.

Governing IPS status: {ips_status}

## What to write
- `top_five`: five candidate ids, best first (5, 4, 3, 2, 1 points).
- `bottom_flag`: one candidate id you would not want the CIO to lean on (-2 points), or null.
- `rationale`: why these five, why in this order, and why the flag -- citing the reviews.
"""


def fallback_ballot(
    voter: str,
    proposals: dict[str, PcProposalBody],
    scores: dict[str, MethodScore],
    settings: VotingSettings,
) -> BallotJudgment:
    """``--no-llm``: rank the others by metric score, nudged toward the voter's own family."""
    family = proposals[voter].category
    others = [a for a in proposals if a != voter]
    adjusted = {
        a: scores[a].composite
        + (settings.own_family_bonus if proposals[a].category == family else 0.0)
        for a in others
    }
    ranked = sorted(others, key=lambda a: (-adjusted[a], a))
    return BallotJudgment(
        top_five=ranked[:TOP_N],
        bottom_flag=ranked[-1] if len(ranked) > TOP_N else None,
        rationale=(
            f"Ballot for {voter} generated without a model (--no-llm): the other candidates "
            "ranked by their six-dimension metric score, with a "
            f"{settings.own_family_bonus:.2f} bonus for the {family.value} family, and the "
            "lowest flagged. No judgment has been applied and the reviews were not read."
        ),
    )


def cast(
    voter: str,
    proposals: dict[str, PcProposalBody],
    llm: LlmClient | None,
    *,
    scores: dict[str, MethodScore],
    settings: VotingSettings,
    system: str,
    ips_status: str,
) -> Ballot:
    if llm is None:
        judgment = fallback_ballot(voter, proposals, scores, settings)
        call = None
    else:
        model = ballot_model(voter, [a for a in proposals if a != voter])
        result = llm.judge(
            model,
            system=system,
            prompt=build_prompt(voter, proposals, ips_status=ips_status),
            tier=Tier.FLAGSHIP,
        )
        judgment, call = result.value, result.call
        if len(judgment.rationale) < MIN_RATIONALE_CHARS:
            raise ValueError(
                f"{voter}: ballot rationale is {len(judgment.rationale)} characters, too thin "
                f"to explain a ranking (minimum {MIN_RATIONALE_CHARS})"
            )
    body = VoteBody(
        voter_agent_id=voter,
        top_five=[str(a) for a in judgment.top_five],
        bottom_flag=None if judgment.bottom_flag is None else str(judgment.bottom_flag),
        rationale=judgment.rationale,
    )
    return Ballot(body=body, call=call)


def run_vote(
    run: RunContext,
    store: DataStore | None,
    *,
    config: Config | None = None,
    llm: LlmClient | None = None,
    workers: int = DEFAULT_WORKERS,
    stage: StageInputs | None = None,
    regime_labels: pd.Series | None = None,
) -> VoteResult:
    """Every PC agent votes; write ``review/<voter>/vote.json`` and ``review/vote_tally.json``."""
    config = config or load_config()
    proposals = load_proposals(run)
    if not proposals:
        raise FileNotFoundError(
            f"no pc_proposal.json under {run.root / 'pc'}; run `uv run saa-agent pc` first"
        )
    reports = load_cro_reports(run)
    reviews = load_reviews(run)
    unreviewed = sorted(set(proposals) - {r.reviewed_agent_id for r in reviews})
    if unreviewed:
        raise FileNotFoundError(
            f"{len(unreviewed)} proposals have no peer review ({', '.join(unreviewed)}); run "
            f"`uv run saa-agent peer-review --run-id {run.run_id}` first -- §3.5 has every "
            "agent read every review before voting"
        )
    stage = stage or gather_inputs(run, store, config=config)
    scoring = score_candidates(
        proposals, reports, stage, load_scoring_settings(config), labels=regime_labels
    )
    settings = load_voting_settings(config)
    system = system_prompt(field_briefing(proposals, reports, reviews)) if llm else ""

    def work(voter: str):
        try:
            return voter, cast(
                voter,
                proposals,
                llm,
                scores=scoring.scores,
                settings=settings,
                system=system,
                ips_status=run.ips_status,
            )
        except Exception as exc:
            return voter, exc

    ballots: dict[str, Ballot] = {}
    skipped: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for voter, outcome in pool.map(work, sorted(proposals)):
            if isinstance(outcome, Exception):
                log.error("ballot for %s failed (%s)", voter, outcome)
                skipped[voter] = repr(outcome)
            else:
                ballots[voter] = outcome

    result = tally(
        [b.body for b in ballots.values()],
        proposals,
        scoring.scores,
        settings,
        regime=scoring.regime,
    )
    for voter, ballot in ballots.items():
        run.write(
            VOTE_CONTRACT,
            agent_slug(voter),
            ballot.body,
            produced_by=Producer.LLM if ballot.call else Producer.SCRIPT,
            agent_id=voter,
            provenance=stage.provenance,
            inputs=stage.inputs,
            model_calls=[ballot.call] if ballot.call else [],
        )
    run.write(
        TALLY_CONTRACT,
        "vote-tally",
        result.body,
        produced_by=Producer.SCRIPT,
        provenance=stage.provenance,
        inputs=[run.input_ref(VOTE_CONTRACT, run.path(VOTE_CONTRACT, agent_id=v)) for v in ballots],
    )
    log.info(
        "vote: %d ballots, %d skipped, shortlist %s, $%.4f",
        len(ballots),
        len(skipped),
        result.body.shortlist,
        sum(b.cost_usd for b in ballots.values()),
    )
    return VoteResult(as_of=run.as_of, ballots=ballots, skipped=skipped, tally=result)


def render_summary(result: VoteResult) -> str:
    text = render_report(result.tally)
    if result.skipped:
        text += "\n## Ballots that failed\n\n" + "".join(
            f"- **{k}**: {v}\n" for k, v in result.skipped.items()
        )
    return text


def write_summary(result: VoteResult, run: RunContext) -> Path:
    return run.write_report(render_summary(result), SUMMARY_REPORT)

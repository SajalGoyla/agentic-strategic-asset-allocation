"""Portfolio-construction agents (Ang et al. 2026 §3.1 step 4, §3.4, Exhibit 5).

One agent per method. The optimiser runs first and the weights are fixed before the model sees
them; the agent writes the case for them, which is what the peer review in §3.5 will argue
over.

The roster runs in the paper's order (§3.4): the registry's methods in parallel -- heuristic,
return-optimized, risk-structured, non-traditional -- then the PC-researcher, whose proposed
method is run and reviewed like any other, and last the adversarial diversifier, which "executes
after the initial 19 have finished" because it moves away from the centroid of all of them.

``--no-llm`` produces every portfolio and every statistic without a model, which is how the
weights get checked without spending anything.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from saa.config import Config, load_config
from saa.contracts import Contract, ModelCall, PcProposalBody, Producer, Tier
from saa.contracts.portfolio import PROPOSAL_CONTRACT, RESEARCH_CONTRACT
from saa.data.store import DataStore
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.portfolio_construction import (
    ADVERSARIAL,
    Candidate,
    StageInputs,
    adversarial_diversifier,
    build_candidate,
    build_candidates,
    equal_weight,
    gather_inputs,
)
from saa.skills.portfolio_construction.methods import METHODS, PortfolioInputs

log = logging.getLogger(__name__)

AGENT_PREFIX = "pc"
AGENT_DIR = Path(__file__).parent
SKILL_PATH = (
    Path(__file__).resolve().parents[3] / "saa" / "skills" / "portfolio_construction" / "SKILL.md"
)
SUMMARY_REPORT = "pc_proposals.md"
DEFAULT_WORKERS = 4

# A rationale this short is not an argument; the peer review would have nothing to engage with.
MIN_RATIONALE_CHARS = 200
# The adversarial diversifier needs a centroid worth moving away from.
MIN_PROPOSALS_FOR_ADVERSARIAL = 2
RESEARCHER_ID = "pc_researcher"
ROSTER = [*METHODS, RESEARCHER_ID, ADVERSARIAL.id]


@dataclass
class Proposal:
    candidate: Candidate
    body: PcProposalBody
    call: ModelCall | None = None

    @property
    def agent_id(self) -> str:
        return self.candidate.agent_id

    @property
    def cost_usd(self) -> float:
        return (self.call.cost_usd or 0.0) if self.call else 0.0


@dataclass
class PcResult:
    as_of: date
    proposals: dict[str, Proposal]
    skipped: dict[str, str]
    stage: StageInputs
    research: object | None = None  # pc_researcher.ResearchOutcome, when the researcher ran

    @property
    def cost_usd(self) -> float:
        return sum(p.cost_usd for p in self.proposals.values())


class Rationale(Contract):
    """The LLM's only output here. The weights are already fixed."""

    rationale: str
    key_assumption: str
    main_weakness: str
    when_preferred: str
    invalidation: str


def system_prompt() -> str:
    parts = [(AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")]
    if SKILL_PATH.exists():
        parts.append("\n\n---\n\n" + SKILL_PATH.read_text(encoding="utf-8"))
    return "".join(parts)


def _weights_table(candidate: Candidate, stage: StageInputs) -> str:
    equal = equal_weight(PortfolioInputs(asset_ids=stage.asset_ids, covariance=stage.covariance))
    lines = ["| asset | weight | vs equal weight | vs benchmark |", "|---|---|---|---|"]
    for asset_id in stage.asset_ids:
        w = candidate.weights.get(asset_id, 0.0)
        if w <= 0.0005:
            continue
        lines.append(
            f"| {asset_id} | {w:.1%} | {w - equal[asset_id]:+.1%} | "
            f"{w - stage.benchmark.get(asset_id, 0.0):+.1%} |"
        )
    held = int((candidate.weights > 0.0005).sum())
    lines.append(f"\n{held} of {len(stage.asset_ids)} assets held.")
    return "\n".join(lines)


def build_prompt(candidate: Candidate, stage: StageInputs, *, ips_status: str) -> str:
    stats = candidate.stats
    compliance = candidate.compliance
    violations = (
        "\n".join(f"- [{v.severity}] {v.rule}: {v.message}" for v in compliance.violations)
        or "None."
    )
    te = "not computed" if stats.tracking_error_pct is None else f"{stats.tracking_error_pct:.2f}%"
    cma_note = (
        "This method uses the judged CMAs, so it inherits their estimation error."
        if candidate.method.uses_cmas
        else "This method ignores expected returns entirely and uses only the covariance "
        "structure (or not even that)."
    )
    if candidate.method.needs_scenarios:
        cma_note += (
            " It optimises over the historical monthly return scenarios, so the tails it sees "
            "are the ones 1993 onward happened to contain."
        )
    if candidate.method.prompt_note:
        cma_note += "\n\n" + candidate.method.prompt_note

    return f"""Make the case for the portfolio your method produced.

Method: **{candidate.method.name}** ({candidate.method.category}, {candidate.method.reference})
As-of date: {stage.as_of}
Macro regime: {stage.regime or "unknown"}
Governing IPS status: {ips_status}

{cma_note}

## Ex-ante statistics
| metric | value |
|---|---|
| expected return | {stats.expected_return_pct:.2f}% |
| volatility | {stats.expected_volatility_pct:.2f}% |
| Sharpe ratio | {stats.sharpe_ratio:.2f} |
| effective number of assets | {stats.effective_n:.1f} of {len(stage.asset_ids)} |
| tracking error vs. the IPS benchmark | {te} |
| concentration (Herfindahl) | {stats.concentration_hhi:.3f} |

## Weights
{_weights_table(candidate, stage)}

## IPS compliance
Compliant: **{compliance.compliant}**
{violations}

## What to write

- `rationale`: the case for this portfolio, for a reader who will also read four or five
  competing proposals and then vote. A few paragraphs.
- `key_assumption`: the one assumption this method rests on, stated plainly.
- `main_weakness`: a concrete weakness — not a hedge. A reviewer will find it anyway.
- `when_preferred`: the conditions under which this method should beat the alternatives.
- `invalidation`: what would have to be true for this portfolio to be the wrong choice.

Do not restate the weights as prose, and do not claim the method is unconditionally best.
"""


def _fallback_rationale(candidate: Candidate, stage: StageInputs) -> str:
    """Used by ``--no-llm``. Deterministic, and honest about being generated without a model."""
    s = candidate.stats
    return (
        f"{candidate.method.name} ({candidate.method.reference}) over {len(stage.asset_ids)} "
        f"asset classes as of {stage.as_of}. Ex-ante expected return {s.expected_return_pct:.2f}%, "
        f"volatility {s.expected_volatility_pct:.2f}%, Sharpe {s.sharpe_ratio:.2f}, effective "
        f"number of assets {s.effective_n:.1f}. "
        + (
            "The method consumes the judged CMAs and inherits their estimation error. "
            if candidate.method.uses_cmas
            else "The method uses no return forecasts, so CMA error does not reach it. "
        )
        + "Generated without a model (--no-llm): no judgment has been applied to this portfolio."
    )


def propose(
    candidate: Candidate,
    stage: StageInputs,
    llm: LlmClient | None,
    *,
    ips_status: str,
    system: str,
) -> Proposal:
    """One method: optimiser output in, argued proposal out."""
    if llm is None:
        return Proposal(
            candidate=candidate, body=candidate.body(_fallback_rationale(candidate, stage))
        )

    result = llm.judge(
        Rationale,
        system=system,
        prompt=build_prompt(candidate, stage, ips_status=ips_status),
        tier=Tier.LOW_COST,
    )
    answer: Rationale = result.value
    if len(answer.rationale) < MIN_RATIONALE_CHARS:
        raise ValueError(
            f"{candidate.agent_id}: rationale is {len(answer.rationale)} characters, too thin "
            f"for peer review (minimum {MIN_RATIONALE_CHARS})"
        )
    notes = (
        f"Key assumption: {answer.key_assumption} "
        f"Main weakness: {answer.main_weakness} "
        f"Preferred when: {answer.when_preferred} "
        f"Invalidated if: {answer.invalidation}"
    )
    return Proposal(
        candidate=candidate,
        body=candidate.body(answer.rationale, notes=notes),
        call=result.call,
    )


def agent_slug(agent_id: str) -> str:
    """Header slug: "pc-max-sharpe"; the researcher is already "pc-researcher"."""
    slug = agent_id.replace("_", "-")
    return slug if slug.startswith(f"{AGENT_PREFIX}-") else f"{AGENT_PREFIX}-{slug}"


def centroid(candidates: list[Candidate], asset_ids: list[str]) -> pd.Series:
    """§3.4: "the mean of all other PC weights"."""
    return (
        pd.DataFrame([c.weights.reindex(asset_ids).fillna(0.0) for c in candidates])
        .mean()
        .reindex(asset_ids)
    )


def run_pc_agents(
    run: RunContext,
    store: DataStore,
    *,
    config: Config | None = None,
    llm: LlmClient | None = None,
    methods: list[str] | None = None,
    workers: int = DEFAULT_WORKERS,
) -> PcResult:
    """Run the roster and write ``pc/<agent_id>/pc_proposal.json`` for each agent.

    ``methods`` defaults to the whole roster (``ROSTER``): the registry methods, then
    ``pc_researcher`` and ``adversarial_diversifier``. ``llm=None`` writes deterministic
    rationales instead of calling a model, so the weights can be checked for free.
    """
    from saa.agents.pc_researcher import research as run_research

    config = config or load_config()
    requested = list(methods or ROSTER)
    unknown = sorted(set(requested) - set(ROSTER))
    stage = gather_inputs(run, store, config=config)
    candidates, skipped = build_candidates(
        stage, config, method_ids=[m for m in requested if m in METHODS]
    )
    for method_id in unknown:
        skipped[method_id] = f"unknown agent; known: {ROSTER}"
    system = system_prompt() if llm is not None else ""

    proposals: dict[str, Proposal] = {}

    def work(method_id: str):
        try:
            return method_id, propose(
                candidates[method_id], stage, llm, ips_status=run.ips_status, system=system
            )
        except Exception as exc:
            return method_id, exc

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for method_id, outcome in pool.map(work, list(candidates)):
            if isinstance(outcome, Exception):
                log.error("pc agent %s failed (%s)", method_id, outcome)
                skipped[method_id] = repr(outcome)
            else:
                proposals[method_id] = outcome

    # The researcher reads what the registry produced, so it runs after it.
    research_outcome = None
    if RESEARCHER_ID in requested:
        try:
            research_outcome = run_research(
                stage, config, candidates, llm, ips_status=run.ips_status
            )
        except Exception as exc:
            log.error("pc researcher failed (%s)", exc)
            skipped[RESEARCHER_ID] = repr(exc)
        else:
            candidates[RESEARCHER_ID] = research_outcome.candidate
            proposals[RESEARCHER_ID] = Proposal(
                candidate=research_outcome.candidate,
                body=research_outcome.proposal,
                call=research_outcome.call,
            )

    # Last, the adversarial diversifier, against every portfolio above.
    if ADVERSARIAL.id in requested:
        others = list(candidates.values())
        if len(others) < MIN_PROPOSALS_FOR_ADVERSARIAL:
            skipped[ADVERSARIAL.id] = (
                f"needs at least {MIN_PROPOSALS_FOR_ADVERSARIAL} other portfolios to move away "
                f"from; {len(others)} ran"
            )
        else:
            center = centroid(others, stage.asset_ids)
            try:
                candidate = build_candidate(
                    ADVERSARIAL,
                    stage,
                    config,
                    build=lambda inputs: adversarial_diversifier(inputs, center),
                )
                proposal = propose(candidate, stage, llm, ips_status=run.ips_status, system=system)
            except Exception as exc:
                log.error("adversarial diversifier failed (%s)", exc)
                skipped[ADVERSARIAL.id] = repr(exc)
            else:
                sigma = stage.covariance.loc[stage.asset_ids, stage.asset_ids].to_numpy()
                active = (candidate.weights - center).to_numpy()
                distance = 100 * float(active @ sigma @ active) ** 0.5
                proposal.body.notes = (
                    f"Tracking error to the centroid of the other {len(others)} proposals: "
                    f"{distance:.2f}%. " + (proposal.body.notes or "")
                ).strip()
                candidates[ADVERSARIAL.id] = candidate
                proposals[ADVERSARIAL.id] = proposal

    if research_outcome is not None:
        run.write(
            RESEARCH_CONTRACT,
            "pc-researcher",
            research_outcome.research,
            produced_by=Producer.LLM if research_outcome.call else Producer.SCRIPT,
            provenance=stage.provenance,
            inputs=stage.inputs,
            model_calls=[research_outcome.call] if research_outcome.call else [],
        )

    for method_id, proposal in proposals.items():
        run.write(
            PROPOSAL_CONTRACT,
            agent_slug(method_id),
            proposal.body,
            produced_by=Producer.HYBRID if proposal.call else Producer.SCRIPT,
            agent_id=method_id,
            provenance=stage.provenance,
            inputs=stage.inputs,
            model_calls=[proposal.call] if proposal.call else [],
        )

    log.info(
        "pc agents: %d proposals, %d skipped, $%.4f",
        len(proposals),
        len(skipped),
        sum(p.cost_usd for p in proposals.values()),
    )
    return PcResult(
        as_of=run.as_of,
        proposals=proposals,
        skipped=skipped,
        stage=stage,
        research=research_outcome,
    )


def render_summary(result: PcResult) -> str:
    stage = result.stage
    lines = [
        "# Portfolio Construction Proposals",
        "",
        f"As of {result.as_of}" + (f", regime **{stage.regime}**" if stage.regime else ""),
        "",
        "| agent | category | return % | vol % | Sharpe | eff. N | TE % | IPS |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for agent_id, proposal in result.proposals.items():
        b = proposal.body
        te = "–" if b.ex_ante_tracking_error_pct is None else f"{b.ex_ante_tracking_error_pct:.2f}"
        ips = "pass" if b.ips_compliance.compliant else "FAIL"
        lines.append(
            f"| {agent_id} | {b.category.value} | {b.expected_return_pct:.2f} | "
            f"{b.expected_volatility_pct:.2f} | {b.sharpe_ratio:.2f} | "
            f"{b.effective_n:.1f} | {te} | {ips} |"
        )
    if result.skipped:
        lines += ["", "## Skipped", ""]
        lines += [f"- **{k}**: {v}" for k, v in result.skipped.items()]

    lines += ["", "## Weights", "", "| asset | " + " | ".join(result.proposals) + " |"]
    lines.append("|---" * (len(result.proposals) + 1) + "|")
    for asset_id in stage.asset_ids:
        cells = [f"{p.body.weights.get(asset_id, 0.0):.1%}" for p in result.proposals.values()]
        lines.append(f"| {asset_id} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_summary(result: PcResult, run: RunContext) -> Path:
    return run.write_report(render_summary(result), SUMMARY_REPORT)


def weights_frame(result: PcResult) -> pd.DataFrame:
    """Agent x asset weights, for the review stage and the CIO ensemble."""
    return (
        pd.DataFrame({agent_id: p.body.weights for agent_id, p in result.proposals.items()})
        .fillna(0.0)
        .T
    )

"""PC-researcher agent (Ang et al. 2026 §3.4, Exhibit 5 "Researcher").

§3.4: the researcher "explores the literature on portfolio construction methods, identifies
objectives not yet represented in the pipeline, and proposes a novel method not spanned by the
current registry". In the paper's March 2026 run it proposed maximum entropy.

A proposal the pipeline cannot run is not one it can review, so the choice is constrained to
``RESEARCH_LIBRARY``: methods implemented in advance but absent from the registry. The judgment
is which gap in the registry matters now, and the case for filling it. The agent writes two
files: ``pc/pc_research.json`` (the method, as a candidate for the registry) and
``pc/pc_researcher/pc_proposal.json`` (its portfolio, which enters the review like any other).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import Field

from saa.config import Config
from saa.contracts import Contract, ModelCall, PcProposalBody, Tier
from saa.contracts.portfolio import PcResearchBody
from saa.llm import LlmClient
from saa.skills.portfolio_construction import (
    METHODS,
    RESEARCH_LIBRARY,
    Candidate,
    StageInputs,
    build_candidate,
)

log = logging.getLogger(__name__)

AGENT = "pc-researcher"
AGENT_ID = "pc_researcher"
AGENT_DIR = Path(__file__).parent
# What the researcher proposes without a model: the paper's own March 2026 choice.
DEFAULT_METHOD = "maximum_entropy"
MIN_RATIONALE_CHARS = 200

ResearchMethodId = StrEnum(
    "ResearchMethodId", {method_id.upper(): method_id for method_id in RESEARCH_LIBRARY}
)


class ResearchChoice(Contract):
    """The LLM's output: which unrepresented method to add, and the case for it."""

    method_id: ResearchMethodId  # type: ignore[valid-type]
    objective: str
    not_spanned_by: list[str] = Field(
        description="registry method ids whose objectives this method does not reduce to"
    )
    gap: str = Field(description="what the current registry cannot express")
    implementation_notes: str
    rationale: str
    main_weakness: str


@dataclass
class ResearchOutcome:
    research: PcResearchBody
    candidate: Candidate
    proposal: PcProposalBody
    call: ModelCall | None = None

    @property
    def cost_usd(self) -> float:
        return (self.call.cost_usd or 0.0) if self.call else 0.0


def system_prompt() -> str:
    return (AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")


def library_options(registry: dict) -> dict:
    """Library methods the registry does not already contain."""
    return {k: m for k, m in RESEARCH_LIBRARY.items() if k not in registry}


def build_prompt(
    stage: StageInputs,
    registry_candidates: dict[str, Candidate],
    options: dict,
    *,
    ips_status: str,
) -> str:
    rows = [
        "| method | family | uses CMAs | vol % | Sharpe | eff. N | IPS |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in registry_candidates.values():
        s = c.stats
        rows.append(
            f"| {c.method.id} ({c.method.reference}) | {c.method.category} | "
            f"{'yes' if c.method.uses_cmas else 'no'} | {s.expected_volatility_pct:.2f} | "
            f"{s.sharpe_ratio:.2f} | {s.effective_n:.1f} | "
            f"{'pass' if c.compliance.compliant else 'FAIL'} |"
        )
    library = [
        f"- `{m.id}`: {m.name} ({m.reference}). "
        + (m.build.__doc__ or "").strip().split("\n\n")[0].replace("\n", " ")
        for m in options.values()
    ]
    return f"""Propose the portfolio-construction method the registry is missing.

As-of date: {stage.as_of}
Macro regime: {stage.regime or "unknown"}
Governing IPS status: {ips_status}

## The registry today, and what each method produced this run
{chr(10).join(rows)}

## Methods you may propose
These are implemented, so whichever you choose will be run and its portfolio reviewed with the
others. Choose exactly one.
{chr(10).join(library)}

## What to write
- `method_id`: your choice.
- `objective`: the objective it optimises, in one or two sentences.
- `not_spanned_by`: the registry methods whose objectives it does not reduce to.
- `gap`: what the registry cannot express today that this method can — read the table above,
  not just the method names.
- `implementation_notes`: inputs, constraints, and anything the reviewers should check.
- `rationale`: the case for adding it now, for reviewers who will vote on its portfolio.
- `main_weakness`: a concrete weakness.
"""


def _fallback(method_id: str, registry: dict) -> ResearchChoice:
    method = RESEARCH_LIBRARY[method_id]
    return ResearchChoice(
        method_id=ResearchMethodId(method_id),
        objective=(method.build.__doc__ or method.name).strip().split("\n\n")[0],
        not_spanned_by=sorted(registry),
        gap="Not assessed: generated without a model (--no-llm).",
        implementation_notes=f"{method.name}, as implemented in "
        "saa.skills.portfolio_construction.methods.",
        rationale=(
            f"{method.name} ({method.reference}) is the paper's own PC-researcher proposal in its "
            "March 2026 run, and is used here as the default without a model. Generated without "
            "a model (--no-llm): no judgment has been applied to which gap in the registry "
            "matters most for this run."
        ),
        main_weakness="Not assessed without a model.",
    )


def research(
    stage: StageInputs,
    config: Config,
    registry_candidates: dict[str, Candidate],
    llm: LlmClient | None,
    *,
    ips_status: str,
) -> ResearchOutcome:
    """Choose a library method the registry lacks, run it, and write the case for it."""
    options = library_options(METHODS)
    if not options:
        raise ValueError("every library method is already in the registry; nothing to propose")

    call = None
    if llm is None:
        choice = _fallback(
            DEFAULT_METHOD if DEFAULT_METHOD in options else next(iter(options)), METHODS
        )
    else:
        result = llm.judge(
            ResearchChoice,
            system=system_prompt(),
            prompt=build_prompt(stage, registry_candidates, options, ips_status=ips_status),
            tier=Tier.FLAGSHIP,
        )
        choice, call = result.value, result.call
        if len(choice.rationale) < MIN_RATIONALE_CHARS:
            raise ValueError(
                f"pc_researcher: rationale is {len(choice.rationale)} characters, too thin for "
                f"peer review (minimum {MIN_RATIONALE_CHARS})"
            )
    method = options[choice.method_id.value]
    unknown = sorted(set(choice.not_spanned_by) - set(METHODS))
    if unknown:
        log.warning("pc_researcher named methods not in the registry: %s", unknown)

    candidate = build_candidate(method, stage, config, agent=AGENT_ID)
    research_body = PcResearchBody(
        method_name=method.name,
        objective=choice.objective,
        reference=method.reference,
        not_spanned_by=[m for m in choice.not_spanned_by if m in METHODS],
        implementation_notes=choice.implementation_notes,
        rationale=choice.rationale,
    )
    proposal = candidate.body(
        choice.rationale,
        notes=(
            f"Proposed method: {method.id} ({method.reference}). Objective: {choice.objective} "
            f"Gap in the registry: {choice.gap} Main weakness: {choice.main_weakness}"
        ),
    )
    return ResearchOutcome(
        research=research_body, candidate=candidate, proposal=proposal, call=call
    )

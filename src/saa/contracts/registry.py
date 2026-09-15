"""The contract registry, and the read/write helpers agents use.

Every contract is registered once here with the filename the paper gives it, the body model,
the judgment model the LLM is constrained to (where there is one), and which pipeline stage
produces it. Everything else -- JSON Schema export, run-directory layout, validation on read --
is derived from this table, so adding a contract means adding one ``Spec``.

Run directory layout::

    runs/<pipeline_run_id>/
      macro/macro-view.json
      cma/<asset_id>/cma_methods.json, cma.json, signals.json, ...
      pc/<agent_id>/pc_proposal.json
      review/<agent_id>/cro_report.json, peer_review-<reviewed>.json, vote.json
      review/vote_tally.json
      cio/cio_decision.json
      reports/*.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from saa.contracts import asset_class as ac
from saa.contracts import cio, macro, portfolio, review
from saa.contracts.base import AgentOutput, Contract, Producer


@dataclass(frozen=True)
class Spec:
    name: str
    filename: str
    body: type[Contract]
    stage: str
    produced_by: Producer
    description: str
    # The model the LLM is constrained to via `messages.parse(output_format=...)`. None for
    # contracts a script writes end to end.
    judgment: type[Contract] | None = None

    @property
    def output_model(self) -> type[BaseModel]:
        """The full file model: header + body."""
        return AgentOutput[self.body]  # type: ignore[name-defined]


_SPECS = [
    Spec(
        name=macro.CONTRACT,
        filename=macro.FILENAME,
        body=macro.MacroViewBody,
        judgment=macro.MacroJudgment,
        stage="macro",
        produced_by=Producer.HYBRID,
        description="Macro regime classification consumed by every downstream agent (§3.2)",
    ),
    Spec(
        name=ac.STATS_CONTRACT,
        filename=ac.STATS_FILENAME,
        body=ac.HistoricalStatsBody,
        stage="cma",
        produced_by=Producer.SCRIPT,
        description="Trailing returns, volatility, drawdowns, and statistics by regime",
    ),
    Spec(
        name=ac.CORRELATION_CONTRACT,
        filename=ac.CORRELATION_FILENAME,
        body=ac.CorrelationRowBody,
        stage="cma",
        produced_by=Producer.SCRIPT,
        description="One asset's correlation row against the rest of the universe",
    ),
    Spec(
        name=ac.SIGNALS_CONTRACT,
        filename=ac.SIGNALS_FILENAME,
        body=ac.SignalsBody,
        stage="cma",
        produced_by=Producer.SCRIPT,
        description="Asset-level macro, technical and valuation signals read by the CMA judge",
    ),
    Spec(
        name=ac.METHODS_CONTRACT,
        filename=ac.METHODS_FILENAME,
        body=ac.CmaMethodsBody,
        stage="cma",
        produced_by=Producer.SCRIPT,
        description="The seven CMA candidates; §3.3 states no LLM judgment is involved here",
    ),
    Spec(
        name=ac.CMA_CONTRACT,
        filename=ac.CMA_FILENAME,
        body=ac.CmaBody,
        judgment=ac.CmaJudgment,
        stage="cma",
        produced_by=Producer.HYBRID,
        description="The CMA judge's final expected return, bounded by the candidate range",
    ),
    Spec(
        name=ac.SCENARIOS_CONTRACT,
        filename=ac.SCENARIOS_FILENAME,
        body=ac.ScenariosBody,
        stage="cma",
        produced_by=Producer.HYBRID,
        description="Bull/base/bear scenarios derived from the method range",
    ),
    Spec(
        name=portfolio.COVARIANCE_CONTRACT,
        filename=portfolio.COVARIANCE_FILENAME,
        body=portfolio.CovarianceBody,
        stage="pc",
        produced_by=Producer.SCRIPT,
        description="Asset-class covariance matrix (§3.1 step 3)",
    ),
    Spec(
        name=portfolio.PROPOSAL_CONTRACT,
        filename=portfolio.PROPOSAL_FILENAME,
        body=portfolio.PcProposalBody,
        stage="pc",
        produced_by=Producer.HYBRID,
        description="One PC agent's candidate portfolio and its rationale",
    ),
    Spec(
        name=portfolio.RESEARCH_CONTRACT,
        filename=portfolio.RESEARCH_FILENAME,
        body=portfolio.PcResearchBody,
        judgment=portfolio.PcResearchBody,
        stage="pc",
        produced_by=Producer.LLM,
        description="A new PC method proposed by the researcher agent (§3.4)",
    ),
    Spec(
        name=review.CRO_CONTRACT,
        filename=review.CRO_FILENAME,
        body=review.CroReportBody,
        judgment=review.CroReportBody,
        stage="review",
        produced_by=Producer.HYBRID,
        description="Standardised risk report per candidate; the CRO scores but never votes",
    ),
    Spec(
        name=review.REVIEW_CONTRACT,
        filename=review.REVIEW_FILENAME,
        body=review.PeerReviewBody,
        judgment=review.PeerReviewBody,
        stage="review",
        produced_by=Producer.LLM,
        description="One intra- or inter-category peer review (§3.5)",
    ),
    Spec(
        name=review.VOTE_CONTRACT,
        filename=review.VOTE_FILENAME,
        body=review.VoteBody,
        judgment=review.VoteBody,
        stage="review",
        produced_by=Producer.LLM,
        description="One agent's modified-Borda ballot",
    ),
    Spec(
        name=review.TALLY_CONTRACT,
        filename=review.TALLY_FILENAME,
        body=review.VoteTallyBody,
        stage="review",
        produced_by=Producer.SCRIPT,
        description="Blended vote and metric ranking, with the diversity constraint enforced",
    ),
    Spec(
        name=cio.DECISION_CONTRACT,
        filename=cio.DECISION_FILENAME,
        body=cio.CioDecisionBody,
        judgment=cio.CioDecisionBody,
        stage="cio",
        produced_by=Producer.HYBRID,
        description="Final ensemble allocation and board memo (§3.6)",
    ),
]

CONTRACTS: dict[str, Spec] = {spec.name: spec for spec in _SPECS}
STAGES = ("macro", "cma", "pc", "review", "cio")


def spec(name: str) -> Spec:
    try:
        return CONTRACTS[name]
    except KeyError:
        raise KeyError(f"unknown contract {name!r}; known: {sorted(CONTRACTS)}") from None


def _require_all_properties(schema: dict[str, Any]) -> dict[str, Any]:
    """Mark every declared property as required, recursively.

    Strict structured outputs need each object to list all of its properties in ``required``
    alongside ``additionalProperties: false``. Pydantic leaves out anything with a default, so
    a field like ``regime_qualifier: str | None = None`` would be optional in the schema and
    the model could simply omit it. Requiring it keeps the field nullable but forces an
    explicit ``null``, which is what makes a missing value distinguishable from a forgotten
    one. Python callers keep the ergonomic defaults; only the schema handed to the API changes.
    """
    if isinstance(schema, dict):
        if schema.get("type") == "object" and "properties" in schema:
            schema["required"] = list(schema["properties"])
        for value in schema.values():
            _require_all_properties(value)
    elif isinstance(schema, list):
        for item in schema:
            _require_all_properties(item)
    return schema


def json_schema(name: str, *, judgment: bool = False) -> dict[str, Any]:
    """JSON Schema for a contract.

    ``judgment=True`` returns the schema the LLM is constrained to -- the small judgment model,
    not the whole file -- with every property required. The harness owns the header; the model
    never writes it.
    """
    entry = spec(name)
    if judgment:
        if entry.judgment is None:
            raise ValueError(f"{name} is script-generated and has no judgment model")
        return _require_all_properties(entry.judgment.model_json_schema())
    return entry.output_model.model_json_schema()


def write(output: AgentOutput, path: Path | str) -> Path:
    """Write a validated contract file (and create its directory)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    return path


def read(name: str, path: Path | str) -> AgentOutput:
    """Read and validate a contract file, failing loudly on drift."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return spec(name).output_model.model_validate(payload)

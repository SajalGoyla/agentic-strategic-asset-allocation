"""The output-contract envelope shared by every agent in the pipeline.

Ang, Azimbayev & Kim (2026) §3.2 make the output contract one of the four things that define
an agent: "JSON files conforming to defined schemas (for machine consumption by downstream
agents) and markdown reports (for human review). Every agent produces both quantitative
outputs and natural-language analysis, ensuring that the pipeline generates audit trails at
every step."

Three conventions hold across every contract:

**The envelope is machine-written, never model-written.** ``AgentOutput`` is ``header`` plus
``body``. The harness fills the header; the LLM only ever produces a *judgment* model nested
inside the body. So the schema handed to ``client.messages.parse(output_format=...)`` is the
small judgment model, not the file schema -- the model cannot fabricate its own provenance,
token counts or run id.

**Script output and LLM judgment are separate models.** §3.2: "the LLM handles judgment,
interpretation, and narrative; the scripts handle computation." Where a stage does both --
the macro agent scores dimensions then classifies, the asset-class agent computes seven CMA
candidates then judges them -- the body holds a deterministic half and a judgment half, and
``Producer`` records which is which.

**Every model forbids extra fields.** That makes ``model_json_schema()`` emit
``additionalProperties: false``, which the Messages API requires for strict structured
outputs, and it means a renamed field fails loudly instead of being silently dropped.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Bump the minor version for additive changes, the major for anything that breaks a reader.
SCHEMA_VERSION = "0.1.0"

# Weights come out of optimisers as floats; compare with a tolerance.
WEIGHT_SUM_TOL = 1e-6


class Contract(BaseModel):
    """Base for every contract model: no undeclared fields, in or out."""

    model_config = ConfigDict(extra="forbid")


class Producer(StrEnum):
    """Who generated a body: deterministic code, an LLM, or both."""

    SCRIPT = "script"
    LLM = "llm"
    HYBRID = "hybrid"


class Tier(StrEnum):
    """Model routing tier (project plan §6). Recorded so spend is attributable per agent."""

    FLAGSHIP = "flagship"
    LOW_COST = "low_cost"


class DatasetVersion(Contract):
    """One entry from ``DataStore.provenance()``."""

    run_id: str
    sha256: str


class ModelCall(Contract):
    """One LLM call, for the §6 budget and for the §5.1 monoculture question.

    The paper flags LLM monoculture as a risk and suggests multiple foundation models as a
    mitigation; that cannot be analysed after the fact unless each output records which model
    produced it.
    """

    model: str
    tier: Tier
    effort: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float | None = None


class InputRef(Contract):
    """An upstream contract file this agent read, so the run DAG can be reconstructed."""

    contract: str
    path: str  # relative to the pipeline run directory
    sha256: str | None = None


class Header(Contract):
    """Machine-written envelope. Agents never generate this."""

    schema_version: str = SCHEMA_VERSION
    contract: str
    agent: str  # slug, e.g. "macro" or "us-large-cap"
    pipeline_run_id: str
    as_of: date  # the date the analysis is dated to
    generated_at: datetime
    produced_by: Producer

    # Which lake versions were read (DataStore.provenance()) and which upstream files.
    provenance: dict[str, DatasetVersion] = Field(default_factory=dict)
    inputs: list[InputRef] = Field(default_factory=list)

    # Which policy governed this output. `ips_status` is "draft" until faculty ratify it, and
    # agents are expected to say so in their narrative.
    ips_version: float
    ips_status: str

    model_calls: list[ModelCall] = Field(default_factory=list)

    # §3.2: every agent produces markdown for human review alongside its JSON.
    report_path: str | None = None

    # §3.5 records the peer-review seed; resampled and Monte Carlo PC methods need one too.
    seed: int | None = None

    @property
    def cost_usd(self) -> float:
        return sum(c.cost_usd or 0.0 for c in self.model_calls)


BodyT = TypeVar("BodyT", bound=Contract)


class AgentOutput(Contract, Generic[BodyT]):
    """A complete contract file: machine-written header plus the agent's body."""

    header: Header
    body: BodyT


# --------------------------------------------------------------------------- shared pieces
class Confidence(StrEnum):
    """§4.1 classifies the March 2026 regime at "medium-high confidence"."""

    LOW = "low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium_high"
    HIGH = "high"


class Violation(Contract):
    """Mirrors ``saa.ips.Violation`` so compliance can be embedded in a contract."""

    rule: str
    severity: str
    message: str
    observed: float | None = None
    limit: float | None = None
    entity: str | None = None


class IpsCompliance(Contract):
    """§3.5: the CRO checks IPS compliance for every candidate; §3.6: the CIO is bound by it."""

    compliant: bool
    violations: list[Violation] = Field(default_factory=list)
    not_evaluated: list[str] = Field(default_factory=list)

    @classmethod
    def from_report(cls, report) -> IpsCompliance:
        """Build from a ``saa.ips.ComplianceReport``."""
        return cls.model_validate(report.to_dict())


class Weights(Contract):
    """Portfolio weights by asset id, validated to be fully invested."""

    weights: dict[str, float]

    @model_validator(mode="after")
    def _fully_invested(self) -> Weights:
        total = sum(self.weights.values())
        if abs(total - 1.0) > WEIGHT_SUM_TOL:
            raise ValueError(f"weights sum to {total:.6f}, expected 1.0")
        return self

"""macro-view.json -- the macro agent's regime call (Ang et al. 2026 §3.2, §4.1).

"With the data, it scores four dimensions -- growth, inflation, monetary policy, and financial
conditions -- using a weighted scoring framework to classify the current regime with a
confidence level into one of four regimes: expansion, late-cycle, recession, or recovery.
Finally, the agent writes a JSON file with the macro regimes and a narrative report. The JSON
output is consumed by all downstream asset-class agents."

Split in two, following the paper's script/LLM division:

* ``MacroScores`` is computed by ``scripts/regime_scores.py`` from ``DataStore.macro()``.
  No LLM touches it.
* ``MacroJudgment`` is the LLM's structured output -- the schema passed to
  ``messages.parse(output_format=MacroJudgment)``.

``PitQuality`` records how much of each dimension was true ALFRED vintage data rather than a
release-lag estimate at the requested ``as_of``. Only 8 of the 62 ingested FRED series carry
revision history, and their vintages start as late as 2011 (CFNAI) and 2016 (GDPNOW), so a
regime call dated before those years rests partly on revised data. Carrying the number in the
contract is what stops a backtest quietly overstating its own rigour.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import Field, model_validator

from saa.contracts.base import AgentOutput, Confidence, Contract

CONTRACT = "macro_view"
FILENAME = "macro-view.json"

DIMENSIONS = ("growth", "inflation", "monetary_policy", "financial_conditions")


class Regime(StrEnum):
    EXPANSION = "expansion"
    LATE_CYCLE = "late_cycle"
    RECESSION = "recession"
    RECOVERY = "recovery"


class Transform(StrEnum):
    """How a raw series was turned into a comparable score."""

    LEVEL = "level"
    YOY = "yoy"
    MOM_ANNUALISED = "mom_annualised"
    ZSCORE = "zscore"
    PERCENTILE = "percentile"
    DIFF = "diff"


# ------------------------------------------------------------------ deterministic: scripts
class IndicatorScore(Contract):
    """One FRED series contributing to one dimension."""

    series_id: str
    name: str
    value: float  # the transformed value actually scored
    raw_value: float | None = None
    transform: Transform
    score: float = Field(ge=-1.0, le=1.0)  # +1 supportive of growth/easing, -1 the reverse
    weight: float = Field(ge=0.0, le=1.0)
    observation_date: date
    available_from: date
    # True when the value came from an ALFRED vintage in force at as_of, rather than from a
    # release-lag estimate. See the module docstring.
    point_in_time: bool


class DimensionScore(Contract):
    dimension: str
    score: float = Field(ge=-1.0, le=1.0)
    indicators: list[IndicatorScore]

    @model_validator(mode="after")
    def _known_dimension(self) -> DimensionScore:
        if self.dimension not in DIMENSIONS:
            raise ValueError(f"unknown macro dimension {self.dimension!r}; expected {DIMENSIONS}")
        return self


class PitQuality(Contract):
    """How point-in-time a dimension actually was at this ``as_of``."""

    dimension: str
    indicators_total: int
    indicators_point_in_time: int

    @property
    def fraction(self) -> float:
        return (
            self.indicators_point_in_time / self.indicators_total if self.indicators_total else 0.0
        )


class MacroScores(Contract):
    """Deterministic output of the regime-scoring script."""

    dimensions: list[DimensionScore]
    pit_quality: list[PitQuality] = Field(default_factory=list)
    lookback_years: int

    @model_validator(mode="after")
    def _all_four(self) -> MacroScores:
        seen = [d.dimension for d in self.dimensions]
        missing = [d for d in DIMENSIONS if d not in seen]
        if missing:
            raise ValueError(f"macro scores are missing dimensions {missing}")
        return self

    def score(self, dimension: str) -> float:
        return next(d.score for d in self.dimensions if d.dimension == dimension)


# ------------------------------------------------------------------------ judgment: the LLM
class RecessionProbability(Contract):
    """§4.1 reports "a baseline recession probability of 25-35%" -- a range, not a point."""

    low_pct: float = Field(ge=0.0, le=100.0)
    high_pct: float = Field(ge=0.0, le=100.0)

    @model_validator(mode="after")
    def _ordered(self) -> RecessionProbability:
        if self.low_pct > self.high_pct:
            raise ValueError(
                f"recession probability low {self.low_pct} exceeds high {self.high_pct}"
            )
        return self


class DimensionRationale(Contract):
    dimension: str
    rationale: str


class MacroJudgment(Contract):
    """The LLM's structured output. Passed to ``messages.parse(output_format=...)``.

    Deliberately narrow: the model classifies and explains, it does not restate the numbers the
    script already computed.
    """

    regime: Regime
    # §4.1: "late-cycle with stagflationary risk" -- the qualifier carries real information
    # that the four-way enum cannot.
    regime_qualifier: str | None = None
    confidence: Confidence
    confidence_score: float = Field(ge=0.0, le=1.0)
    recession_probability: RecessionProbability
    dimension_rationales: list[DimensionRationale]
    key_risks: list[str]
    narrative: str

    @model_validator(mode="after")
    def _rationale_per_dimension(self) -> MacroJudgment:
        seen = [r.dimension for r in self.dimension_rationales]
        missing = [d for d in DIMENSIONS if d not in seen]
        if missing:
            raise ValueError(f"no rationale given for dimensions {missing}")
        return self


class MacroViewBody(Contract):
    scores: MacroScores
    judgment: MacroJudgment


MacroView = AgentOutput[MacroViewBody]

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
    # The last month that could actually be scored. Monthly growth releases lag by weeks, so
    # this is normally a month or two behind ``header.as_of``; the gap is the ragged edge, and
    # a reader needs it to know how stale the call is.
    data_end: date | None = None
    # False when the history was scored from the latest vintage of each series rather than
    # re-queried at every month end. Correct for a live run; not point-in-time for a backtest.
    point_in_time: bool = False

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


# --------------------------------------------------------------------------- regime_history
HISTORY_CONTRACT = "regime_history"
HISTORY_FILENAME = "regime_history.json"


class RegimeMonth(Contract):
    """One month's regime label and the dimension scores behind it."""

    date: date
    regime: Regime
    confidence: float = Field(ge=0.0, le=1.0)
    growth: float = Field(ge=-1.0, le=1.0)
    inflation: float = Field(ge=-1.0, le=1.0)
    monetary_policy: float = Field(ge=-1.0, le=1.0)
    financial_conditions: float = Field(ge=-1.0, le=1.0)


class RegimeHistoryBody(Contract):
    """Month-by-month regime labels (§3.3 method 2, and regime-conditional statistics).

    Written by the same deterministic scorer that produces ``macro-view.json``, so the label
    history and the current call can never disagree. ``point_in_time`` records whether each
    month was scored from data public at the time or from the latest vintage -- a backtest
    conditioning on these labels needs to know which.
    """

    months: list[RegimeMonth]
    point_in_time: bool
    lookback_years: int

    @model_validator(mode="after")
    def _ordered_and_unique(self) -> RegimeHistoryBody:
        dates = [m.date for m in self.months]
        if not dates:
            raise ValueError("regime history is empty")
        if len(set(dates)) != len(dates):
            raise ValueError("regime history has duplicate months")
        if dates != sorted(dates):
            raise ValueError("regime history must be in ascending date order")
        return self

    def labels(self) -> dict[date, str]:
        """Month -> regime label, for `conditional_stats(returns, risk_free, labels)`."""
        return {m.date: m.regime.value for m in self.months}


RegimeHistory = AgentOutput[RegimeHistoryBody]

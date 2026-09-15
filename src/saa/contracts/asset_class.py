"""The asset-class agent's six JSON outputs (Ang et al. 2026 Exhibit 3).

"Output: cma_methods.json, cma.json, signals.json, historical_stats.json, scenarios.json,
correlation_row.json, analysis.md"

Five are deterministic script output. Only ``cma.json`` involves LLM judgment -- §3.3 is
explicit that the seven candidates "are written to a cma_methods.json file by a Python script;
no LLM judgment is involved up to this point."

The CMA-judge skill (Exhibit 4) reads cma_methods.json, signals.json, macro-view.json and
historical_stats.json, and is bound by one hard constraint: "final estimate MUST be within
[min_method, max_method]". ``CmaBody`` enforces that in a validator rather than trusting the
prompt -- a judge that drifts outside the candidate range fails loudly.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from saa.contracts.base import AgentOutput, Confidence, Contract

# ------------------------------------------------------------------------ historical_stats
STATS_CONTRACT = "historical_stats"
STATS_FILENAME = "historical_stats.json"


class WindowStats(Contract):
    """Trailing statistics over one window. Annualised, in percent except ratios."""

    years: float | None = None  # None means "since inception of the spliced history"
    annualised_return_pct: float
    annualised_volatility_pct: float
    sharpe_ratio: float  # excess of the T-bill return
    max_drawdown_pct: float
    best_month_pct: float | None = None
    worst_month_pct: float | None = None
    positive_months_pct: float | None = None
    months: int


class RegimeStats(Contract):
    """§3.3 method 2 conditions the historical premium on the macro regime; these are the
    per-regime statistics that method reads."""

    regime: str
    annualised_return_pct: float
    annualised_volatility_pct: float
    months: int


class HistoricalStatsBody(Contract):
    asset_id: str
    history_start: str
    windows: list[WindowStats]
    by_regime: list[RegimeStats] = Field(default_factory=list)
    # Which proxy supplied each stretch of history, from DataStore.asset_returns(field="source").
    history_sources: dict[str, str] = Field(default_factory=dict)


HistoricalStats = AgentOutput[HistoricalStatsBody]


# ------------------------------------------------------------------------ correlation_row
CORRELATION_CONTRACT = "correlation_row"
CORRELATION_FILENAME = "correlation_row.json"


class CorrelationRowBody(Contract):
    """One asset's correlations against the rest of the universe (Exhibit 3 step 2)."""

    asset_id: str
    window_years: float
    correlations: dict[str, float]

    @model_validator(mode="after")
    def _in_range(self) -> CorrelationRowBody:
        bad = {k: v for k, v in self.correlations.items() if not -1.0 <= v <= 1.0}
        if bad:
            raise ValueError(f"correlations outside [-1, 1]: {bad}")
        if self.correlations.get(self.asset_id, 1.0) != 1.0:
            raise ValueError(f"self-correlation for {self.asset_id} must be 1.0")
        return self


CorrelationRow = AgentOutput[CorrelationRowBody]


# ----------------------------------------------------------------------------- signals
SIGNALS_CONTRACT = "signals"
SIGNALS_FILENAME = "signals.json"


class SignalCategory(StrEnum):
    """Exhibit 3 steps 3-5 and Exhibit 4's "asset-level macro, technical, valuation signals"."""

    MACRO = "macro"
    TECHNICAL = "technical"
    VALUATION = "valuation"
    SENTIMENT = "sentiment"


class Signal(Contract):
    name: str
    category: SignalCategory
    value: float | None = None
    score: float = Field(ge=-1.0, le=1.0)  # +1 bullish for this asset class
    rationale: str
    source: str | None = None  # dataset or "web_search"


class SignalsBody(Contract):
    asset_id: str
    signals: list[Signal]
    composite_score: float = Field(ge=-1.0, le=1.0)


Signals = AgentOutput[SignalsBody]


# --------------------------------------------------------------------------- cma_methods
METHODS_CONTRACT = "cma_methods"
METHODS_FILENAME = "cma_methods.json"


class CmaMethodId(StrEnum):
    """The seven candidates of Exhibit 4."""

    HISTORICAL_ERP = "historical_erp"
    REGIME_ADJUSTED = "regime_adjusted"
    BL_EQUILIBRIUM = "bl_equilibrium"
    INVERSE_GORDON = "inverse_gordon"
    IMPLIED_ERP_CAPE = "implied_erp_cape"
    SURVEY_CONSENSUS = "survey_consensus"
    AUTO_BLEND = "auto_blend"


class CmaMethodEstimate(Contract):
    """§3.3: "Each method returns a point estimate, a confidence score between 0 and 1, a
    component breakdown, and a one-line rationale"."""

    method: CmaMethodId
    expected_return_pct: float
    confidence: float = Field(ge=0.0, le=1.0)
    components: dict[str, float] = Field(default_factory=dict)
    rationale: str
    # Set when a method could not be computed from free data (see config/cma_inputs.yaml).
    unavailable_reason: str | None = None


class CmaMethodsBody(Contract):
    asset_id: str
    horizon_years: int
    volatility_pct: float
    methods: list[CmaMethodEstimate]

    @model_validator(mode="after")
    def _auto_blend_present(self) -> CmaMethodsBody:
        ids = [m.method for m in self.methods]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate CMA methods")
        if CmaMethodId.AUTO_BLEND not in ids:
            raise ValueError("cma_methods must include the auto-blend (Exhibit 4 method 7)")
        return self

    @property
    def available(self) -> list[CmaMethodEstimate]:
        return [m for m in self.methods if m.unavailable_reason is None]

    @property
    def method_range(self) -> tuple[float, float]:
        """The [min, max] the judge's final estimate must lie within."""
        values = [m.expected_return_pct for m in self.available]
        return min(values), max(values)


CmaMethods = AgentOutput[CmaMethodsBody]


# ---------------------------------------------------------------------------------- cma
CMA_CONTRACT = "cma"
CMA_FILENAME = "cma.json"


class Dispersion(StrEnum):
    """Exhibit 4 step 1: "tight <3pp / moderate 3-6pp / wide >6pp"."""

    TIGHT = "tight"
    MODERATE = "moderate"
    WIDE = "wide"

    @classmethod
    def classify(cls, spread_pp: float) -> Dispersion:
        if spread_pp < 3:
            return cls.TIGHT
        return cls.MODERATE if spread_pp <= 6 else cls.WIDE


class SelectionMode(StrEnum):
    """Exhibit 4 step 5: "pick one method, define custom weights, or accept blend"."""

    SINGLE_METHOD = "single_method"
    CUSTOM_BLEND = "custom_blend"
    AUTO_BLEND = "auto_blend"


class CmaJudgment(Contract):
    """The CMA judge's structured output -- the LLM half of the asset-class agent.

    Fields follow the five judgment steps of Exhibit 4, so the rationale is forced to cover
    dispersion, regime, valuation and signal alignment rather than a bare assertion.
    """

    selection: SelectionMode
    method_weights: dict[CmaMethodId, float]
    expected_return_pct: float
    confidence: Confidence
    dispersion: Dispersion
    regime_logic: str  # step 2
    valuation_context: str  # step 3
    signal_alignment: str  # step 4
    rationale: str

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> CmaJudgment:
        total = sum(self.method_weights.values())
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"method weights sum to {total:.4f}, expected 1.0")
        if any(w < 0 for w in self.method_weights.values()):
            raise ValueError("method weights must be non-negative")
        if self.selection == SelectionMode.SINGLE_METHOD:
            chosen = [m for m, w in self.method_weights.items() if w > 0]
            if len(chosen) != 1:
                raise ValueError(f"single_method selection has {len(chosen)} weighted methods")
        return self


class CmaBody(Contract):
    asset_id: str
    horizon_years: int
    expected_return_pct: float
    volatility_pct: float
    # Carried from cma_methods so the hard constraint can be checked without reopening it.
    method_range: tuple[float, float]
    judgment: CmaJudgment

    @model_validator(mode="after")
    def _within_method_range(self) -> CmaBody:
        low, high = self.method_range
        if low > high:
            raise ValueError(f"method_range {self.method_range} is inverted")
        if not low - 1e-9 <= self.expected_return_pct <= high + 1e-9:
            raise ValueError(
                f"{self.asset_id}: final CMA {self.expected_return_pct:.2f}% is outside the "
                f"candidate range [{low:.2f}, {high:.2f}] -- Exhibit 4 makes this a hard "
                "constraint on the judge"
            )
        if abs(self.judgment.expected_return_pct - self.expected_return_pct) > 1e-6:
            raise ValueError("cma.expected_return_pct disagrees with the judgment")
        return self


Cma = AgentOutput[CmaBody]


# ----------------------------------------------------------------------------- scenarios
SCENARIOS_CONTRACT = "scenarios"
SCENARIOS_FILENAME = "scenarios.json"


class Scenario(Contract):
    name: str  # bull | base | bear
    expected_return_pct: float
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    narrative: str


class ScenariosBody(Contract):
    """Exhibit 3 step 8: "Scenario analysis (bull/bear from method range)"."""

    asset_id: str
    scenarios: list[Scenario]

    @model_validator(mode="after")
    def _has_bull_and_bear(self) -> ScenariosBody:
        names = {s.name for s in self.scenarios}
        missing = {"bull", "bear"} - names
        if missing:
            raise ValueError(f"scenarios must include {sorted(missing)}")
        return self


Scenarios = AgentOutput[ScenariosBody]

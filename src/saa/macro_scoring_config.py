"""Typed loader for ``config/macro_scoring.yaml``.

Kept out of ``config.py`` because the scoring framework belongs to the macro agent rather than
to ingestion, but cross-validated against the macro catalogue at load time so a typo in a
series id fails immediately instead of quietly dropping an indicator.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from saa.contracts.macro import DIMENSIONS, Transform

RuleField = Literal[
    "growth_below",
    "growth_at_least",
    "inflation_below",
    "inflation_at_least",
    "monetary_policy_below",
    "monetary_policy_at_least",
    "financial_conditions_below",
    "financial_conditions_at_least",
    "momentum_below",
    "momentum_at_least",
]


class Indicator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    series: str
    transform: Transform
    sign: Literal[-1, 1]
    weight: float = Field(gt=0.0)
    diff_months: int = Field(default=12, gt=0)


class Dimension(BaseModel):
    model_config = ConfigDict(extra="forbid")

    indicators: list[Indicator]

    @model_validator(mode="after")
    def _unique_series(self) -> Dimension:
        ids = [i.series for i in self.indicators]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate indicators within a dimension: {dupes}")
        return self


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regime: str
    when: dict[RuleField, float]

    @model_validator(mode="after")
    def _known_regime(self) -> Rule:
        from saa.contracts.macro import Regime

        if self.regime not in {r.value for r in Regime}:
            raise ValueError(f"unknown regime {self.regime!r}")
        if not self.when:
            raise ValueError(f"rule for {self.regime} has no conditions")
        return self


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[Rule]
    default: str

    @model_validator(mode="after")
    def _known_default(self) -> Classification:
        from saa.contracts.macro import Regime

        if self.default not in {r.value for r in Regime}:
            raise ValueError(f"unknown default regime {self.default!r}")
        return self


class ConfidenceSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    margin_full: float = Field(gt=0.0)
    dispersion_penalty: float = Field(ge=0.0, le=1.0)
    coverage_penalty: float = Field(ge=0.0, le=1.0)


class MacroScoringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lookback_years: int = Field(gt=0)
    momentum_months: int = Field(gt=0)
    min_indicators: int = Field(gt=0)
    dimensions: dict[str, Dimension]
    classification: Classification
    confidence: ConfidenceSettings

    @model_validator(mode="after")
    def _all_four_dimensions(self) -> MacroScoringConfig:
        missing = [d for d in DIMENSIONS if d not in self.dimensions]
        if missing:
            raise ValueError(f"macro_scoring.yaml is missing dimensions {missing}")
        extra = sorted(set(self.dimensions) - set(DIMENSIONS))
        if extra:
            raise ValueError(f"macro_scoring.yaml scores undeclared dimensions {extra}")
        return self

    def indicators(self, dimension: str) -> list[Indicator]:
        return self.dimensions[dimension].indicators

    @property
    def series_ids(self) -> list[str]:
        seen: dict[str, None] = {}
        for dimension in DIMENSIONS:
            for indicator in self.indicators(dimension):
                seen[indicator.series] = None
        return list(seen)


def cross_validate(scoring: MacroScoringConfig, macro) -> None:
    """Every scored series must be ingested, and none may be evaluation-only.

    ``macro`` is a ``saa.config.MacroCatalog``. Scoring an ``evaluation_only`` series would put
    an ex-post label into a point-in-time input, which is the one mistake this whole layer
    exists to prevent.
    """
    catalog = {s.id: s for s in macro.series}
    unknown = sorted(set(scoring.series_ids) - set(catalog))
    if unknown:
        raise ValueError(f"macro_scoring.yaml scores series not in macro_series.yaml: {unknown}")

    labels = sorted(s for s in scoring.series_ids if catalog[s].evaluation_only)
    if labels:
        raise ValueError(
            f"macro_scoring.yaml scores evaluation-only series {labels}; these are known only "
            "ex post and cannot be regime inputs"
        )

    for dimension in DIMENSIONS:
        declared = {i.series for i in scoring.indicators(dimension)}
        wrong = sorted(s for s in declared if catalog[s].dimension != dimension)
        if wrong:
            raise ValueError(
                f"{dimension} scores series that macro_series.yaml assigns elsewhere: {wrong}"
            )

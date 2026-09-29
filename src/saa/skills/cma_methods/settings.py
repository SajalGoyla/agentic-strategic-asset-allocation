"""Typed loader for ``config/cma.yaml``: the numbers the CMA calculators need that no dataset
supplies (confidences, credit losses, yield recipes, the survey mapping)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from saa.config import Config
from saa.contracts.asset_class import CmaMethodId

CALCULATED = [m for m in CmaMethodId if m is not CmaMethodId.AUTO_BLEND]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Adjustments(_Model):
    fallback_input: float = Field(gt=0, le=1)
    reits_valuation: float = Field(gt=0, le=1)
    currency_unhedged: float = Field(gt=0, le=1)


class HistorySettings(_Model):
    start: date
    full_confidence_months: int = Field(gt=0)


class RegimeSettings(_Model):
    credibility_months: float = Field(gt=0)


class BlackLittermanSettings(_Model):
    risk_aversion: float | Literal["historical"]
    risk_aversion_bounds: tuple[float, float]


class ValuationSettings(_Model):
    cape_anchor_since: date
    reversion_years: float = Field(gt=0)
    max_stale_days: int = Field(gt=0)
    max_survey_age_days: int = Field(gt=0)


class YieldRecipe(_Model):
    series: list[str] = Field(min_length=1)
    add_spread: str | None = None
    fallback: bool = False
    unhedged: bool = False


class CmaSettings(_Model):
    applies_to: dict[CmaMethodId, list[str]]
    confidence: dict[CmaMethodId, dict[str, float]]
    adjustments: Adjustments
    history: HistorySettings
    regime: RegimeSettings
    black_litterman: BlackLittermanSettings
    valuation: ValuationSettings
    yields: dict[str, list[YieldRecipe]]
    credit_loss_pct: dict[str, float]
    survey: dict[str, str]
    risk_free_series: str
    growth_survey: str
    inflation_survey: str

    @model_validator(mode="after")
    def _complete(self) -> CmaSettings:
        for name, table in (("applies_to", self.applies_to), ("confidence", self.confidence)):
            missing = [m.value for m in CALCULATED if m not in table]
            if missing:
                raise ValueError(f"cma.yaml {name} is missing methods {missing}")
        for method, table in self.confidence.items():
            if "default" not in table:
                raise ValueError(f"cma.yaml confidence.{method} needs a `default`")
        return self

    def applies(self, method: CmaMethodId, asset_id: str, group: str) -> bool:
        targets = self.applies_to[method]
        return asset_id in targets or group in targets

    def base_confidence(self, method: CmaMethodId, asset_id: str, group: str) -> float:
        table = self.confidence[method]
        return table.get(asset_id, table.get(group, table["default"]))

    def cross_validate(self, config: Config) -> CmaSettings:
        """Every asset and series named here must exist in the universe and macro catalog."""
        assets = {a.id for a in config.universe.assets}
        groups = {a.group for a in config.universe.assets}
        series = set(config.macro.ids)
        bad_targets = {t for targets in self.applies_to.values() for t in targets} - assets - groups
        bad_assets = (set(self.yields) | set(self.credit_loss_pct) | set(self.survey)) - assets
        needed = {s for recipes in self.yields.values() for r in recipes for s in r.series}
        needed |= {r.add_spread for recipes in self.yields.values() for r in recipes} - {None}
        needed.add(self.risk_free_series)
        problems = [
            f"unknown applies_to targets {sorted(bad_targets)}" if bad_targets else "",
            f"unknown assets {sorted(bad_assets)}" if bad_assets else "",
            f"series not in macro_series.yaml {sorted(needed - series)}" if needed - series else "",
        ]
        problems = [p for p in problems if p]
        if problems:
            raise ValueError("config/cma.yaml: " + "; ".join(problems))
        return self


def load_cma_settings(config: Config, path: Path | str | None = None) -> CmaSettings:
    path = Path(path) if path is not None else config.config_dir / "cma.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return CmaSettings.model_validate(raw).cross_validate(config)

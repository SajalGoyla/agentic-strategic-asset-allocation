"""Typed loader for ``config/signals.yaml``."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from saa.config import Config


class Weighted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weight: float = Field(gt=0.0)


class MomentumSettings(Weighted):
    lookback_months: int = Field(gt=0)
    skip_months: int = Field(ge=0)


class TrendSettings(Weighted):
    window_months: int = Field(gt=0)


class MeanReversionSettings(Weighted):
    lookback_months: int = Field(gt=0)


class TechnicalSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    momentum: MomentumSettings
    trend: TrendSettings
    mean_reversion: MeanReversionSettings
    relative_momentum: MomentumSettings


class ValuationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    earnings_yield: Weighted
    cape: Weighted
    yield_level: Weighted
    credit_spread: Weighted


class RegimeFitSettings(Weighted):
    min_months: int = Field(gt=0)


class DimensionAlignmentSettings(Weighted):
    dimensions: list[str]
    window_months: int = Field(gt=0)


class MacroSignalSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    regime_fit: RegimeFitSettings
    dimension_alignment: DimensionAlignmentSettings


class SignalSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lookback_years: int = Field(gt=0)
    min_months: int = Field(gt=0)
    category_weights: dict[str, float]
    technical: TechnicalSettings
    valuation: ValuationSettings
    macro: MacroSignalSettings
    credit_spreads: dict[str, str] = Field(default_factory=dict)
    yield_levels: dict[str, str] = Field(default_factory=dict)

    @property
    def series_ids(self) -> list[str]:
        """Every FRED series the valuation signals need."""
        return sorted(set(self.credit_spreads.values()) | set(self.yield_levels.values()))


def load_signal_settings(config: Config, path: Path | None = None) -> SignalSettings:
    path = path or config.config_dir / "signals.yaml"
    settings = SignalSettings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))

    known = {s.id for s in config.macro.series}
    missing = sorted(set(settings.series_ids) - known)
    if missing:
        raise ValueError(f"signals.yaml references series not in macro_series.yaml: {missing}")

    asset_ids = {a.id for a in config.universe.assets}
    for field in ("credit_spreads", "yield_levels"):
        unknown = sorted(set(getattr(settings, field)) - asset_ids)
        if unknown:
            raise ValueError(f"signals.yaml {field} references unknown assets: {unknown}")
    return settings

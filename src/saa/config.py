"""Configuration: YAML files under ``config/`` plus secrets from environment / ``.env``.

The YAML files are the single source of truth for *what* is ingested (asset universe, macro
series, source settings). Code should never hard-code tickers or series IDs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]

Frequency = Literal["d", "w", "m", "q", "a"]
AssetGroup = Literal["equity", "fixed_income", "real_assets", "cash"]


# --------------------------------------------------------------------------- universe
class Asset(BaseModel):
    id: str
    name: str
    group: AssetGroup
    ticker: str
    benchmark: str
    inception: date
    backfill_ticker: str | None = None
    history_proxy: str | None = None
    cma_series: list[str] = Field(default_factory=list)
    notes: str | None = None


class Universe(BaseModel):
    assets: list[Asset]
    reference_tickers: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique(self) -> Universe:
        for attr in ("id", "ticker"):
            values = [getattr(a, attr) for a in self.assets]
            dupes = sorted({v for v in values if values.count(v) > 1})
            if dupes:
                raise ValueError(f"duplicate asset {attr}s: {dupes}")
        return self

    @property
    def tickers(self) -> list[str]:
        return [a.ticker for a in self.assets]

    def all_tickers(self) -> list[str]:
        """ETF tickers, backfill proxies and reference tickers (de-duplicated, ordered)."""
        seq = self.tickers + [a.backfill_ticker for a in self.assets if a.backfill_ticker]
        return list(dict.fromkeys(seq + self.reference_tickers))

    def get(self, asset_id: str) -> Asset:
        for asset in self.assets:
            if asset.id == asset_id:
                return asset
        raise KeyError(asset_id)


# --------------------------------------------------------------------------- macro series
class MacroSeries(BaseModel):
    id: str
    name: str
    dimension: str
    frequency: Frequency
    release_lag_days: int = 0
    vintages: bool = False
    evaluation_only: bool = False
    start: date | None = None
    notes: str | None = None


class MacroCatalog(BaseModel):
    dimensions: dict[str, str]
    series: list[MacroSeries]

    @model_validator(mode="after")
    def _check(self) -> MacroCatalog:
        ids = [s.id for s in self.series]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate macro series ids: {dupes}")
        unknown = sorted({s.dimension for s in self.series} - set(self.dimensions))
        if unknown:
            raise ValueError(f"series reference undeclared dimensions: {unknown}")
        return self

    @property
    def ids(self) -> list[str]:
        return [s.id for s in self.series]

    def by_dimension(self, dimension: str) -> list[MacroSeries]:
        return [s for s in self.series if s.dimension == dimension]


# --------------------------------------------------------------------------- source settings
class HttpSettings(BaseModel):
    user_agent: str
    timeout_s: float = 60.0
    max_retries: int = 4
    backoff_s: float = 1.5


class FredSettings(BaseModel):
    observation_start: date
    vintage_start: date
    vintage_chunk_years: int = 5
    min_request_interval_s: float = 0.6


class YahooSettings(BaseModel):
    max_retries: int = 3
    pause_s: float = 1.0
    fund_snapshot: bool = True


class FrenchDataset(BaseModel):
    name: str
    description: str = ""


class FrenchSettings(BaseModel):
    base_url: str
    release_lag_days: int = 60
    datasets: list[FrenchDataset]


class TreasuryCurve(BaseModel):
    type: str
    start_year: int


class TreasurySettings(BaseModel):
    base_url: str
    min_request_interval_s: float = 0.3
    curves: dict[str, TreasuryCurve]


class ShillerSettings(BaseModel):
    homepage: str
    fallback_url: str
    release_lag_days: int = 60


class SpfSettings(BaseModel):
    url: str
    release_lag_days: int = 45
    variables: list[str]


class ValidationSettings(BaseModel):
    stale_days: dict[str, int]
    max_abs_daily_return: float = 0.25
    max_gap_days: int = 10


class Settings(BaseModel):
    data_dir: Path
    keep_raw: bool = True
    http: HttpSettings
    fred: FredSettings
    yahoo: YahooSettings
    french: FrenchSettings
    treasury: TreasurySettings
    shiller: ShillerSettings
    spf: SpfSettings
    validation: ValidationSettings


@dataclass(frozen=True)
class Config:
    settings: Settings
    universe: Universe
    macro: MacroCatalog
    fred_api_key: str | None
    config_dir: Path


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_config(config_dir: Path | str | None = None) -> Config:
    """Load and cross-validate all configuration. Secrets come from the environment/.env."""
    load_dotenv(PROJECT_ROOT / ".env")
    config_dir = Path(config_dir or os.getenv("SAA_CONFIG_DIR") or PROJECT_ROOT / "config")

    settings = Settings.model_validate(_read_yaml(config_dir / "data_sources.yaml"))
    data_dir = Path(os.getenv("SAA_DATA_DIR") or settings.data_dir)
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    settings = settings.model_copy(update={"data_dir": data_dir})

    universe = Universe.model_validate(_read_yaml(config_dir / "universe.yaml"))
    macro = MacroCatalog.model_validate(_read_yaml(config_dir / "macro_series.yaml"))

    missing = sorted({s for a in universe.assets for s in a.cma_series} - set(macro.ids))
    if missing:
        raise ValueError(f"universe.yaml cma_series not declared in macro_series.yaml: {missing}")

    return Config(
        settings=settings,
        universe=universe,
        macro=macro,
        fred_api_key=os.getenv("FRED_API_KEY") or None,
        config_dir=config_dir,
    )

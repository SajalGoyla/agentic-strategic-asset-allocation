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

from saa.ips import IPS

PROJECT_ROOT = Path(__file__).resolve().parents[2]

Frequency = Literal["d", "w", "m", "q", "a"]
AssetGroup = Literal["equity", "fixed_income", "real_assets", "cash"]


# --------------------------------------------------------------------------- universe
class HistorySource(BaseModel):
    """One link in an asset's return-history chain, used for months before the ETF existed."""

    source: Literal[
        "yahoo", "french", "par_bond", "worldbank", "crsp_treasury", "crsp_stock", "crsp_fund"
    ]
    kind: str
    ticker: str | None = None
    permno: int | None = None
    dataset: str | None = None
    columns: list[str] = Field(default_factory=list)
    combine: Literal["sum", "mean"] = "sum"
    series: list[str] = Field(default_factory=list)
    maturity_years: float | None = None
    commodity: str | None = None

    @model_validator(mode="after")
    def _required(self) -> HistorySource:
        required = {
            "yahoo": ["ticker"],
            "french": ["dataset", "columns"],
            "par_bond": ["series", "maturity_years"],
            "worldbank": ["commodity"],
            "crsp_treasury": ["columns"],
            "crsp_stock": ["permno"],
            "crsp_fund": ["ticker"],
        }[self.source]
        missing = [f for f in required if not getattr(self, f)]
        if missing:
            raise ValueError(f"{self.source} history link needs {missing}")
        return self

    @property
    def label(self) -> str:
        if self.source == "yahoo":
            return str(self.ticker)
        if self.source == "french":
            if self.combine == "sum":
                joined = " + ".join(self.columns)
            else:
                joined = f"mean({', '.join(self.columns)})"
            return f"french:{self.dataset}[{joined}]"
        if self.source == "par_bond":
            return f"par_bond:{'/'.join(self.series)}@{self.maturity_years:g}y"
        if self.source == "crsp_treasury":
            return f"crsp:mcti[{'/'.join(self.columns)}]"
        if self.source == "crsp_stock":
            return f"crsp:{self.ticker or 'permno'}({self.permno})"
        if self.source == "crsp_fund":
            return f"crsp_fund:{self.ticker}"
        return f"worldbank:{self.commodity}"

    @property
    def licensed(self) -> bool:
        """WRDS/CRSP links: licensed data, available only with WRDS credentials."""
        return self.source.startswith("crsp")


class Asset(BaseModel):
    id: str
    name: str
    group: AssetGroup
    ticker: str
    benchmark: str
    inception: date
    crsp_permno: int | None = None
    history: list[HistorySource] = Field(default_factory=list)
    cma_series: list[str] = Field(default_factory=list)
    notes: str | None = None

    @property
    def proxy_tickers(self) -> list[str]:
        return [h.ticker for h in self.history if h.source == "yahoo" and h.ticker]


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
        """ETF tickers, Yahoo history proxies and reference tickers (de-duplicated, ordered)."""
        seq = self.tickers + [t for a in self.assets for t in a.proxy_tickers]
        return list(dict.fromkeys(seq + self.reference_tickers))

    def crsp_permnos(self) -> list[int]:
        """CRSP securities to pull: the ETFs (for cross-checks) and crsp_stock history links."""
        seq = [a.crsp_permno for a in self.assets if a.crsp_permno]
        seq += [h.permno for a in self.assets for h in a.history if h.source == "crsp_stock"]
        return list(dict.fromkeys(p for p in seq if p))

    def crsp_fund_tickers(self) -> list[str]:
        seq = [h.ticker for a in self.assets for h in a.history if h.source == "crsp_fund"]
        return list(dict.fromkeys(t for t in seq if t))

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


class WorldBankSettings(BaseModel):
    page: str
    fallback_url: str
    release_lag_days: int = 5


class WrdsSettings(BaseModel):
    enabled: bool = True
    release_lag_days: int = 1
    treasury_series: list[str] = Field(default_factory=list)


class HistorySettings(BaseModel):
    earliest: date
    target_start: date
    backtest_start: date
    month_end_tolerance_days: int = 7
    max_abs_monthly_return: float = 0.5


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
    worldbank: WorldBankSettings
    wrds: WrdsSettings = Field(default_factory=WrdsSettings)
    history: HistorySettings
    validation: ValidationSettings


@dataclass(frozen=True)
class Config:
    settings: Settings
    universe: Universe
    macro: MacroCatalog
    ips: IPS
    fred_api_key: str | None
    config_dir: Path


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _cross_validate_ips(ips: IPS, universe: Universe, macro: MacroCatalog) -> None:
    """The IPS is written by humans, so catch the ways it can drift from the universe."""
    asset_ids = {a.id for a in universe.assets}
    groups = {a.group for a in universe.assets}

    unknown = sorted(set(ips.active_risk.benchmark.weights) - asset_ids)
    if unknown:
        raise ValueError(
            f"ips.yaml benchmark {ips.active_risk.benchmark.id} references assets not in "
            f"universe.yaml: {unknown}"
        )

    undeclared = sorted(set(ips.universe.bounds.per_group) - groups)
    if undeclared:
        raise ValueError(f"ips.yaml per_group bounds reference unknown groups: {undeclared}")

    uncovered = sorted(groups - set(ips.universe.bounds.per_group))
    if uncovered:
        raise ValueError(f"ips.yaml declares no per_group bounds for: {uncovered}")

    if ips.objectives.return_.inflation_series not in set(macro.ids):
        raise ValueError(
            f"ips.yaml inflation_series {ips.objectives.return_.inflation_series!r} is not "
            "declared in macro_series.yaml"
        )

    # The benchmark is a measuring stick, not a candidate allocation: a 60/40 index is
    # concentrated by construction and is deliberately *not* held to the portfolio's
    # diversification bounds. Only well-formedness is checked (the Benchmark model already
    # enforces that the weights sum to 1).
    negative = sorted(k for k, v in ips.active_risk.benchmark.weights.items() if v < 0)
    if negative:
        raise ValueError(
            f"ips.yaml benchmark {ips.active_risk.benchmark.id} has negative weights: {negative}"
        )


def _cross_validate(settings: Settings, universe: Universe, macro: MacroCatalog) -> None:
    fred_ids = set(macro.ids)
    missing = sorted({s for a in universe.assets for s in a.cma_series} - fred_ids)
    if missing:
        raise ValueError(f"universe.yaml cma_series not declared in macro_series.yaml: {missing}")

    french = {d.name for d in settings.french.datasets}
    for asset in universe.assets:
        for link in asset.history:
            if link.source == "par_bond" and not set(link.series) <= fred_ids:
                raise ValueError(
                    f"{asset.id}: par_bond series {link.series} not in macro_series.yaml"
                )
            if link.source == "french" and link.dataset not in french:
                raise ValueError(
                    f"{asset.id}: French dataset {link.dataset} not in data_sources.yaml"
                )
            treasury = set(settings.wrds.treasury_series)
            if link.source == "crsp_treasury" and not set(link.columns) <= treasury:
                raise ValueError(
                    f"{asset.id}: CRSP Treasury columns {link.columns} not in wrds.treasury_series"
                )


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
    ips = IPS.model_validate(_read_yaml(config_dir / "ips.yaml"))
    _cross_validate(settings, universe, macro)
    _cross_validate_ips(ips, universe, macro)

    return Config(
        settings=settings,
        universe=universe,
        macro=macro,
        ips=ips,
        fred_api_key=os.getenv("FRED_API_KEY") or None,
        config_dir=config_dir,
    )

"""Output models of the historical-analysis skill.

DRAFT (schema_version "0.1-draft"): these move into the shared output-contract package once the
project schemas are agreed. Returns and risk figures are decimals (0.05 = 5%). A value is null
when the window does not have enough history.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

SCHEMA_VERSION = "0.1-draft"


class WindowStats(BaseModel):
    window: str = Field(description="window name, e.g. '10y' or 'since_1990'")
    start: date | None = None
    end: date | None = None
    months: int = 0
    sufficient: bool = Field(
        False, description="false when history is too short; metrics are then null"
    )
    annualized_return: float | None = Field(None, description="geometric")
    cumulative_return: float | None = None
    annualized_volatility: float | None = None
    sharpe_ratio: float | None = Field(None, description="vs 3-month T-bill")
    sortino_ratio: float | None = None
    max_drawdown: float | None = Field(None, description="negative decimal, e.g. -0.35")
    max_drawdown_peak: date | None = Field(None, description="null = peak at window start")
    max_drawdown_trough: date | None = None
    max_drawdown_recovery: date | None = Field(None, description="null = not yet recovered")
    max_drawdown_duration_months: int | None = None
    current_drawdown: float | None = None
    var_95_monthly: float | None = Field(None, description="historical VaR, positive loss")
    cvar_95_monthly: float | None = Field(None, description="expected shortfall, positive loss")
    skewness: float | None = None
    excess_kurtosis: float | None = None
    best_month: float | None = None
    best_month_date: date | None = None
    worst_month: float | None = None
    worst_month_date: date | None = None
    hit_rate: float | None = Field(None, description="share of positive months")
    beta_to_us_large_cap: float | None = None
    correlation_to_us_large_cap: float | None = None
    correlation_to_intermediate_treasuries: float | None = None
    proxy_share: float | None = Field(
        None, description="share of months from pre-ETF proxies rather than the ETF itself"
    )


class SourceSpan(BaseModel):
    source: str
    kind: str
    start: date
    end: date
    months: int


class AssetHistoricalStats(BaseModel):
    """Contents of ``historical_stats.json`` for one asset class."""

    schema_version: str = SCHEMA_VERSION
    asset_id: str
    name: str
    group: str
    ticker: str
    as_of: date = Field(description="information date: only data available by then is used")
    data_end: date | None = Field(None, description="last month-end return used")
    history_start: date | None = None
    sources: list[SourceSpan] = Field(default_factory=list)
    windows: dict[str, WindowStats]
    recent_daily_volatility: dict[str, float | None] = Field(
        default_factory=dict, description="ETF daily-return volatility, annualised: 3m, 1y"
    )
    provenance: dict[str, dict] = Field(default_factory=dict)


class CorrelationRow(BaseModel):
    """Contents of ``correlation_row.json``: one asset's correlations with the other 17."""

    schema_version: str = SCHEMA_VERSION
    asset_id: str
    as_of: date
    end: date | None = None
    months: dict[str, int] = Field(description="window -> number of months in the window")
    correlations: dict[str, dict[str, float | None]] = Field(
        description="window -> other asset_id -> correlation of monthly returns"
    )


class RegimeStats(BaseModel):
    regime: str
    months: int
    annualized_mean_return: float | None = Field(None, description="arithmetic")
    annualized_volatility: float | None = None
    sharpe_ratio: float | None = None
    hit_rate: float | None = None


class StockBondCorrelation(BaseModel):
    pair: list[str]
    window_months: int
    latest: float | None = None
    one_year_ago: float | None = None
    min_10y: float | None = None
    max_10y: float | None = None


class HistoricalAnalysis(BaseModel):
    """Bundle written to ``historical_analysis.json``."""

    schema_version: str = SCHEMA_VERSION
    as_of: date
    generated_at: datetime
    data_end: date | None = Field(None, description="last month all assets have returns for")
    windows: dict[str, int | str] = Field(description="window -> months, or start date, or 'full'")
    risk_free: dict[str, str | float | None]
    assets: list[AssetHistoricalStats]
    correlation_rows: list[CorrelationRow]
    stock_bond_correlation: StockBondCorrelation | None = None
    regime_stats: dict[str, list[RegimeStats]] | None = Field(
        None, description="asset_id -> stats per regime label (only when labels are supplied)"
    )
    provenance: dict[str, dict] = Field(default_factory=dict)

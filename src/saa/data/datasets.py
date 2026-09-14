"""Canonical curated datasets: the data contract between ingestion and the agents.

Every table in the lake is long/tidy with an explicit schema and primary key. Tables that
feed look-ahead-sensitive work carry an ``available_from`` column: the first date on which the
observation could have been known. ``DataStore`` uses it to serve point-in-time views.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

DT = "datetime64[ns]"


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    description: str
    columns: dict[str, str]
    keys: tuple[str, ...]
    date_col: str | None = "date"
    # Column identifying one logical series (ticker, FRED id...). If a source fails to deliver
    # an expected entity, the pipeline carries that entity forward from the previous version.
    entity_col: str | None = None
    # Snapshot tables accumulate across runs instead of being replaced.
    accumulate: bool = False


_SPECS = [
    DatasetSpec(
        name="market/prices_daily",
        description="Daily OHLCV, adjusted close and distributions for ETFs and backfill funds (Yahoo)",
        columns={
            "date": DT, "ticker": "string", "open": "float64", "high": "float64",
            "low": "float64", "close": "float64", "adj_close": "float64", "volume": "float64",
            "dividends": "float64", "splits": "float64", "capital_gains": "float64",
        },
        keys=("ticker", "date"),
        entity_col="ticker",
    ),
    DatasetSpec(
        name="market/fund_snapshot",
        description="Point-in-time ETF fundamentals (P/E, yield, duration, AUM) captured each run (Yahoo)",
        columns={
            "snapshot_date": DT, "ticker": "string", "quote_type": "string",
            "total_assets": "float64", "expense_ratio_pct": "float64", "trailing_pe": "float64",
            "distribution_yield": "float64", "earnings_yield": "float64",
            "book_to_price": "float64", "duration_years": "float64", "maturity_years": "float64",
        },
        keys=("ticker", "snapshot_date"),
        date_col="snapshot_date",
        accumulate=True,
    ),
    DatasetSpec(
        name="macro/fred_observations",
        description="FRED/ALFRED observations; vintage rows carry realtime_start/realtime_end",
        columns={
            "series_id": "string", "date": DT, "value": "float64",
            "realtime_start": DT, "realtime_end": DT, "available_from": DT,
        },
        keys=("series_id", "date", "realtime_start"),
        entity_col="series_id",
    ),
    DatasetSpec(
        name="macro/fred_series_meta",
        description="FRED series metadata joined with the project macro catalog",
        columns={
            "series_id": "string", "title": "string", "dimension": "string",
            "frequency": "string", "units": "string", "seasonal_adjustment": "string",
            "last_updated": "string", "source_mode": "string",
        },
        keys=("series_id",),
        date_col=None,
        entity_col="series_id",
    ),
    DatasetSpec(
        name="factors/french",
        description="Ken French library monthly factor and portfolio returns (decimal)",
        columns={
            "dataset": "string", "date": DT, "factor": "string", "value": "float64",
            "available_from": DT,
        },
        keys=("dataset", "factor", "date"),
        entity_col="dataset",
    ),
    DatasetSpec(
        name="rates/treasury_par_curve",
        description="US Treasury daily par yield curves, nominal and real (percent)",
        columns={
            "curve": "string", "date": DT, "tenor": "string", "tenor_months": "float64",
            "yield_pct": "float64",
        },
        keys=("curve", "tenor_months", "date"),
        entity_col="curve",
    ),
    DatasetSpec(
        name="valuation/shiller_us_equity",
        description="Shiller S&P 500 monthly price, dividends, earnings, CPI, GS10 and CAPE",
        columns={
            "date": DT, "price": "float64", "dividend": "float64", "earnings": "float64",
            "cpi": "float64", "gs10": "float64", "real_price": "float64",
            "real_dividend": "float64", "real_earnings": "float64", "cape": "float64",
            "tr_cape": "float64", "excess_cape_yield": "float64", "available_from": DT,
        },
        keys=("date",),
    ),
    DatasetSpec(
        name="surveys/spf_median",
        description="Philadelphia Fed Survey of Professional Forecasters median forecasts",
        columns={
            "variable": "string", "survey_date": DT, "horizon": "string", "value": "float64",
            "available_from": DT,
        },
        keys=("variable", "horizon", "survey_date"),
        date_col="survey_date",
        entity_col="variable",
    ),
]

DATASETS: dict[str, DatasetSpec] = {spec.name: spec for spec in _SPECS}


def conform(df: pd.DataFrame, spec: DatasetSpec) -> pd.DataFrame:
    """Coerce a frame to the dataset schema; fail loudly on missing columns or duplicate keys."""
    missing = [c for c in spec.columns if c not in df.columns]
    if missing:
        raise ValueError(f"{spec.name}: missing columns {missing}")
    out = df[list(spec.columns)].copy()
    for col, dtype in spec.columns.items():
        if dtype == DT:
            out[col] = pd.to_datetime(out[col]).astype(DT)
        else:
            out[col] = out[col].astype(dtype)
    dupes = out.duplicated(list(spec.keys))
    if dupes.any():
        raise ValueError(f"{spec.name}: {int(dupes.sum())} duplicate rows on keys {spec.keys}")
    return out.sort_values(list(spec.keys)).reset_index(drop=True)

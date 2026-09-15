"""Point-in-time read API over the data lake.

Agents and skills should read data only through ``DataStore``:

* ``as_of`` returns only information that was available on that date (ALFRED vintages for
  revised macro series, estimated release dates otherwise), so backtests avoid look-ahead.
* The first read of each dataset pins its version; ``provenance()`` reports the pinned
  versions so agent output contracts can record exactly which data they used. Passing
  ``run_ids`` reproduces a historical run.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

import numpy as np
import pandas as pd

from saa.config import Config, load_config
from saa.data.lake import DataLake

DateLike = str | date

_RESAMPLE = {"W": "W-FRI", "M": "ME", "Q": "QE"}


def _as_list(value: str | Iterable[str] | None) -> list[str] | None:
    if value is None:
        return None
    return [value] if isinstance(value, str) else list(value)


def _earliest(*values: DateLike | None) -> pd.Timestamp | None:
    stamps = [pd.Timestamp(v) for v in values if v is not None]
    return min(stamps) if stamps else None


def _between(
    df: pd.DataFrame, col: str, start: DateLike | None, end: DateLike | None
) -> pd.DataFrame:
    if start is not None:
        df = df[df[col] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df[col] <= pd.Timestamp(end)]
    return df


def point_in_time(obs: pd.DataFrame, as_of: DateLike) -> pd.DataFrame:
    """Macro observations visible on ``as_of``: the vintage in force for ALFRED rows, otherwise
    rows whose estimated availability date has passed. One row per (series_id, date)."""
    as_of = pd.Timestamp(as_of)
    vintage = obs["realtime_start"].notna()
    in_force = (
        vintage
        & (obs["realtime_start"] <= as_of)
        & (obs["realtime_end"].isna() | (obs["realtime_end"] >= as_of))
    )
    released = ~vintage & (obs["available_from"] <= as_of)
    out = obs[in_force | released]
    out = out.sort_values(["series_id", "date", "realtime_start"], na_position="first")
    return out.drop_duplicates(["series_id", "date"], keep="last")


def latest_vintage(obs: pd.DataFrame) -> pd.DataFrame:
    """Current values: open-ended vintage rows, else estimated (non-vintage) rows.
    Both have realtime_end NaT; where both exist for a date the vintage row wins."""
    current = obs[obs["realtime_end"].isna()]
    current = current.sort_values(["series_id", "date", "realtime_start"], na_position="first")
    return current.drop_duplicates(["series_id", "date"], keep="last")


class DataStore:
    def __init__(self, config: Config | None = None, *, run_ids: dict[str, str] | None = None):
        self.config = config or load_config()
        self.lake = DataLake(self.config.settings.data_dir)
        self._pins = dict(run_ids or {})
        self._frames: dict[str, pd.DataFrame] = {}
        self._versions: dict[str, dict] = {}

    # ------------------------------------------------------------------ plumbing
    def _load(self, name: str) -> pd.DataFrame:
        if name not in self._frames:
            version = self.lake.version(name, self._pins.get(name))
            if version is None:
                raise FileNotFoundError(
                    f"dataset {name!r} has not been ingested yet; run `uv run saa-data ingest`"
                )
            self._frames[name] = pd.read_parquet(self.lake.root / version["path"])
            self._versions[name] = version
        return self._frames[name]

    def provenance(self) -> dict[str, dict]:
        """Dataset versions read so far; embed in agent outputs for reproducibility."""
        return {
            name: {"run_id": v["run_id"], "sha256": v["sha256"]}
            for name, v in self._versions.items()
        }

    @property
    def universe(self):
        return self.config.universe

    # ------------------------------------------------------------------ market
    def prices(
        self,
        tickers: str | Iterable[str] | None = None,
        *,
        field: str = "adj_close",
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
    ) -> pd.DataFrame:
        """Wide daily frame (date x ticker). Defaults to the 18 universe ETFs."""
        tickers = _as_list(tickers) or self.universe.tickers
        df = self._load("market/prices_daily")
        df = df[df["ticker"].isin(tickers)]
        df = _between(df, "date", start, _earliest(end, as_of))
        wide = df.pivot(index="date", columns="ticker", values=field)
        return wide.reindex(columns=[t for t in tickers if t in wide.columns])

    def returns(
        self,
        tickers: str | Iterable[str] | None = None,
        *,
        freq: str = "M",
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
        log: bool = False,
    ) -> pd.DataFrame:
        """Total returns from adjusted closes at D/W/M/Q frequency. The final period may be
        partial (e.g. month-to-date)."""
        px = self.prices(tickers, end=end, as_of=as_of)
        if freq != "D":
            px = px.resample(_RESAMPLE[freq]).last()
        rets = px.pct_change(fill_method=None).iloc[1:]
        if log:
            rets = np.log1p(rets)
        rets = rets.dropna(how="all")
        if start is not None:
            rets = rets[rets.index >= pd.Timestamp(start)]
        return rets

    def asset_returns(
        self,
        assets: str | Iterable[str] | None = None,
        *,
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
        field: str = "ret",
    ) -> pd.DataFrame:
        """Long-history monthly total returns (date x asset_id) for the 18 asset classes,
        ETF spliced with public proxies. ``field="source"`` shows which source each month
        came from; ``history_links()`` scores each proxy against its ETF."""
        ids = _as_list(assets) or [a.id for a in self.universe.assets]
        df = self._load("market/asset_returns_monthly")
        df = df[df["asset_id"].isin(ids)]
        if as_of is not None:
            df = df[df["available_from"] <= pd.Timestamp(as_of)]
        df = _between(df, "date", start, end)
        wide = df.pivot(index="date", columns="asset_id", values=field)
        return wide.reindex(columns=[i for i in ids if i in wide.columns])

    def history_links(self) -> pd.DataFrame:
        return self._load("market/asset_history_links")

    def fund_snapshot(
        self, tickers: str | Iterable[str] | None = None, *, as_of: DateLike | None = None
    ) -> pd.DataFrame:
        """Most recent fundamentals snapshot per ticker taken on or before ``as_of``."""
        tickers = _as_list(tickers) or self.universe.tickers
        df = self._load("market/fund_snapshot")
        df = df[df["ticker"].isin(tickers)]
        if as_of is not None:
            df = df[df["snapshot_date"] <= pd.Timestamp(as_of)]
        return (
            df.sort_values("snapshot_date")
            .groupby("ticker", observed=True)
            .tail(1)
            .set_index("ticker")
        )

    # ------------------------------------------------------------------ macro
    def _series_ids(self, series_ids, dimension, as_of, allow_lookahead) -> list[str]:
        catalog = {s.id: s for s in self.config.macro.series}
        explicit = _as_list(series_ids)
        if explicit is not None:
            ids = explicit
        elif dimension is not None:
            if dimension not in self.config.macro.dimensions:
                raise KeyError(f"unknown macro dimension {dimension!r}")
            ids = [s.id for s in self.config.macro.by_dimension(dimension)]
        else:
            ids = list(catalog)
        if as_of is not None and not allow_lookahead:
            blocked = [i for i in ids if i in catalog and catalog[i].evaluation_only]
            if blocked and explicit is not None:
                raise ValueError(
                    f"{blocked} are evaluation-only (known only ex post); "
                    "pass allow_lookahead=True for ex-post analysis"
                )
            ids = [i for i in ids if i not in blocked]
        return ids

    def macro_long(
        self,
        series_ids: str | Iterable[str] | None = None,
        *,
        dimension: str | None = None,
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
        allow_lookahead: bool = False,
    ) -> pd.DataFrame:
        ids = self._series_ids(series_ids, dimension, as_of, allow_lookahead)
        obs = self._load("macro/fred_observations")
        obs = obs[obs["series_id"].isin(ids)]
        obs = point_in_time(obs, as_of) if as_of is not None else latest_vintage(obs)
        return _between(obs, "date", start, end).reset_index(drop=True)

    def macro(
        self,
        series_ids: str | Iterable[str] | None = None,
        *,
        dimension: str | None = None,
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
        freq: str | None = None,
        allow_lookahead: bool = False,
    ) -> pd.DataFrame:
        """Wide frame (date x series_id). ``freq`` (W/M/Q) aligns mixed frequencies by taking the
        last available value in each period."""
        long = self.macro_long(
            series_ids,
            dimension=dimension,
            start=start,
            end=end,
            as_of=as_of,
            allow_lookahead=allow_lookahead,
        )
        wide = long.pivot(index="date", columns="series_id", values="value")
        if freq is not None:
            wide = wide.resample(_RESAMPLE[freq]).last()
        return wide

    def series_meta(self) -> pd.DataFrame:
        return self._load("macro/fred_series_meta").set_index("series_id")

    # ------------------------------------------------------------------ factors, rates, valuation, surveys
    def factors(
        self,
        dataset: str = "F-F_Research_Data_Factors",
        *,
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
    ) -> pd.DataFrame:
        df = self._load("factors/french")
        df = df[df["dataset"] == dataset]
        if as_of is not None:
            df = df[df["available_from"] <= pd.Timestamp(as_of)]
        df = _between(df, "date", start, end)
        return df.pivot(index="date", columns="factor", values="value")

    def yield_curve(
        self,
        curve: str = "nominal",
        *,
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
    ) -> pd.DataFrame:
        """Wide frame (date x tenor in months) of par yields in percent."""
        df = self._load("rates/treasury_par_curve")
        df = df[df["curve"] == curve]
        df = _between(df, "date", start, _earliest(end, as_of))
        return df.pivot(index="date", columns="tenor_months", values="yield_pct").sort_index(axis=1)

    def shiller(
        self,
        *,
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
    ) -> pd.DataFrame:
        df = self._load("valuation/shiller_us_equity")
        if as_of is not None:
            df = df[df["available_from"] <= pd.Timestamp(as_of)]
        return _between(df, "date", start, end).set_index("date").drop(columns="available_from")

    def commodity_prices(
        self,
        series: str | Iterable[str],
        *,
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
    ) -> pd.DataFrame:
        """World Bank monthly average prices (date x series), e.g. ``"Gold"``."""
        names = _as_list(series)
        df = self._load("commodities/worldbank_monthly")
        df = df[df["series"].isin(names)]
        if as_of is not None:
            df = df[df["available_from"] <= pd.Timestamp(as_of)]
        return _between(df, "date", start, end).pivot(
            index="date", columns="series", values="value"
        )

    def survey(
        self,
        variable: str,
        *,
        horizon: str | None = None,
        start: DateLike | None = None,
        end: DateLike | None = None,
        as_of: DateLike | None = None,
    ) -> pd.DataFrame | pd.Series:
        df = self._load("surveys/spf_median")
        df = df[df["variable"] == variable]
        if as_of is not None:
            df = df[df["available_from"] <= pd.Timestamp(as_of)]
        df = _between(df, "survey_date", start, end)
        wide = df.pivot(index="survey_date", columns="horizon", values="value")
        return wide[horizon] if horizon is not None else wide

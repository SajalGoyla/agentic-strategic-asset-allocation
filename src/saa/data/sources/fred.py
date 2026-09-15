"""FRED / ALFRED connector.

Two modes:

* ``api`` (``FRED_API_KEY`` set): official API with series metadata, plus the full ALFRED
  revision history for series flagged ``vintages: true``. Needed for look-ahead-free backtests.
* ``graph_csv`` (no key): public fredgraph CSV download. Latest vintage only; availability
  dates are approximated as period end + ``release_lag_days``.
"""

from __future__ import annotations

import io
import json
import logging
from datetime import date, timedelta

import pandas as pd

from saa.config import MacroSeries
from saa.data.http import Throttle, get
from saa.data.sources.base import FetchResult, Source

log = logging.getLogger(__name__)

API_URL = "https://api.stlouisfed.org/fred"
GRAPH_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
OPEN_ENDED = "9999-12-31"
OBS = "macro/fred_observations"
META = "macro/fred_series_meta"
OBS_COLUMNS = ["series_id", "date", "value", "realtime_start", "realtime_end", "available_from"]


def period_end(dates: pd.Series, frequency: str) -> pd.Series:
    """FRED stamps monthly/quarterly/annual observations at period start; roll to period end.
    Daily and weekly observations are already stamped at (or near) the period end."""
    dates = pd.to_datetime(dates)
    offset = {
        "m": pd.offsets.MonthEnd(0),
        "q": pd.offsets.QuarterEnd(0),
        "a": pd.offsets.YearEnd(0),
    }.get(frequency)
    return dates + offset if offset is not None else dates


def estimate_available_from(dates: pd.Series, series: MacroSeries) -> pd.Series:
    return period_end(dates, series.frequency) + pd.Timedelta(days=series.release_lag_days)


def vintage_windows(
    start: date, chunk_years: int, today: date | None = None
) -> list[tuple[str, str]]:
    """Split the real-time period into non-overlapping windows to keep API responses small.
    FRED clips realtime_start/realtime_end to the requested window, so windows tile exactly."""
    today = today or date.today()
    windows, cur = [], start
    while True:
        try:
            nxt = cur.replace(year=cur.year + chunk_years)
        except ValueError:  # 29 February
            nxt = cur.replace(year=cur.year + chunk_years, day=28)
        if nxt > today:
            windows.append((cur.isoformat(), OPEN_ENDED))
            return windows
        windows.append((cur.isoformat(), (nxt - timedelta(days=1)).isoformat()))
        cur = nxt


def parse_observations_json(
    pages: list[dict], series: MacroSeries, *, vintage: bool
) -> pd.DataFrame:
    rows = [obs for page in pages for obs in page.get("observations", [])]
    if not rows:
        return pd.DataFrame(columns=OBS_COLUMNS)
    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")  # FRED encodes missing as "."
    df = df.dropna(subset=["value"]).copy()
    df["series_id"] = series.id
    df["date"] = pd.to_datetime(df["date"])
    if vintage:
        df["realtime_start"] = pd.to_datetime(df["realtime_start"])
        df["realtime_end"] = pd.to_datetime(
            df["realtime_end"].where(df["realtime_end"] != OPEN_ENDED)
        )
        df["available_from"] = df["realtime_start"]
    else:
        df["realtime_start"] = pd.NaT
        df["realtime_end"] = pd.NaT
        df["available_from"] = estimate_available_from(df["date"], series)
    return df[OBS_COLUMNS].reset_index(drop=True)


def parse_graph_csv(text: str, series: MacroSeries) -> pd.DataFrame:
    raw = pd.read_csv(io.StringIO(text))
    if raw.shape[1] < 2 or str(raw.columns[1]).strip() != series.id:
        raise ValueError(f"unexpected fredgraph response: {text[:80]!r}")
    df = raw.iloc[:, :2].copy()
    df.columns = ["date", "value"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"]).copy()
    df["series_id"] = series.id
    df["date"] = pd.to_datetime(df["date"])
    df["realtime_start"] = pd.NaT
    df["realtime_end"] = pd.NaT
    df["available_from"] = estimate_available_from(df["date"], series)
    return df[OBS_COLUMNS].reset_index(drop=True)


class FredSource(Source):
    name = "fred"

    def __init__(self, config, session=None):
        super().__init__(config, session)
        self.api_key = config.fred_api_key
        self.throttle = Throttle(self.settings.fred.min_request_interval_s)

    @property
    def mode(self) -> str:
        return "api" if self.api_key else "graph_csv"

    def fetch(self) -> FetchResult:
        catalog = self.config.macro
        ids = set(catalog.ids)
        result = FetchResult(self.name, expected_entities={OBS: ids, META: ids})
        if self.mode == "graph_csv":
            result.warnings.append(
                "FRED_API_KEY not set: used keyless fredgraph CSV (latest vintage only, "
                "no metadata, availability dates approximated from release lags)"
            )

        observations, metadata = [], []
        for series in catalog.series:
            try:
                if self.mode == "api":
                    frame = self._observations_api(series, result)
                else:
                    frame = self._observations_csv(series, result)
            except Exception as exc:
                result.warnings.append(f"{series.id}: observations failed ({exc})")
                continue
            if frame.empty:
                result.warnings.append(f"{series.id}: no observations returned")
                continue
            observations.append(frame)
            metadata.append(self._metadata(series, result))
            log.info("fred %-18s %6d rows", series.id, len(frame))

        if observations:
            result.tables[OBS] = pd.concat(observations, ignore_index=True)
        if metadata:
            result.tables[META] = pd.DataFrame(metadata)
        return result

    def _start(self, series: MacroSeries) -> str:
        return (series.start or self.settings.fred.observation_start).isoformat()

    def _pages(self, series: MacroSeries, window: tuple[str, str] | None) -> list[dict]:
        params = {
            "series_id": series.id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": self._start(series),
            "limit": 100000,
        }
        if window:
            params["realtime_start"], params["realtime_end"] = window
        pages, offset = [], 0
        while True:
            params["offset"] = offset
            page = get(
                self.session,
                f"{API_URL}/series/observations",
                params=params,
                timeout=self.settings.http.timeout_s,
                throttle=self.throttle,
            ).json()
            pages.append(page)
            n = len(page.get("observations", []))
            offset += n
            if n == 0 or offset >= int(page.get("count", 0)):
                return pages

    def _first_vintage(self, series: MacroSeries) -> date | None:
        payload = get(
            self.session,
            f"{API_URL}/series/vintagedates",
            params={
                "series_id": series.id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": 1,
            },
            timeout=self.settings.http.timeout_s,
            throttle=self.throttle,
        ).json()
        dates = payload.get("vintage_dates") or []
        return date.fromisoformat(dates[0]) if dates else None

    def _observations_api(self, series: MacroSeries, result: FetchResult) -> pd.DataFrame:
        latest_pages = self._pages(series, None)
        result.raw[f"{series.id}.json"] = json.dumps(latest_pages).encode("utf-8")
        latest = parse_observations_json(latest_pages, series, vintage=False)
        if not series.vintages:
            return latest

        # ALFRED rejects real-time windows that start before a series' first vintage.
        first = self._first_vintage(series)
        if first is None:
            result.warnings.append(f"{series.id}: no ALFRED vintages; using latest values")
            return latest
        fred = self.settings.fred
        start = max(fred.vintage_start, first)
        vintage_pages = [
            page
            for window in vintage_windows(start, fred.vintage_chunk_years)
            for page in self._pages(series, window)
        ]
        result.raw[f"{series.id}_vintages.json"] = json.dumps(vintage_pages).encode("utf-8")
        vintages = parse_observations_json(vintage_pages, series, vintage=True)
        # Dates that became public before the first vintage keep latest (revised) values with
        # estimated release dates, so as-of queries still cover the early sample.
        backfill = latest[latest["available_from"] < pd.Timestamp(start)]
        return pd.concat([vintages, backfill], ignore_index=True)

    def _observations_csv(self, series: MacroSeries, result: FetchResult) -> pd.DataFrame:
        text = get(
            self.session,
            GRAPH_CSV_URL,
            params={"id": series.id, "cosd": self._start(series)},
            timeout=self.settings.http.timeout_s,
            throttle=self.throttle,
        ).text
        result.raw[f"{series.id}.csv"] = text.encode("utf-8")
        return parse_graph_csv(text, series)

    def _metadata(self, series: MacroSeries, result: FetchResult) -> dict:
        row = {
            "series_id": series.id,
            "title": series.name,
            "dimension": series.dimension,
            "frequency": series.frequency,
            "units": None,
            "seasonal_adjustment": None,
            "last_updated": None,
            "source_mode": self.mode,
        }
        if self.mode != "api":
            return row
        try:
            payload = get(
                self.session,
                f"{API_URL}/series",
                params={"series_id": series.id, "api_key": self.api_key, "file_type": "json"},
                timeout=self.settings.http.timeout_s,
                throttle=self.throttle,
            ).json()
            info = payload["seriess"][0]
        except Exception as exc:
            result.warnings.append(f"{series.id}: metadata failed ({exc})")
            return row
        reported = str(info.get("frequency_short", "")).lower()
        if reported and reported[0] != series.frequency:
            result.warnings.append(
                f"{series.id}: configured frequency '{series.frequency}' but FRED reports "
                f"'{info.get('frequency_short')}'"
            )
        row.update(
            title=info.get("title", series.name),
            units=info.get("units"),
            seasonal_adjustment=info.get("seasonal_adjustment_short"),
            last_updated=info.get("last_updated"),
        )
        return row

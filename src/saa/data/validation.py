"""Data-quality checks over the latest curated datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from saa.config import Config
from saa.data.datasets import DATASETS
from saa.data.lake import DataLake
from saa.data.sources.fred import period_end

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


@dataclass
class Check:
    dataset: str
    check: str
    status: str
    detail: str
    entity: str | None = None


@dataclass
class ValidationReport:
    generated_for: str
    checks: list[Check] = field(default_factory=list)
    info: dict = field(default_factory=dict)

    def add(self, dataset: str, check: str, status: str, detail: str, entity: str | None = None):
        self.checks.append(Check(dataset, check, status, detail, entity))

    def summary(self) -> dict[str, int]:
        counts = {PASS: 0, WARN: 0, FAIL: 0}
        for c in self.checks:
            counts[c.status] += 1
        return counts

    @property
    def ok(self) -> bool:
        return self.summary()[FAIL] == 0

    def to_dict(self) -> dict:
        return {
            "generated_for": self.generated_for,
            "summary": self.summary(),
            "info": self.info,
            "checks": [asdict(c) for c in self.checks],
        }


def validate_lake(config: Config, lake: DataLake, today: date | None = None) -> ValidationReport:
    today = pd.Timestamp(today or date.today()).normalize()
    report = ValidationReport(generated_for=today.date().isoformat())
    frames: dict[str, pd.DataFrame] = {}
    for name, spec in DATASETS.items():
        if not lake.has_dataset(name):
            report.add(name, "exists", FAIL, "dataset has not been ingested")
            continue
        df = lake.read_dataset(name)
        frames[name] = df
        dupes = int(df.duplicated(list(spec.keys)).sum())
        report.add(
            name,
            "primary_key",
            FAIL if dupes else PASS,
            f"{dupes} duplicate keys" if dupes else f"{len(df)} rows, keys unique",
        )

    checks = {
        "market/prices_daily": _check_prices,
        "market/fund_snapshot": _check_fund_snapshot,
        "macro/fred_observations": _check_macro,
        "factors/french": _check_french,
        "rates/treasury_par_curve": _check_treasury,
        "valuation/shiller_us_equity": _check_shiller,
        "surveys/spf_median": _check_spf,
    }
    for name, check in checks.items():
        if name in frames:
            check(config, frames[name], report, today)
    return report


def _age_status(age_days: int, allowed_days: int) -> str:
    return PASS if age_days <= allowed_days else WARN


def _check_prices(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "market/prices_daily"
    v = config.settings.validation
    groups = {str(t): g.sort_values("date") for t, g in df.groupby("ticker", observed=True)}
    coverage = {}
    for asset in config.universe.assets:
        entry: dict[str, str] = {"ticker": asset.ticker}
        for role, ticker in (("etf", asset.ticker), ("backfill", asset.backfill_ticker)):
            if ticker is None:
                continue
            g = groups.get(ticker)
            if g is None:
                report.add(name, "present", FAIL if role == "etf" else WARN, f"{role} ticker has no data", ticker)
                continue
            first, last = g["date"].iloc[0], g["date"].iloc[-1]
            entry[f"{role}_first"] = first.date().isoformat()
            entry[f"{role}_last"] = last.date().isoformat()

            lag = int(np.busday_count(last.date(), today.date()))
            status = PASS if lag <= 3 else WARN if lag <= 10 else FAIL
            report.add(name, "freshness", status, f"last observation {last.date()} ({lag} business days ago)", ticker)

            if role == "etf":
                # Yahoo histories often begin a few weeks after launch (e.g. EFA)
                slack = pd.Timestamp(asset.inception) + pd.Timedelta(days=31)
                report.add(
                    name,
                    "history_start",
                    PASS if first <= slack else WARN,
                    f"first observation {first.date()}, fund inception {asset.inception}",
                    ticker,
                )

            bad = int((g["close"] <= 0).sum())
            if bad:
                report.add(name, "positive_prices", FAIL, f"{bad} non-positive closes", ticker)

            rets = g["adj_close"].pct_change(fill_method=None)
            jumps = g.loc[rets.abs() > v.max_abs_daily_return, "date"]
            detail = f"{len(jumps)} daily moves > {v.max_abs_daily_return:.0%}"
            if len(jumps):
                detail += f": {[d.date().isoformat() for d in jumps[:5]]}"
            report.add(name, "return_outliers", WARN if len(jumps) else PASS, detail, ticker)

            gaps = int((g["date"].diff().dt.days > v.max_gap_days).sum())
            report.add(name, "gaps", WARN if gaps else PASS, f"{gaps} gaps > {v.max_gap_days} calendar days", ticker)
        coverage[asset.id] = entry

    report.info["price_coverage"] = coverage
    starts = {a.ticker: groups[a.ticker]["date"].iloc[0] for a in config.universe.assets if a.ticker in groups}
    if starts:
        limiting = max(starts, key=starts.get)
        report.info["common_etf_history_start"] = starts[limiting].date().isoformat()
        report.info["common_etf_history_limited_by"] = limiting


def _check_fund_snapshot(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "market/fund_snapshot"
    latest = df[df["snapshot_date"] == df["snapshot_date"].max()]
    missing = sorted(set(config.universe.tickers) - set(latest["ticker"].astype(str)))
    report.add(
        name,
        "coverage",
        WARN if missing else PASS,
        f"latest snapshot {latest['snapshot_date'].max().date()} missing {missing}" if missing
        else f"latest snapshot {latest['snapshot_date'].max().date()} covers all ETFs",
    )


def _check_macro(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "macro/fred_observations"
    stale = config.settings.validation.stale_days
    latest = df.groupby("series_id", observed=True)["date"].max()
    first = df.groupby("series_id", observed=True)["date"].min()
    for s in config.macro.series:
        if s.id not in latest.index:
            report.add(name, "present", FAIL, "series missing", s.id)
            continue
        end = period_end(pd.Series([latest[s.id]]), s.frequency).iloc[0]
        age = (today - end).days
        allowed = stale[s.frequency] + max(s.release_lag_days, 0)
        report.add(
            name,
            "freshness",
            _age_status(age, allowed),
            f"last period {latest[s.id].date()} ended {age}d ago (allowed {allowed}d); "
            f"history from {first[s.id].date()}",
            s.id,
        )


def _check_french(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "factors/french"
    latest = df.groupby("dataset", observed=True)["date"].max()
    allowed = 2 * config.settings.validation.stale_days["m"] + config.settings.french.release_lag_days
    for ds in config.settings.french.datasets:
        if ds.name not in latest.index:
            report.add(name, "present", FAIL, "dataset missing", ds.name)
            continue
        age = (today - latest[ds.name]).days
        report.add(name, "freshness", _age_status(age, allowed), f"last month {latest[ds.name].date()} ({age}d ago)", ds.name)


def _check_treasury(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "rates/treasury_par_curve"
    allowed = config.settings.validation.stale_days["d"]
    for curve in config.settings.treasury.curves:
        g = df[df["curve"] == curve]
        if g.empty:
            report.add(name, "present", FAIL, "curve missing", curve)
            continue
        age = (today - g["date"].max()).days
        report.add(name, "freshness", _age_status(age, allowed), f"last date {g['date'].max().date()} ({age}d ago)", curve)
        out_of_range = int(((g["yield_pct"] < -3) | (g["yield_pct"] > 25)).sum())
        report.add(name, "yield_range", FAIL if out_of_range else PASS, f"{out_of_range} yields outside [-3%, 25%]", curve)


def _check_shiller(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "valuation/shiller_us_equity"
    last = df["date"].max()
    last_cape = df.loc[df["cape"].notna(), "date"].max()
    allowed = config.settings.validation.stale_days["m"] + config.settings.shiller.release_lag_days
    age = (today - last).days
    report.add(name, "freshness", _age_status(age, allowed), f"last month {last.date()} ({age}d ago); last CAPE {last_cape.date()}")


def _check_spf(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "surveys/spf_median"
    for var in config.settings.spf.variables:
        dates = df.loc[df["variable"] == var, "survey_date"].drop_duplicates().sort_values()
        if dates.empty:
            report.add(name, "present", FAIL, "variable missing", var)
            continue
        # Some long-horizon questions are asked only in Q1 surveys.
        cadence = dates.diff().dt.days.tail(8).median()
        allowed = 400 if cadence > 100 else 200
        age = (today - dates.iloc[-1]).days
        report.add(name, "freshness", _age_status(age, allowed), f"latest survey {dates.iloc[-1].date()} ({age}d ago)", var)

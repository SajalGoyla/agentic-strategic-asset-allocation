"""Data-quality checks over the latest curated datasets."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from saa.config import Config
from saa.data.datasets import DATASETS
from saa.data.history import last_complete_month_end, monthly_from_daily
from saa.data.lake import DataLake
from saa.data.sources.fred import period_end

log = logging.getLogger(__name__)

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
            if spec.optional:
                report.info.setdefault("optional_not_ingested", []).append(name)
            else:
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
        "commodities/worldbank_monthly": _check_worldbank,
        "market/asset_returns_monthly": _check_asset_history,
    }
    for name, check in checks.items():
        if name in frames:
            check(config, frames[name], report, today)
    if "wrds/crsp_stock_monthly" in frames and "market/prices_daily" in frames:
        _check_crsp_vs_yahoo(
            config, frames["wrds/crsp_stock_monthly"], frames["market/prices_daily"], report
        )
    return report


def _check_crsp_vs_yahoo(
    config: Config, crsp: pd.DataFrame, prices: pd.DataFrame, report: ValidationReport
):
    """Yahoo adjusted-close returns should reproduce CRSP total returns for the same ETF."""
    tolerance = config.settings.history.month_end_tolerance_days
    for asset in config.universe.assets:
        if not asset.crsp_permno:
            continue
        crsp_ret = crsp.loc[crsp["permno"] == asset.crsp_permno].set_index("date")["ret"]
        try:
            yahoo_ret = monthly_from_daily(prices, asset.ticker, tolerance)
        except KeyError:
            continue
        both = pd.concat([crsp_ret, yahoo_ret], axis=1, keys=["crsp", "yahoo"]).dropna()
        if len(both) < 12:
            continue
        diff = both["crsp"] - both["yahoo"]
        tracking, gap = diff.std() * np.sqrt(12), diff.mean() * 12
        report.add(
            "market/prices_daily",
            "matches_crsp",
            PASS if tracking <= 0.01 and abs(gap) <= 0.005 else WARN,
            f"{len(both)} months vs CRSP: tracking {tracking:.2%}, mean gap {gap:+.2%}/yr",
            asset.ticker,
        )


def _age_status(age_days: int, allowed_days: int) -> str:
    return PASS if age_days <= allowed_days else WARN


def _check_prices(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "market/prices_daily"
    v = config.settings.validation
    groups = {str(t): g.sort_values("date") for t, g in df.groupby("ticker", observed=True)}
    coverage = {}
    for asset in config.universe.assets:
        entry: dict = {"ticker": asset.ticker, "proxies": {}}
        roles = [("etf", asset.ticker)] + [("proxy", t) for t in asset.proxy_tickers]
        for role, ticker in roles:
            g = groups.get(ticker)
            if g is None:
                report.add(
                    name,
                    "present",
                    FAIL if role == "etf" else WARN,
                    f"{role} ticker has no data",
                    ticker,
                )
                continue
            first, last = g["date"].iloc[0], g["date"].iloc[-1]
            lag = int(np.busday_count(last.date(), today.date()))
            if role == "proxy":
                # Proxies only supply pre-ETF history; staleness is informational.
                entry["proxies"][ticker] = first.date().isoformat()
                if lag > 10:
                    report.add(
                        name, "freshness", WARN, f"proxy last observation {last.date()}", ticker
                    )
                continue
            entry["etf_first"] = first.date().isoformat()
            entry["etf_last"] = last.date().isoformat()
            status = PASS if lag <= 3 else WARN if lag <= 10 else FAIL
            report.add(
                name,
                "freshness",
                status,
                f"last observation {last.date()} ({lag} business days ago)",
                ticker,
            )

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
            report.add(
                name,
                "gaps",
                WARN if gaps else PASS,
                f"{gaps} gaps > {v.max_gap_days} calendar days",
                ticker,
            )
        coverage[asset.id] = entry

    report.info["price_coverage"] = coverage
    starts = {
        a.ticker: groups[a.ticker]["date"].iloc[0]
        for a in config.universe.assets
        if a.ticker in groups
    }
    if starts:
        limiting = max(starts, key=starts.get)
        report.info["common_etf_history_start"] = starts[limiting].date().isoformat()
        report.info["common_etf_history_limited_by"] = limiting


def _check_fund_snapshot(
    config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp
):
    name = "market/fund_snapshot"
    latest = df[df["snapshot_date"] == df["snapshot_date"].max()]
    missing = sorted(set(config.universe.tickers) - set(latest["ticker"].astype(str)))
    report.add(
        name,
        "coverage",
        WARN if missing else PASS,
        f"latest snapshot {latest['snapshot_date'].max().date()} missing {missing}"
        if missing
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
    allowed = (
        2 * config.settings.validation.stale_days["m"] + config.settings.french.release_lag_days
    )
    for ds in config.settings.french.datasets:
        if ds.name not in latest.index:
            report.add(name, "present", FAIL, "dataset missing", ds.name)
            continue
        age = (today - latest[ds.name]).days
        report.add(
            name,
            "freshness",
            _age_status(age, allowed),
            f"last month {latest[ds.name].date()} ({age}d ago)",
            ds.name,
        )


def _check_treasury(
    config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp
):
    name = "rates/treasury_par_curve"
    allowed = config.settings.validation.stale_days["d"]
    for curve in config.settings.treasury.curves:
        g = df[df["curve"] == curve]
        if g.empty:
            report.add(name, "present", FAIL, "curve missing", curve)
            continue
        age = (today - g["date"].max()).days
        report.add(
            name,
            "freshness",
            _age_status(age, allowed),
            f"last date {g['date'].max().date()} ({age}d ago)",
            curve,
        )
        out_of_range = int(((g["yield_pct"] < -3) | (g["yield_pct"] > 25)).sum())
        report.add(
            name,
            "yield_range",
            FAIL if out_of_range else PASS,
            f"{out_of_range} yields outside [-3%, 25%]",
            curve,
        )


def _check_shiller(config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp):
    name = "valuation/shiller_us_equity"
    last = df["date"].max()
    last_cape = df.loc[df["cape"].notna(), "date"].max()
    allowed = config.settings.validation.stale_days["m"] + config.settings.shiller.release_lag_days
    age = (today - last).days
    report.add(
        name,
        "freshness",
        _age_status(age, allowed),
        f"last month {last.date()} ({age}d ago); last CAPE {last_cape.date()}",
    )


def _check_worldbank(
    config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp
):
    name = "commodities/worldbank_monthly"
    needed = {
        h.commodity for a in config.universe.assets for h in a.history if h.source == "worldbank"
    }
    present = set(df["series"].astype(str))
    for commodity in sorted(needed):
        report.add(
            name,
            "present",
            PASS if commodity in present else FAIL,
            "used by asset history",
            commodity,
        )
    last = df["date"].max()
    allowed = (
        2 * config.settings.validation.stale_days["m"] + config.settings.worldbank.release_lag_days
    )
    age = (today - last).days
    report.add(
        name, "freshness", _age_status(age, allowed), f"last month {last.date()} ({age}d ago)"
    )


def _check_asset_history(
    config: Config, df: pd.DataFrame, report: ValidationReport, today: pd.Timestamp
):
    name = "market/asset_returns_monthly"
    h = config.settings.history
    target = pd.Timestamp(h.target_start) + pd.offsets.MonthEnd(0)
    backtest = pd.Timestamp(h.backtest_start) + pd.offsets.MonthEnd(0)
    expected_last = last_complete_month_end(today)
    coverage = {}
    starts = {}
    for asset in config.universe.assets:
        g = df[df["asset_id"] == asset.id].sort_values("date")
        if g.empty:
            report.add(name, "present", FAIL, "no monthly return history", asset.id)
            continue
        first, last = g["date"].iloc[0], g["date"].iloc[-1]
        starts[asset.id] = first
        status = PASS if first <= target else WARN if first <= backtest else FAIL
        report.add(
            name,
            "history_start",
            status,
            f"returns from {first.date()} (target {target.date()}, backtest needs {backtest.date()})",
            asset.id,
        )
        missing = pd.date_range(first, last, freq="ME").difference(pd.DatetimeIndex(g["date"]))
        detail = f"{len(missing)} missing months"
        if len(missing):
            detail += f": {[d.date().isoformat() for d in missing[:5]]}"
        report.add(name, "continuity", FAIL if len(missing) else PASS, detail, asset.id)
        report.add(
            name,
            "freshness",
            PASS if last >= expected_last else WARN,
            f"last month {last.date()} (expected {expected_last.date()})",
            asset.id,
        )
        big = g[g["ret"].abs() > h.max_abs_monthly_return]
        report.add(
            name,
            "return_outliers",
            WARN if len(big) else PASS,
            f"{len(big)} months with |return| > {h.max_abs_monthly_return:.0%}",
            asset.id,
        )
        mix = g.groupby("source", observed=True)["date"].agg(["min", "max", "count"])
        coverage[asset.id] = {
            "start": first.date().isoformat(),
            "sources": {
                str(src): f"{row['min'].date()}..{row['max'].date()} ({row['count']} months)"
                for src, row in mix.sort_values("min").iterrows()
            },
        }
    report.info["asset_history"] = coverage
    if starts:
        limiting = max(starts, key=starts.get)
        report.info["common_history_start"] = starts[limiting].date().isoformat()
        report.info["common_history_limited_by"] = limiting


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
        report.add(
            name,
            "freshness",
            _age_status(age, allowed),
            f"latest survey {dates.iloc[-1].date()} ({age}d ago)",
            var,
        )


# --------------------------------------------------------------- as-of coverage (decision 60)
# The `as_of` date is an information cutoff, not a timestamp: every DataStore query filters on
# `available_from`, so it decides what the agents are allowed to know. Nothing checked that the
# lake actually *reaches* that date, so a run with `as_of` set to today against a lake two months
# behind silently produced September numbers in a run header asserting November -- no error, and
# every narrative discussing "current" conditions out of date. A paid run is the worst place to
# discover that, so it is checked before one starts.
class StaleLakeError(RuntimeError):
    """The data lake does not reach the run's as-of date."""


# A month-end release lag: the panel may legitimately lack the month that just ended for a few
# days while sources publish. Beyond that, a missing month is missing data, not a release lag.
MONTH_END_GRACE_DAYS = 7


@dataclass(frozen=True)
class AsOfCoverage:
    """How far the lake's usable data reaches against a run's information cutoff."""

    as_of: date
    latest_month: date | None
    expected_month: date
    months_missing: int
    stale: bool
    detail: str


def asof_coverage(returns_last_month: date | None, as_of: date) -> AsOfCoverage:
    """Compare the spliced return panel's last month against the last month `as_of` implies.

    The test is not a day count but "does the panel reach the last complete month end before
    `as_of`" -- the exact question, with no threshold to argue about. The monthly panel is the
    binding series: the covariance matrix, every backtest and the momentum signals are built
    from it, so if it stops short the whole run is as of that earlier month whatever the header
    says. Within `MONTH_END_GRACE_DAYS` of a month end the just-ended month is not yet expected.
    """
    expected = last_complete_month_end(pd.Timestamp(as_of))
    if (pd.Timestamp(as_of) - expected).days <= MONTH_END_GRACE_DAYS:
        expected = last_complete_month_end(expected)
    expected_date = expected.date()

    if returns_last_month is None:
        return AsOfCoverage(
            as_of=as_of,
            latest_month=None,
            expected_month=expected_date,
            months_missing=-1,
            stale=True,
            detail="the spliced return panel is empty; run `uv run saa-data ingest`",
        )

    missing = 0
    cursor = expected
    while cursor.date() > returns_last_month:
        missing += 1
        cursor = last_complete_month_end(cursor)
    stale = missing > 0
    if stale:
        detail = (
            f"monthly returns reach {returns_last_month}, but an as-of of {as_of} expects "
            f"{expected_date}: {missing} month(s) missing. This run would be as of "
            f"{returns_last_month} in all but its header. Run `uv run saa-data ingest`, or "
            f"pass --as-of {returns_last_month} to say so plainly."
        )
    else:
        detail = f"monthly returns reach {returns_last_month}, covering an as-of of {as_of}"
    return AsOfCoverage(
        as_of=as_of,
        latest_month=returns_last_month,
        expected_month=expected_date,
        months_missing=missing,
        stale=stale,
        detail=detail,
    )


def check_asof_coverage(store, as_of: date, *, allow_stale: bool = False) -> AsOfCoverage:
    """Raise unless the lake reaches `as_of`. `allow_stale` downgrades it to a warning."""
    panel = store.returns()
    last = None
    if not panel.empty:
        ends = [panel[c].dropna().index.max() for c in panel.columns]
        ends = [e for e in ends if e is not None and not pd.isna(e)]
        if ends:
            last = min(ends).date()  # usable only as far as the shortest column reaches
    coverage = asof_coverage(last, as_of)
    if coverage.stale and not allow_stale:
        raise StaleLakeError(coverage.detail)
    if coverage.stale:
        log.warning("stale lake, continuing on --allow-stale: %s", coverage.detail)
    return coverage

"""Group-level US equity valuation from firm-level CRSP, Compustat and I/B/E/S data.

The ETFs report only today's P/E and yield, and only Shiller covers history, and only for the
S&P 500. This module rebuilds, month by month, the payout, earnings and book yields of
rule-based stand-ins for each US equity asset class:

    us_large_cap   the largest ``large_n`` common stocks by market cap (S&P 500 stand-in)
    us_value       the largest ``style_n`` stocks with book-to-market above that month's median
    us_growth      the largest ``style_n`` stocks with book-to-market at or below it
    us_small_cap   ranks ``style_n`` + 1 .. ``small_n`` (Russell 2000 stand-in)
    reits          every REIT

Yields are aggregate ratios (sum over firms / sum of market caps), i.e. cap-weighted, as an
index is. Fundamentals count only ``lag_months`` after the fiscal year ends, so each month sees
what was public then. Pure pandas: the WRDS source does the queries and calls
``aggregate_equity_valuation``. Firm-level inputs are licensed and never stored; only these
aggregates are written to the (git-ignored) lake.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

GROUPS = ("us_large_cap", "us_small_cap", "us_value", "us_growth", "reits")
FLOWS = ("dvc", "prstkc", "sstk", "ib")  # annual $m flows summed per group


@dataclass(frozen=True)
class GroupRules:
    large_n: int = 500
    style_n: int = 1000
    small_n: int = 3000
    lag_months: int = 6  # fiscal year-end to public availability (Fama-French convention)
    max_age_months: int = 18  # older fundamentals are treated as missing


def _month_end(values) -> pd.Series:
    return pd.to_datetime(values) + pd.offsets.MonthEnd(0)


def link_fundamentals(fundamentals: pd.DataFrame, links: pd.DataFrame) -> pd.DataFrame:
    """Attach a CRSP permno to each Compustat annual record via the CCM link table (the link
    must be active on the fiscal year-end). Missing payout flows count as zero, as is standard:
    Compustat leaves them blank when a firm paid nothing."""
    f = fundamentals.merge(links, on="gvkey", how="inner")
    end = f["linkenddt"].fillna(pd.Timestamp.max)
    f = f[(f["datadate"] >= f["linkdt"]) & (f["datadate"] <= end)].copy()
    for col in FLOWS:
        f[col] = f[col].fillna(0.0)
    f["be"] = f["ceq"] + f["txditc"].fillna(0.0)
    return f.sort_values(["permno", "datadate"]).drop_duplicates(
        ["permno", "datadate"], keep="last"
    )


def attach_fundamentals(
    panel: pd.DataFrame, fundamentals: pd.DataFrame, rules: GroupRules
) -> pd.DataFrame:
    """For each firm-month, the latest fundamentals that were public by that month end."""
    f = fundamentals.copy()
    f["available"] = _month_end(f["datadate"] + pd.DateOffset(months=rules.lag_months))
    f = f.sort_values("available")
    p = panel.sort_values("date")
    merged = pd.merge_asof(
        p,
        f[["permno", "available", "datadate", "be", *FLOWS]],
        left_on="date",
        right_on="available",
        by="permno",
        direction="backward",
    )
    stale = merged["datadate"] < merged["date"] - pd.DateOffset(months=rules.max_age_months)
    merged.loc[stale, ["be", *FLOWS]] = np.nan
    merged["has_fundamentals"] = merged["dvc"].notna()  # flows are zero-filled when present
    return merged


def assign_groups(firms: pd.DataFrame, rules: GroupRules) -> pd.DataFrame:
    """One row per (firm, month, group); a firm can sit in several groups (large and value)."""
    reit = firms["issuertype"] == "REIT"
    common = firms[~reit].copy()
    common["rank"] = common.groupby("date")["mcap"].rank(ascending=False, method="first")
    top = common[common["rank"] <= rules.style_n].copy()
    top["bm"] = top["be"] / top["mcap"]
    has_bm = top["bm"].notna() & (top["be"] > 0)
    median = top[has_bm].groupby("date")["bm"].transform("median")
    top["median_bm"] = median.reindex(top.index)

    parts = [
        common[common["rank"] <= rules.large_n].assign(group="us_large_cap"),
        common[(common["rank"] > rules.style_n) & (common["rank"] <= rules.small_n)].assign(
            group="us_small_cap"
        ),
        top[has_bm & (top["bm"] > top["median_bm"])].assign(group="us_value"),
        top[has_bm & (top["bm"] <= top["median_bm"])].assign(group="us_growth"),
        firms[reit].assign(group="reits"),
    ]
    return pd.concat(parts, ignore_index=True)


def _cap_weighted(values: pd.Series, caps: pd.Series) -> float:
    ok = values.notna()
    return float((values[ok] * caps[ok]).sum() / caps[ok].sum()) if ok.any() else np.nan


def _summarise(g: pd.DataFrame) -> pd.Series:
    total = g["mcap"].sum()
    covered = g[g["has_fundamentals"]]
    cap = covered["mcap"].sum()

    def ratio(col: str) -> float:
        return float(covered[col].sum() / cap) if cap > 0 else np.nan

    ltg = g["ltg_pct"] if "ltg_pct" in g else pd.Series(np.nan, index=g.index)
    div, buy, issue = ratio("dvc"), ratio("prstkc"), ratio("sstk")
    return pd.Series(
        {
            "n_firms": len(g),
            "market_cap_musd": total,
            "fundamentals_coverage_pct": 100 * cap / total if total > 0 else np.nan,
            "dividend_yield_pct": 100 * div,
            "buyback_yield_pct": 100 * buy,
            "issuance_yield_pct": 100 * issue,
            "net_payout_yield_pct": 100 * (div + buy - issue),
            "earnings_yield_pct": 100 * ratio("ib"),
            "book_to_price": ratio("be"),
            "ltg_pct": _cap_weighted(ltg, g["mcap"]),
            "ltg_coverage_pct": 100 * g.loc[ltg.notna(), "mcap"].sum() / total if total else np.nan,
        }
    )


def aggregate_equity_valuation(
    panel: pd.DataFrame,
    fundamentals: pd.DataFrame,
    links: pd.DataFrame,
    ltg: pd.DataFrame | None = None,
    rules: GroupRules | None = None,
) -> pd.DataFrame:
    """Monthly valuation per group.

    panel         permno, date (month end), mcap ($m), issuertype ("REIT" or other)
    fundamentals  gvkey, datadate, dvc, prstkc, sstk, ib, ceq, txditc (Compustat, $m)
    links         gvkey, permno, linkdt, linkenddt (CCM; null end = still linked)
    ltg           permno, date, ltg_pct (I/B/E/S median long-term growth), optional
    """
    rules = rules or GroupRules()
    panel = panel.assign(date=_month_end(panel["date"]))
    linked = link_fundamentals(fundamentals, links)
    firms = attach_fundamentals(panel, linked, rules)
    if ltg is not None and not ltg.empty:
        latest = (
            ltg.assign(date=_month_end(ltg["date"]))
            .sort_values("date")
            .drop_duplicates(["permno", "date"], keep="last")
        )
        firms = firms.merge(
            latest[["permno", "date", "ltg_pct"]], on=["permno", "date"], how="left"
        )
    grouped = assign_groups(firms, rules)
    out = grouped.groupby(["group", "date"])[list(grouped.columns)].apply(_summarise).reset_index()
    out["n_firms"] = out["n_firms"].astype("int64")
    return out.sort_values(["group", "date"]).reset_index(drop=True)

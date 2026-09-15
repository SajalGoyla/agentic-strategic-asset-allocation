"""Long-history monthly total returns for the 18 IPS asset classes.

ETF histories start between 1993 and 2010, but the paper uses data from 1990 and backtests
1996-2026. For each asset, monthly returns are taken from the ETF where it has a month-end
price, and otherwise from the first available link in the asset's ``history`` chain in
``config/universe.yaml`` (index/active mutual funds, futures, French library portfolios,
synthetic par-bond returns from FRED yields, World Bank prices). Every month records its source,
and every link is scored against the ETF over their overlap (correlation, tracking error, mean
difference) so agents can weigh proxy quality. Returns are spliced as-is: no rescaling.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from saa.config import Asset, Config, HistorySource
from saa.data.lake import DataLake
from saa.data.sources.fred import period_end
from saa.data.store import latest_vintage

log = logging.getLogger(__name__)

RETURNS = "market/asset_returns_monthly"
LINKS = "market/asset_history_links"
_INPUTS = (
    "market/prices_daily",
    "factors/french",
    "macro/fred_observations",
    "commodities/worldbank_monthly",
    "wrds/crsp_treasury_indexes",
    "wrds/crsp_stock_monthly",
    "wrds/crsp_fund_monthly",
)
_EMPTY = pd.Series(dtype="float64", index=pd.DatetimeIndex([], name="date"))


def last_complete_month_end(today: pd.Timestamp | None = None) -> pd.Timestamp:
    today = pd.Timestamp(today if today is not None else pd.Timestamp.today()).normalize()
    return pd.Timestamp(today.year, today.month, 1) - pd.Timedelta(days=1)


def _month_end_values(series: pd.Series, tolerance_days: int) -> pd.Series:
    """Last value in each calendar month, kept only if observed within the tolerance of month end."""
    series = series.dropna().sort_index()
    if series.empty:
        return _EMPTY
    last_value = series.resample("ME").last()
    last_seen = series.index.to_series().resample("ME").last()
    fresh = (pd.Series(last_seen.index, index=last_seen.index) - last_seen) <= pd.Timedelta(
        days=tolerance_days
    )
    return last_value.where(fresh)


def monthly_from_daily(prices: pd.DataFrame, ticker: str, tolerance_days: int = 7) -> pd.Series:
    g = prices.loc[prices["ticker"] == ticker, ["date", "adj_close"]]
    if g.empty:
        raise KeyError(f"no prices for {ticker}")
    px = _month_end_values(g.set_index("date")["adj_close"], tolerance_days)
    return px.pct_change(fill_method=None).dropna()


def french_returns(french: pd.DataFrame, link: HistorySource) -> pd.Series:
    wide = french[french["dataset"] == link.dataset].pivot(
        index="date", columns="factor", values="value"
    )
    missing = [c for c in link.columns if c not in wide.columns]
    if missing:
        raise KeyError(f"columns {missing} not in {link.dataset}")
    sub = wide[link.columns]
    combined = sub.sum(axis=1) if link.combine == "sum" else sub.mean(axis=1)
    return combined[sub.notna().all(axis=1)]


def par_bond_price(coupon, yld, maturity_years: float):
    """Price per 1 face of a semi-annual bond (vectorised; fractional periods allowed)."""
    n = 2 * maturity_years
    c, y = np.asarray(coupon) / 2, np.asarray(yld) / 2
    discount = (1 + y) ** -n
    safe_y = np.where(np.abs(y) < 1e-10, 1.0, y)
    annuity = np.where(np.abs(y) < 1e-10, n, (1 - discount) / safe_y)
    return c * annuity + discount


def par_bond_returns(yields_pct: pd.Series, maturity_years: float) -> pd.Series:
    """Monthly total return of buying a par bond at last month's yield and repricing it one
    month later at this month's yield (coupon accrual + price change)."""
    y = yields_pct.astype(float) / 100
    prev = y.shift(1)
    price = par_bond_price(prev, y, maturity_years - 1 / 12)
    return pd.Series(price - 1 + prev / 12, index=y.index).dropna()


def fred_yield_returns(
    fred: pd.DataFrame,
    link: HistorySource,
    tolerance_days: int,
    frequencies: dict[str, str] | None = None,
) -> pd.Series:
    """Par-bond returns from FRED yields. Daily/weekly series use the last value near month
    end; monthly/quarterly series (stamped at period start) are rolled to period end first."""
    frequencies = frequencies or {}
    obs = latest_vintage(fred[fred["series_id"].isin(link.series)])
    wide = obs.pivot(index="date", columns="series_id", values="value")
    missing = [s for s in link.series if s not in wide.columns]
    if missing:
        raise KeyError(f"FRED series {missing} not ingested")
    columns = {}
    for s in link.series:
        values = wide[s].dropna()
        if frequencies.get(s, "d") in ("m", "q", "a"):
            values.index = period_end(pd.Series(values.index), frequencies[s]).to_numpy()
        columns[s] = _month_end_values(values, tolerance_days)
    month_end = pd.concat(columns, axis=1)
    avg = month_end.mean(axis=1)[month_end.notna().all(axis=1)]
    return par_bond_returns(avg, float(link.maturity_years))


def worldbank_returns(worldbank: pd.DataFrame, link: HistorySource) -> pd.Series:
    s = worldbank.loc[worldbank["series"] == link.commodity].set_index("date")["value"]
    if s.empty:
        raise KeyError(f"World Bank series {link.commodity!r} not ingested")
    return s.sort_index().pct_change(fill_method=None).dropna()


def crsp_treasury_returns(indexes: pd.DataFrame, link: HistorySource) -> pd.Series:
    """Mean of CRSP fixed-term index returns (e.g. b7ret and b10ret for a 7-10y ETF)."""
    wide = indexes.pivot(index="date", columns="series", values="ret")
    missing = [c for c in link.columns if c not in wide.columns]
    if missing:
        raise KeyError(f"CRSP Treasury series {missing} not ingested")
    sub = wide[link.columns]
    return sub.mean(axis=1)[sub.notna().all(axis=1)]


def crsp_stock_returns(stocks: pd.DataFrame, link: HistorySource) -> pd.Series:
    s = stocks.loc[stocks["permno"] == link.permno].set_index("date")["ret"]
    if s.empty:
        raise KeyError(f"CRSP permno {link.permno} not ingested")
    return s.sort_index().dropna()


def crsp_fund_returns(funds: pd.DataFrame, link: HistorySource) -> pd.Series:
    s = funds.loc[funds["ticker"] == link.ticker].set_index("date")["ret"]
    if s.empty:
        raise KeyError(f"CRSP fund {link.ticker} not ingested")
    return s.sort_index().dropna()


def splice(series: list[pd.Series]) -> pd.DataFrame:
    """Per month, take the first series (by priority) that has a value."""
    combined = pd.concat([s.rename(i) for i, s in enumerate(series)], axis=1, sort=True)
    combined = combined[combined.notna().any(axis=1)]
    values = combined.to_numpy()
    pick = np.isfinite(values).argmax(axis=1)
    return pd.DataFrame(
        {"ret": values[np.arange(len(values)), pick], "priority": pick}, index=combined.index
    )


def _link_returns(link: HistorySource, inputs: dict, config: Config) -> pd.Series:
    tolerance = config.settings.history.month_end_tolerance_days
    if link.source == "yahoo":
        return monthly_from_daily(
            _require(inputs, "market/prices_daily"), str(link.ticker), tolerance
        )
    if link.source == "french":
        return french_returns(_require(inputs, "factors/french"), link)
    if link.source == "par_bond":
        frequencies = {s.id: s.frequency for s in config.macro.series}
        return fred_yield_returns(
            _require(inputs, "macro/fred_observations"), link, tolerance, frequencies
        )
    if link.source == "crsp_treasury":
        return crsp_treasury_returns(_require(inputs, "wrds/crsp_treasury_indexes"), link)
    if link.source == "crsp_stock":
        return crsp_stock_returns(_require(inputs, "wrds/crsp_stock_monthly"), link)
    if link.source == "crsp_fund":
        return crsp_fund_returns(_require(inputs, "wrds/crsp_fund_monthly"), link)
    return worldbank_returns(_require(inputs, "commodities/worldbank_monthly"), link)


def _require(inputs: dict, name: str) -> pd.DataFrame:
    if inputs.get(name) is None:
        raise KeyError(f"{name} not ingested")
    return inputs[name]


def _lag_days(link: HistorySource, config: Config) -> int:
    s = config.settings
    return {
        "yahoo": 1,
        "par_bond": 1,
        "french": s.french.release_lag_days,
        "worldbank": s.worldbank.release_lag_days,
        "crsp_treasury": s.wrds.release_lag_days,
        "crsp_stock": s.wrds.release_lag_days,
        "crsp_fund": s.wrds.release_lag_days,
    }[link.source]


def _asset_history(
    asset: Asset, inputs: dict, config: Config, cutoff: pd.Timestamp, notes: list[str]
) -> tuple[pd.DataFrame, list[dict]]:
    earliest = pd.Timestamp(config.settings.history.earliest)
    chain = [HistorySource(source="yahoo", ticker=asset.ticker, kind="etf"), *asset.history]
    series = []
    for link in chain:
        try:
            r = _link_returns(link, inputs, config)
        except (KeyError, ValueError) as exc:
            notes.append(f"{asset.id}: {link.label} unavailable ({exc})")
            r = _EMPTY
        series.append(r[(r.index >= earliest) & (r.index <= cutoff)])

    spliced = splice(series)
    spliced["date"] = spliced.index
    spliced["asset_id"] = asset.id
    spliced["source"] = [chain[p].label for p in spliced["priority"]]
    spliced["kind"] = [chain[p].kind for p in spliced["priority"]]
    lags = [_lag_days(chain[p], config) for p in spliced["priority"]]
    spliced["available_from"] = spliced["date"] + pd.to_timedelta(lags, unit="D")

    etf = series[0]
    links = []
    for p, (link, r) in enumerate(zip(chain, series, strict=True)):
        row = {
            "asset_id": asset.id,
            "priority": p,
            "source": link.label,
            "kind": link.kind,
            "first_date": r.index.min() if len(r) else pd.NaT,
            "last_date": r.index.max() if len(r) else pd.NaT,
            "months_used": int((spliced["priority"] == p).sum()),
            "overlap_months": 0,
            "corr": np.nan,
            "tracking_error": np.nan,
            "mean_diff": np.nan,
        }
        if p > 0:
            both = pd.concat([etf, r], axis=1, keys=["etf", "proxy"]).dropna()
            row["overlap_months"] = len(both)
            if len(both) >= 12:
                diff = both["etf"] - both["proxy"]
                row["corr"] = float(both["etf"].corr(both["proxy"]))
                row["tracking_error"] = float(diff.std() * np.sqrt(12))
                row["mean_diff"] = float(diff.mean() * 12)
        links.append(row)
    return spliced.reset_index(drop=True), links


def build_history(
    config: Config, lake: DataLake, today: pd.Timestamp | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Return (monthly returns, link diagnostics, notes) for every asset in the universe."""
    cutoff = last_complete_month_end(today)
    inputs = {name: lake.read_dataset(name) if lake.has_dataset(name) else None for name in _INPUTS}
    notes: list[str] = []
    returns, links = [], []
    for asset in config.universe.assets:
        asset_returns, asset_links = _asset_history(asset, inputs, config, cutoff, notes)
        if asset_returns.empty:
            notes.append(f"{asset.id}: no return history could be built")
            continue
        returns.append(asset_returns)
        links.extend(asset_links)
        log.info(
            "history %-24s %s..%s", asset.id, asset_returns["date"].min().date(), cutoff.date()
        )
    return pd.concat(returns, ignore_index=True), pd.DataFrame(links), notes

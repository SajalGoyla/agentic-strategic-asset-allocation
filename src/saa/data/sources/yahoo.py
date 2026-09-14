"""Yahoo Finance connector (via yfinance): daily prices/distributions and ETF fundamentals.

Yahoo is free but unofficial and occasionally returns empty responses, so every ticker is
retried. The fund snapshot is *current* data only; because it is appended every run it builds
a point-in-time valuation history going forward.
"""

from __future__ import annotations

import logging
import math
import time

import pandas as pd
import yfinance as yf

from saa.data.sources.base import FetchResult, Source

log = logging.getLogger(__name__)

PRICES = "market/prices_daily"
SNAPSHOT = "market/fund_snapshot"

PRICE_COLUMNS = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
    "Dividends": "dividends",
    "Stock Splits": "splits",
    "Capital Gains": "capital_gains",
}
_ACTION_COLUMNS = {"dividends", "splits", "capital_gains"}


def normalize_history(hist: pd.DataFrame, ticker: str) -> pd.DataFrame:
    df = hist.rename(columns=PRICE_COLUMNS)
    for col in PRICE_COLUMNS.values():
        if col not in df.columns:
            df[col] = 0.0 if col in _ACTION_COLUMNS else math.nan
    index = pd.DatetimeIndex(hist.index)
    if index.tz is not None:
        index = index.tz_localize(None)  # keep exchange-local calendar date
    df.index = index.normalize()
    df = df[~df.index.duplicated(keep="last")]
    df = df.reset_index(names="date")
    df["ticker"] = ticker
    return df[["date", "ticker", *PRICE_COLUMNS.values()]]


def _num(value) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return math.nan
    return value if math.isfinite(value) else math.nan


def _holding(frame: pd.DataFrame | None, label: str) -> float:
    try:
        value = _num(frame.loc[label].iloc[0])
    except (AttributeError, KeyError, IndexError):
        return math.nan
    return value if value > 0 else math.nan


def fund_snapshot(tk: yf.Ticker, ticker: str, snapshot_date: pd.Timestamp) -> dict:
    info = tk.info or {}
    equity = bonds = None
    try:
        funds = tk.funds_data
        equity, bonds = funds.equity_holdings, funds.bond_holdings
    except Exception:  # not a fund, or Yahoo has no holdings data
        pass
    return {
        "snapshot_date": snapshot_date,
        "ticker": ticker,
        "quote_type": info.get("quoteType"),
        "total_assets": _num(info.get("totalAssets")),
        "expense_ratio_pct": _num(info.get("netExpenseRatio")),
        "trailing_pe": _num(info.get("trailingPE")),
        "distribution_yield": _num(info.get("yield")),
        # Yahoo reports holdings valuation as inverse ratios (E/P, B/P)
        "earnings_yield": _holding(equity, "Price/Earnings"),
        "book_to_price": _holding(equity, "Price/Book"),
        "duration_years": _holding(bonds, "Duration"),
        "maturity_years": _holding(bonds, "Maturity"),
    }


class YahooSource(Source):
    name = "yahoo"

    def fetch(self) -> FetchResult:
        cfg = self.settings.yahoo
        universe = self.config.universe
        tickers = universe.all_tickers()
        result = FetchResult(self.name, expected_entities={PRICES: set(tickers)})
        today = pd.Timestamp.today().normalize()

        frames, snapshots = [], []
        for ticker in tickers:
            try:
                frame = normalize_history(self._history(ticker), ticker)
                frames.append(frame)
                log.info("yahoo %-6s %6d rows from %s", ticker, len(frame), frame["date"].min().date())
            except Exception as exc:
                result.warnings.append(f"{ticker}: price download failed ({exc})")
            if cfg.fund_snapshot and ticker in universe.tickers:
                try:
                    snapshots.append(fund_snapshot(yf.Ticker(ticker), ticker, today))
                except Exception as exc:
                    result.warnings.append(f"{ticker}: fund snapshot failed ({exc})")
            time.sleep(cfg.pause_s)

        if frames:
            result.tables[PRICES] = pd.concat(frames, ignore_index=True)
        if snapshots:
            result.tables[SNAPSHOT] = pd.DataFrame(snapshots)
        return result

    def _history(self, ticker: str) -> pd.DataFrame:
        cfg = self.settings.yahoo
        last_error: object = None
        for attempt in range(cfg.max_retries):
            try:
                hist = yf.Ticker(ticker).history(
                    period="max", interval="1d", auto_adjust=False, actions=True
                )
                if not hist.empty:
                    return hist
                last_error = "empty response"
            except Exception as exc:
                last_error = exc
            time.sleep(cfg.pause_s * 2**attempt)
        raise RuntimeError(f"no data after {cfg.max_retries} attempts: {last_error}")

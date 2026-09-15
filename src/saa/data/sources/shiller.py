"""Robert Shiller's U.S. stock market data (S&P 500 price, dividends, earnings, CAPE).

Inputs for the Inverse Gordon (dividend yield + earnings growth) and CAPE-implied ERP CMA
methods. The canonical file moved from Yale (frozen at 2023-09) to shillerdata.com, whose
download link carries a version token, so the current link is discovered from the homepage.
"""

from __future__ import annotations

import html
import io
import logging
import re

import numpy as np
import pandas as pd

from saa.data.http import get
from saa.data.sources.base import FetchResult, Source

log = logging.getLogger(__name__)

DATASET = "valuation/shiller_us_equity"
_LINK = re.compile(r'href="([^"]*ie_data\.xls[^"]*)"', re.IGNORECASE)

# column position -> (expected header in the "Date" row, output name)
_LAYOUT = {
    0: ("Date", "date_code"),
    1: ("P", "price"),
    2: ("D", "dividend"),
    3: ("E", "earnings"),
    4: ("CPI", "cpi"),
    6: ("Rate GS10", "gs10"),
    7: ("Price", "real_price"),
    8: ("Dividend", "real_dividend"),
    10: ("Earnings", "real_earnings"),
    12: ("CAPE", "cape"),
    14: ("TR CAPE", "tr_cape"),
    16: ("Yield", "excess_cape_yield"),
}


def discover_download_url(homepage_html: str) -> str | None:
    match = _LINK.search(homepage_html)
    if not match:
        return None
    url = html.unescape(match.group(1))
    return "https:" + url if url.startswith("//") else url


def shiller_dates(codes: pd.Series) -> pd.Series:
    """Shiller encodes months as decimals: 1871.01 = Jan 1871, 1871.1 = Oct 1871."""
    codes = codes.astype(float)
    year = np.floor(codes).astype(int)
    month = np.rint((codes - year) * 100).astype(int)
    starts = pd.to_datetime(pd.DataFrame({"year": year, "month": month, "day": 1}))
    return starts + pd.offsets.MonthEnd(0)


def parse_shiller_xls(content: bytes, release_lag_days: int) -> pd.DataFrame:
    raw = pd.read_excel(io.BytesIO(content), sheet_name="Data", header=None)
    first_col = raw.iloc[:, 0].astype(str).str.strip()
    header_rows = raw.index[first_col == "Date"]
    if len(header_rows) == 0:
        raise ValueError("Shiller layout changed: no 'Date' header row")
    header = raw.loc[header_rows[0]].astype(str).str.strip()
    for pos, (label, _) in _LAYOUT.items():
        if not header.iloc[pos].startswith(label):
            raise ValueError(
                f"Shiller layout changed: column {pos} is {header.iloc[pos]!r}, expected {label!r}"
            )
    body = raw.loc[header_rows[0] + 1 :]
    body = body[pd.to_numeric(body.iloc[:, 0], errors="coerce").notna()]
    df = body[list(_LAYOUT)].apply(pd.to_numeric, errors="coerce")
    df.columns = [name for _, name in _LAYOUT.values()]
    df["date"] = shiller_dates(df.pop("date_code")).to_numpy()
    df["available_from"] = df["date"] + pd.Timedelta(days=release_lag_days)
    return df.reset_index(drop=True)


class ShillerSource(Source):
    name = "shiller"

    def fetch(self) -> FetchResult:
        cfg = self.settings.shiller
        timeout = self.settings.http.timeout_s
        result = FetchResult(self.name)
        url = None
        try:
            url = discover_download_url(get(self.session, cfg.homepage, timeout=timeout).text)
        except Exception as exc:
            result.warnings.append(f"could not read {cfg.homepage} ({exc})")
        if url is None:
            url = cfg.fallback_url
            result.warnings.append(f"download link not found on homepage; using fallback {url}")

        content = get(self.session, url, timeout=timeout).content
        result.raw["ie_data.xls"] = content
        df = parse_shiller_xls(content, cfg.release_lag_days)
        result.tables[DATASET] = df
        log.info("shiller: %d months, last %s (from %s)", len(df), df["date"].max().date(), url)
        return result

"""World Bank Commodity Price Data ("Pink Sheet"): monthly commodity prices since 1960.

Used for gold history before gold futures data begins (2000). Prices are monthly averages, so
returns built from them are slightly smoother than month-end returns. The download link carries
a document token that changes with each monthly release, so it is discovered from the
commodity-markets page, with the last known link as fallback.
"""

from __future__ import annotations

import html
import io
import logging
import re
import warnings

import pandas as pd

from saa.data.http import get
from saa.data.sources.base import FetchResult, Source

log = logging.getLogger(__name__)

DATASET = "commodities/worldbank_monthly"
_LINK = re.compile(r'href="([^"]*CMO-Historical-Data-Monthly\.xlsx[^"]*)"', re.IGNORECASE)
_PERIOD = re.compile(r"^\d{4}M\d{2}$")


def discover_download_url(page_html: str) -> str | None:
    match = _LINK.search(page_html)
    return html.unescape(match.group(1)) if match else None


def parse_worldbank_prices(content: bytes, release_lag_days: int) -> pd.DataFrame:
    """Long frame of the "Monthly Prices" sheet: commodity names sit two rows above the first
    ``YYYYMmm`` data row and units one row above."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # openpyxl styling warnings
        raw = pd.read_excel(io.BytesIO(content), sheet_name="Monthly Prices", header=None)
    codes = raw.iloc[:, 0].astype(str).str.strip()
    is_data = codes.str.match(_PERIOD)
    if not is_data.any():
        raise ValueError("World Bank layout changed: no YYYYMmm rows in 'Monthly Prices'")
    first = int(is_data.idxmax())
    names, units = raw.iloc[first - 2], raw.iloc[first - 1]
    body = raw.loc[is_data]
    dates = (pd.to_datetime(codes[is_data], format="%YM%m") + pd.offsets.MonthEnd(0)).to_numpy()

    frames = []
    for col in raw.columns[1:]:
        name = names[col]
        if not isinstance(name, str) or not name.strip():
            continue
        frames.append(
            pd.DataFrame(
                {
                    "series": name.strip().rstrip("*").strip(),
                    "unit": str(units[col]).strip(),
                    "date": dates,
                    "value": pd.to_numeric(body[col], errors="coerce").to_numpy(),
                }
            )
        )
    df = pd.concat(frames, ignore_index=True).dropna(subset=["value"])
    df = df.drop_duplicates(["series", "date"], keep="first")
    df["available_from"] = df["date"] + pd.Timedelta(days=release_lag_days)
    return df.reset_index(drop=True)


class WorldBankSource(Source):
    name = "worldbank"

    def fetch(self) -> FetchResult:
        cfg = self.settings.worldbank
        timeout = self.settings.http.timeout_s
        result = FetchResult(self.name)
        url = None
        try:
            url = discover_download_url(get(self.session, cfg.page, timeout=timeout).text)
        except Exception as exc:
            result.warnings.append(f"could not read {cfg.page} ({exc})")
        if url is None:
            url = cfg.fallback_url
            result.warnings.append(f"download link not found on page; using fallback {url}")

        content = get(self.session, url, timeout=timeout).content
        result.raw["CMO-Historical-Data-Monthly.xlsx"] = content
        df = parse_worldbank_prices(content, cfg.release_lag_days)
        result.tables[DATASET] = df
        log.info(
            "worldbank: %d series, last month %s", df["series"].nunique(), df["date"].max().date()
        )
        return result

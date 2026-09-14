"""U.S. Treasury daily par yield curves (nominal and real) from home.treasury.gov."""

from __future__ import annotations

import io
import logging
import re
from datetime import date

import pandas as pd

from saa.data.http import Throttle, get
from saa.data.sources.base import FetchResult, Source

log = logging.getLogger(__name__)

DATASET = "rates/treasury_par_curve"
_TENOR = re.compile(r"^\s*([\d.]+)\s*(mo|month|months|yr|year|years)\s*$", re.IGNORECASE)
_COLUMNS = ["curve", "date", "tenor", "tenor_months", "yield_pct"]


def tenor_months(label: str) -> float | None:
    match = _TENOR.match(str(label))
    if not match:
        return None
    n = float(match.group(1))
    return n if match.group(2).lower().startswith("mo") else n * 12


def tenor_label(months: float) -> str:
    return f"{months:g}M" if months < 12 else f"{months / 12:g}Y"


def parse_treasury_csv(text: str, curve: str) -> pd.DataFrame:
    """Column labels change across years ("1 Mo", "1.5 Month", "5 YR"); normalise to months."""
    if not text.strip():
        return pd.DataFrame(columns=_COLUMNS)
    df = pd.read_csv(io.StringIO(text))
    if df.empty or "Date" not in df.columns:
        return pd.DataFrame(columns=_COLUMNS)
    tenors = {c: tenor_months(c) for c in df.columns if c != "Date"}
    tenors = {c: m for c, m in tenors.items() if m is not None}
    long = df.melt(id_vars="Date", value_vars=list(tenors), var_name="label", value_name="yield_pct")
    long["yield_pct"] = pd.to_numeric(long["yield_pct"], errors="coerce")
    long = long.dropna(subset=["yield_pct"]).copy()
    long["date"] = pd.to_datetime(long["Date"], format="%m/%d/%Y")
    long["tenor_months"] = long["label"].map(tenors)
    long["tenor"] = long["tenor_months"].map(tenor_label)
    long["curve"] = curve
    return long[_COLUMNS]


class TreasurySource(Source):
    name = "treasury"

    def fetch(self) -> FetchResult:
        cfg = self.settings.treasury
        throttle = Throttle(cfg.min_request_interval_s)
        result = FetchResult(self.name, expected_entities={DATASET: set(cfg.curves)})
        frames = []
        for curve, spec in cfg.curves.items():
            curve_frames, failed = [], []
            for year in range(spec.start_year, date.today().year + 1):
                params = {
                    "type": spec.type,
                    "field_tdr_date_value": year,
                    "page": "",
                    "_format": "csv",
                }
                try:
                    text = get(
                        self.session,
                        f"{cfg.base_url}/{year}/all",
                        params=params,
                        timeout=self.settings.http.timeout_s,
                        throttle=throttle,
                    ).text
                    curve_frames.append(parse_treasury_csv(text, curve))
                except Exception as exc:
                    failed.append(f"{year}: {exc}")
                    continue
                result.raw[f"{curve}_{year}.csv"] = text.encode("utf-8")
            if failed:
                # An incomplete curve would silently shorten history; keep the previous version.
                result.warnings.append(f"{curve}: curve dropped, {len(failed)} years failed: {failed[:3]}")
                continue
            frames.extend(curve_frames)
            log.info("treasury %s: %d years", curve, len(curve_frames))
        if frames:
            result.tables[DATASET] = pd.concat(frames, ignore_index=True)
        return result

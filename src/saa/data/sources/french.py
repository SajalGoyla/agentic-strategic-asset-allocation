"""Kenneth French Data Library connector (zipped CSV files)."""

from __future__ import annotations

import io
import logging
import re
import zipfile

import pandas as pd

from saa.data.http import get
from saa.data.sources.base import FetchResult, Source

log = logging.getLogger(__name__)

DATASET = "factors/french"
_DATE_CODE = re.compile(r"^(\d{6}|\d{8})$")
_MISSING = (-99.99, -999.0)


def parse_french_csv(text: str) -> pd.DataFrame:
    """Return the first monthly (YYYYMM) or daily (YYYYMMDD) table of a French CSV file as a
    wide frame of decimal returns indexed by date. Later blocks (annual returns, firm counts,
    equal-weighted variants) are ignored."""
    header: list[str] | None = None
    rows: list[list[str]] = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.split(",")]
        while len(cells) > 1 and cells[-1] == "":
            cells.pop()
        if header is not None and _DATE_CODE.match(cells[0]) and len(cells) == len(header) + 1:
            rows.append(cells)
            continue
        if rows:
            break
        if len(cells) > 1 and cells[0] == "" and all(cells[1:]):
            header = cells[1:]
    if not rows:
        raise ValueError("no monthly or daily table found")

    codes = [r[0] for r in rows]
    values = pd.DataFrame([r[1:] for r in rows], columns=header).apply(
        pd.to_numeric, errors="coerce"
    )
    values = values.mask(values.isin(_MISSING)) / 100.0
    if len(codes[0]) == 6:
        index = pd.to_datetime(codes, format="%Y%m") + pd.offsets.MonthEnd(0)
    else:
        index = pd.to_datetime(codes, format="%Y%m%d")
    values.index = pd.DatetimeIndex(index, name="date")
    return values


def to_long(wide: pd.DataFrame, dataset: str, release_lag_days: int) -> pd.DataFrame:
    long = wide.reset_index().melt(id_vars="date", var_name="factor", value_name="value")
    long = long.dropna(subset=["value"])
    long["dataset"] = dataset
    long["available_from"] = long["date"] + pd.Timedelta(days=release_lag_days)
    return long


class FrenchSource(Source):
    name = "french"

    def fetch(self) -> FetchResult:
        cfg = self.settings.french
        result = FetchResult(self.name, expected_entities={DATASET: {d.name for d in cfg.datasets}})
        frames = []
        for ds in cfg.datasets:
            filename = f"{ds.name}_CSV.zip"
            try:
                content = get(
                    self.session, f"{cfg.base_url}/{filename}", timeout=self.settings.http.timeout_s
                ).content
                result.raw[filename] = content
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    member = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
                    text = zf.read(member).decode("latin-1")
                wide = parse_french_csv(text)
            except Exception as exc:
                result.warnings.append(f"{ds.name}: download/parse failed ({exc!r})")
                continue
            frames.append(to_long(wide, ds.name, cfg.release_lag_days))
            log.info(
                "french %-32s %s..%s", ds.name, wide.index.min().date(), wide.index.max().date()
            )
        if frames:
            result.tables[DATASET] = pd.concat(frames, ignore_index=True)
        return result

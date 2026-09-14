"""Philadelphia Fed Survey of Professional Forecasters (median level forecasts).

Supplies the "Survey/Analyst consensus" CMA method: 10-year expected returns for the S&P 500
(STOCK10), 10-year Treasuries (BOND10) and T-bills (BILL10), plus long-run inflation and growth.

Horizon codes (SPF convention): 1 = previous quarter (history), 2 = current quarter,
3-6 = next four quarters, A-D = annual averages for current year and next three years,
``point`` = single-value long-horizon variables such as CPI10.
"""

from __future__ import annotations

import io
import logging
import warnings

import pandas as pd

from saa.data.http import get
from saa.data.sources.base import FetchResult, Source

log = logging.getLogger(__name__)

DATASET = "surveys/spf_median"
_COLUMNS = ["variable", "survey_date", "horizon", "value", "available_from"]


def parse_spf_workbook(
    content: bytes, variables: list[str], release_lag_days: int
) -> tuple[pd.DataFrame, list[str]]:
    problems: list[str] = []
    frames = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # openpyxl warns about unparsable header/footer styling
        book = pd.ExcelFile(io.BytesIO(content))
        sheets = {v: book.parse(v) for v in variables if v in book.sheet_names}
    for var in variables:
        sheet = sheets.get(var)
        if sheet is None:
            problems.append(f"{var}: sheet not found in SPF workbook")
            continue
        value_cols = [c for c in sheet.columns if c not in ("YEAR", "QUARTER")]
        long = sheet.melt(
            id_vars=["YEAR", "QUARTER"], value_vars=value_cols, var_name="column", value_name="value"
        )
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long = long.dropna(subset=["value", "YEAR", "QUARTER"])
        if long.empty:
            problems.append(f"{var}: no values")
            continue
        suffix = long["column"].astype(str).str[len(var) :]
        long["horizon"] = suffix.where(suffix != "", "point")
        long["survey_date"] = pd.to_datetime(
            pd.DataFrame(
                {
                    "year": long["YEAR"].astype(int),
                    "month": (long["QUARTER"].astype(int) - 1) * 3 + 1,
                    "day": 1,
                }
            )
        )
        long["variable"] = var
        long["available_from"] = long["survey_date"] + pd.Timedelta(days=release_lag_days)
        frames.append(long[_COLUMNS])
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_COLUMNS)
    return df, problems


class SpfSource(Source):
    name = "spf"

    def fetch(self) -> FetchResult:
        cfg = self.settings.spf
        result = FetchResult(self.name, expected_entities={DATASET: set(cfg.variables)})
        content = get(self.session, cfg.url, timeout=self.settings.http.timeout_s).content
        result.raw["medianLevel.xlsx"] = content
        df, problems = parse_spf_workbook(content, cfg.variables, cfg.release_lag_days)
        result.warnings.extend(problems)
        if not df.empty:
            result.tables[DATASET] = df
            log.info("spf: %d rows, latest survey %s", len(df), df["survey_date"].max().date())
        return result

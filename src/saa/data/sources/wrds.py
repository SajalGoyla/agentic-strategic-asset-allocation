"""WRDS (CRSP) connector: licensed monthly returns that improve pre-ETF history.

Pulls CRSP fixed-term Treasury indexes, monthly returns for selected securities (the 18 ETFs for
cross-checking Yahoo, plus bullion-fund history links) and mutual fund returns for history links.
Skipped automatically when WRDS credentials are missing, so the pipeline still runs on public
data. Everything under ``wrds/`` is licensed to the account holder: never commit or publish it.
"""

from __future__ import annotations

import logging
import re

import pandas as pd

from saa.data.sources.base import FetchResult, Source
from saa.data.wrds_client import WrdsClient, credentials_problem

log = logging.getLogger(__name__)

TREASURY = "wrds/crsp_treasury_indexes"
STOCKS = "wrds/crsp_stock_monthly"
FUNDS = "wrds/crsp_fund_monthly"
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


def _month_end(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values) + pd.offsets.MonthEnd(0)


class WrdsSource(Source):
    name = "wrds"

    def fetch(self) -> FetchResult:
        cfg = self.settings.wrds
        result = FetchResult(self.name)
        if not cfg.enabled:
            result.skipped = "disabled in config/data_sources.yaml"
            return result
        problem = credentials_problem()
        if problem:
            result.skipped = problem
            return result

        universe = self.config.universe
        permnos = universe.crsp_permnos()
        tickers = universe.crsp_fund_tickers()
        result.expected_entities = {
            TREASURY: set(cfg.treasury_series),
            STOCKS: {str(p) for p in permnos},
            FUNDS: set(tickers),
        }
        with WrdsClient() as client:
            jobs = (
                (TREASURY, lambda: self._treasury(client)),
                (STOCKS, lambda: self._stocks(client, permnos)),
                (FUNDS, lambda: self._funds(client, tickers, result)),
            )
            for dataset, job in jobs:
                try:
                    df = job()
                except Exception as exc:
                    message = str(exc).strip().splitlines()[0]
                    result.warnings.append(f"{dataset}: query failed ({message})")
                    continue
                if not df.empty:
                    result.tables[dataset] = df
                    log.info("wrds %s: %d rows", dataset, len(df))
        return result

    def _stamp(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["available_from"] = df["date"] + pd.Timedelta(days=self.settings.wrds.release_lag_days)
        return df.reset_index(drop=True)

    def _treasury(self, client: WrdsClient) -> pd.DataFrame:
        columns = self.settings.wrds.treasury_series
        if not columns:
            return pd.DataFrame()
        invalid = [c for c in columns if not _IDENTIFIER.match(c)]
        if invalid:
            raise ValueError(f"invalid CRSP column names {invalid}")
        wide = client.query(f"select caldt, {', '.join(columns)} from crsp.mcti order by caldt")
        long = wide.melt(id_vars="caldt", var_name="series", value_name="ret")
        long = long.dropna(subset=["ret"])
        long["date"] = _month_end(long["caldt"])  # CRSP stamps the last trading day
        return self._stamp(long[["series", "date", "ret"]])

    def _stocks(self, client: WrdsClient, permnos: list[int]) -> pd.DataFrame:
        if not permnos:
            return pd.DataFrame()
        rets = client.query(
            "select permno, date, ret, prc, shrout from crsp.msf "
            "where permno = any(%(p)s) and ret is not null order by permno, date",
            {"p": permnos},
        )
        names = client.query(
            "select permno, ticker, nameenddt from crsp.stocknames where permno = any(%(p)s)",
            {"p": permnos},
        )
        rets["permno"] = rets["permno"].astype("int64")
        names["permno"] = names["permno"].astype("int64")
        latest = names.sort_values("nameenddt").drop_duplicates("permno", keep="last")
        rets["ticker"] = rets["permno"].map(latest.set_index("permno")["ticker"])
        rets["date"] = _month_end(rets["date"])
        rets["prc"] = rets["prc"].abs()  # negative CRSP prices are bid/ask midpoints
        return self._stamp(rets[["permno", "ticker", "date", "ret", "prc", "shrout"]])

    def _funds(self, client: WrdsClient, tickers: list[str], result: FetchResult) -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame()
        names = client.query(
            "select ticker, crsp_fundno, chgenddt from crsp.fund_names where ticker = any(%(t)s)",
            {"t": tickers},
        )
        names["crsp_fundno"] = names["crsp_fundno"].astype("int64")
        # Tickers get reused; take the fund most recently carrying the ticker.
        chosen = names.sort_values("chgenddt").drop_duplicates("ticker", keep="last")
        for ticker, group in names.groupby("ticker"):
            if group["crsp_fundno"].nunique() > 1:
                fundno = int(chosen.loc[chosen["ticker"] == ticker, "crsp_fundno"].iloc[0])
                result.warnings.append(f"{ticker}: several CRSP fund numbers; using {fundno}")
        for ticker in sorted(set(tickers) - set(chosen["ticker"])):
            result.warnings.append(f"{ticker}: not found in crsp.fund_names")
        rets = client.query(
            "select crsp_fundno, caldt, mret, mtna from crsp.monthly_tna_ret_nav "
            "where crsp_fundno = any(%(f)s) and mret is not null order by crsp_fundno, caldt",
            {"f": [int(f) for f in chosen["crsp_fundno"].unique()]},
        )
        rets["crsp_fundno"] = rets["crsp_fundno"].astype("int64")
        df = rets.merge(chosen[["ticker", "crsp_fundno"]], on="crsp_fundno")
        df["ret"] = pd.to_numeric(df["mret"], errors="coerce")
        df["tna"] = pd.to_numeric(df["mtna"], errors="coerce")
        df["date"] = _month_end(df["caldt"])
        df = df.dropna(subset=["ret"])
        return self._stamp(df[["ticker", "crsp_fundno", "date", "ret", "tna"]])

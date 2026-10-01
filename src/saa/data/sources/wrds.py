"""WRDS connector: licensed data that improves pre-ETF history and the CMA inputs.

Pulls CRSP fixed-term Treasury indexes, monthly returns for selected securities (the 18 ETFs for
cross-checking Yahoo, plus bullion-fund history links) and mutual fund returns for history links.
For the CMA methods it also builds US equity valuation aggregates (CRSP + Compustat + I/B/E/S),
corporate bond yields by rating class (WRDS Bond Returns) and the ETFs' market values (CRSP
CIZ). Firm- and bond-level rows are aggregated on the way in and never stored.
Skipped automatically when WRDS credentials are missing, so the pipeline still runs on public
data. Everything under ``wrds/`` is licensed to the account holder: never commit or publish it.
"""

from __future__ import annotations

import logging
import re

import pandas as pd

from saa.data.equity_valuation import (
    US_GROUPS,
    GroupRules,
    aggregate_equity_valuation,
    aggregate_international_valuation,
)
from saa.data.sources.base import FetchResult, Source
from saa.data.wrds_client import WrdsClient, credentials_problem

log = logging.getLogger(__name__)

TREASURY = "wrds/crsp_treasury_indexes"
STOCKS = "wrds/crsp_stock_monthly"
FUNDS = "wrds/crsp_fund_monthly"
VALUATION = "wrds/equity_valuation"
BONDS = "wrds/corporate_bond_yields"
ETF_CAPS = "wrds/etf_market_caps"
BOND_CLASSES = ("investment_grade", "high_yield")
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
            VALUATION: set(US_GROUPS) | set(self.settings.wrds.international_groups),
            BONDS: set(BOND_CLASSES),
            ETF_CAPS: {str(p) for p in permnos},
        }
        with WrdsClient() as client:
            jobs = (
                (TREASURY, lambda: self._treasury(client)),
                (STOCKS, lambda: self._stocks(client, permnos)),
                (FUNDS, lambda: self._funds(client, tickers, result)),
                (VALUATION, lambda: self._equity_valuation(client, result)),
                (BONDS, lambda: self._bond_yields(client)),
                (ETF_CAPS, lambda: self._etf_caps(client, permnos)),
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

    # ------------------------------------------------------------------ CMA inputs
    def _equity_valuation(self, client: WrdsClient, result: FetchResult) -> pd.DataFrame:
        """Group payout, earnings and book yields; see saa.data.equity_valuation. The
        international groups are optional: if their queries fail, the US groups still land."""
        us = self._us_equity_valuation(client)
        try:
            intl = self._international_valuation(client)
        except Exception as exc:
            message = str(exc).strip().splitlines()[0]
            result.warnings.append(f"{VALUATION}: international groups failed ({message})")
            intl = pd.DataFrame()
        return pd.concat([us, intl], ignore_index=True)

    def _us_equity_valuation(self, client: WrdsClient) -> pd.DataFrame:
        cfg = self.settings.wrds
        rules = GroupRules(**cfg.equity_groups.model_dump())
        start = pd.Timestamp(cfg.valuation_start)
        # CIZ monthly file: the legacy crsp.msf stops at 2024-12. Common stocks of US issuers
        # on NYSE/AMEX/Nasdaq, ranked by market cap within each month; REITs kept separately
        # (they are often "shares of beneficial interest", share type SB).
        panel = client.query(
            """
            select permno, mthcaldt as date, mthcap / 1000.0 as mcap, issuertype
            from (
                select permno, mthcaldt, mthcap, issuertype,
                       row_number() over (
                           partition by mthcaldt, issuertype = 'REIT' order by mthcap desc
                       ) as rk
                from crsp.msf_v2
                where mthcaldt >= %(start)s and mthcap > 0
                  and securitytype = 'EQTY' and securitysubtype = 'COM' and usincflg = 'Y'
                  and primaryexch in ('N', 'A', 'Q')
                  and (
                      (sharetype = 'NS' and issuertype in ('CORP', 'ACOR'))
                      or (sharetype in ('NS', 'SB') and issuertype = 'REIT')
                  )
            ) ranked
            where issuertype = 'REIT' or rk <= %(n)s
            """,
            {"start": start.date(), "n": rules.small_n},
        )
        fundamentals = client.query(
            "select gvkey, datadate, dvc, prstkc, sstk, ib, ceq, txditc from comp.funda "
            "where indfmt = 'INDL' and datafmt = 'STD' and popsrc = 'D' and consol = 'C' "
            "and datadate >= %(start)s",
            {"start": (start - pd.DateOffset(years=2)).date()},
        )
        links = client.query(
            "select gvkey, lpermno as permno, linkdt, linkenddt from crsp.ccmxpf_linktable "
            "where linktype in ('LU', 'LC') and linkprim in ('P', 'C') and lpermno is not null"
        )
        ltg = client.query(
            """
            select l.permno, s.statpers as date, s.medest as ltg_pct
            from ibes.statsum_epsus s
            join wrdsapps_link_crsp_ibes.ibcrsphist l
              on s.ticker = l.ticker and s.statpers between l.sdate and l.edate
            where s.fpi = '0' and s.measure = 'EPS' and s.usfirm = 1
              and s.statpers >= %(start)s and l.score <= 2 and s.medest is not null
            """,
            {"start": start.date()},
        )
        for frame, cols in (
            (panel, ["date"]),
            (fundamentals, ["datadate"]),
            (links, ["linkdt", "linkenddt"]),
            (ltg, ["date"]),
        ):
            for col in cols:
                frame[col] = pd.to_datetime(frame[col])
        for frame in (panel, links, ltg):
            frame["permno"] = frame["permno"].astype("int64")
        return self._stamp(aggregate_equity_valuation(panel, fundamentals, links, ltg, rules))

    def _international_valuation(self, client: WrdsClient) -> pd.DataFrame:
        """International groups from Compustat Global. Market caps are month-end price x shares
        from the daily security file (``monthend = 1``), converted to dollars through
        Compustat's GBP cross rates, and only each region's ``top_n`` largest primary issues
        leave the database."""
        cfg = self.settings.wrds
        if not cfg.international_groups:
            return pd.DataFrame()
        rules = GroupRules(**cfg.equity_groups.model_dump())
        start = pd.Timestamp(cfg.international_start)
        panels = []
        for group, spec in cfg.international_groups.items():
            panel = client.query(
                """
                with px as (
                    select s.gvkey, s.datadate,
                           s.prccd / coalesce(nullif(s.qunit, 0), 1) * s.cshoc as cap_local,
                           s.prccd / coalesce(nullif(s.qunit, 0), 1)
                               / coalesce(nullif(s.ajexdi, 0), 1) as price_adj,
                           s.curcdd
                    from comp_global_daily.g_secd s
                    join comp_global_daily.g_company co
                      on co.gvkey = s.gvkey and co.prirow = s.iid
                    where s.monthend = 1 and s.datadate >= %(start)s
                      and s.loc = any(%(countries)s) and s.prccd > 0 and s.cshoc > 0
                ),
                fx as (
                    select date_trunc('month', datadate) as m, tocurm, exratm
                    from comp_global_daily.g_exrt_mth
                    where fromcurm = 'GBP' and datadate >= %(start)s and exratm > 0
                ),
                usd as (
                    select px.gvkey, px.datadate,
                           px.cap_local * u.exratm / c.exratm / 1e6 as mcap,
                           px.price_adj * u.exratm / c.exratm as price_usd
                    from px
                    join fx c on c.m = date_trunc('month', px.datadate) and c.tocurm = px.curcdd
                    join fx u on u.m = c.m and u.tocurm = 'USD'
                )
                select gvkey, datadate as date, mcap, price_usd from (
                    select *, row_number() over (
                        partition by date_trunc('month', datadate) order by mcap desc
                    ) as rk
                    from usd
                ) ranked
                where rk <= %(n)s
                """,
                {"start": start.date(), "countries": spec.countries, "n": spec.top_n},
            )
            panels.append(panel.assign(group=group))
        panel = pd.concat(panels, ignore_index=True)
        panel["date"] = pd.to_datetime(panel["date"])
        gvkeys = sorted(panel["gvkey"].unique().tolist())
        # Banks and insurers are filed in the financial-services format (FS), not INDL; both
        # are read, preferring INDL where a company has both.
        fundamentals = client.query(
            "select gvkey, datadate, indfmt, curcd, dvc, prstkc, sstk, ib, ceq, txditc "
            "from comp_global_daily.g_funda "
            "where indfmt in ('INDL', 'FS') and datafmt = 'HIST_STD' and consol = 'C' "
            "and popsrc = 'I' and datadate >= %(start)s and gvkey = any(%(g)s)",
            {"start": (start - pd.DateOffset(years=2)).date(), "g": gvkeys},
        )
        fundamentals["datadate"] = pd.to_datetime(fundamentals["datadate"])
        fundamentals = fundamentals.sort_values("indfmt", ascending=False).drop_duplicates(
            ["gvkey", "datadate"]
        )
        dividends = client.query(
            """
            select s.gvkey, s.datadate as date, s.div / coalesce(nullif(s.ajexdi, 0), 1) as dps,
                   s.curcddv as currency
            from comp_global_daily.g_secd s
            join comp_global_daily.g_company co on co.gvkey = s.gvkey and co.prirow = s.iid
            where s.div > 0 and s.datadate >= %(start)s and s.gvkey = any(%(g)s)
            """,
            {"start": (start - pd.DateOffset(years=1)).date(), "g": gvkeys},
        )
        dividends["date"] = pd.to_datetime(dividends["date"])
        rates = client.query(
            "select datadate as date, tocurm as currency, exratm from comp_global_daily.g_exrt_mth "
            "where fromcurm = 'GBP' and datadate >= %(start)s and exratm > 0",
            {"start": (start - pd.DateOffset(years=2)).date()},
        )
        rates["date"] = pd.to_datetime(rates["date"])
        usd = rates[rates["currency"] == "USD"].set_index("date")["exratm"]
        rates["usd_per_unit"] = rates["date"].map(usd) / rates["exratm"]
        # Each payment in dollars at its own month's rate.
        dividends["month"] = dividends["date"] + pd.offsets.MonthEnd(0)
        dividends = dividends.merge(
            rates.assign(month=rates["date"] + pd.offsets.MonthEnd(0))[
                ["month", "currency", "usd_per_unit"]
            ],
            on=["month", "currency"],
            how="inner",
        )
        dividends["dps_usd"] = dividends["dps"] * dividends["usd_per_unit"]
        top_n = {g: spec.top_n for g, spec in cfg.international_groups.items()}
        out = aggregate_international_valuation(
            panel, fundamentals, rates, top_n, rules, dividends[["gvkey", "date", "dps_usd"]]
        )
        return self._stamp(out)

    def _bond_yields(self, client: WrdsClient) -> pd.DataFrame:
        """Amount-weighted yield and duration by rating class, aggregated in the database.
        Unrated bonds (which WRDS files under HY), convertibles, defaulted bonds and bonds within
        a year of maturity are excluded; yields above 50% are distressed quotes. The table's
        ``t_spread`` is not used: it is sparsely populated and benchmarked to Treasury
        maturities that often do not match the bond's."""
        df = client.query(
            """
            select date,
                   case when rating_num <= 10 then 'investment_grade' else 'high_yield' end
                       as rating_class,
                   count(*) as n_bonds,
                   100 * sum(yield * amount_outstanding) / sum(amount_outstanding) as yield_pct,
                   sum(duration * amount_outstanding) / sum(amount_outstanding) as duration_years
            from wrdsapps_bondret.bondret
            where rating_num is not null and rating_num <= 21 and conv = 0
              and yield between 0 and 0.5 and duration is not null
              and amount_outstanding > 0 and tmt >= 1
              and (defaulted is null or defaulted <> 'Y')
            group by 1, 2
            order by 1, 2
            """
        )
        df["date"] = _month_end(df["date"])
        df["n_bonds"] = df["n_bonds"].astype("int64")
        return self._stamp(df)

    def _etf_caps(self, client: WrdsClient, permnos: list[int]) -> pd.DataFrame:
        """The ETFs' market values: the point-in-time stand-in for asset-class size in the
        Black-Litterman method (the fund snapshot holds only AUM on the days it was taken)."""
        if not permnos:
            return pd.DataFrame()
        df = client.query(
            "select permno, mthcaldt as date, mthcap / 1000.0 as market_cap_musd "
            "from crsp.msf_v2 where permno = any(%(p)s) and mthcap > 0 order by permno, mthcaldt",
            {"p": permnos},
        )
        df["permno"] = df["permno"].astype("int64")
        tickers = {a.crsp_permno: a.ticker for a in self.config.universe.assets if a.crsp_permno}
        df["ticker"] = df["permno"].map(tickers)
        df["date"] = _month_end(df["date"])
        return self._stamp(df[["permno", "ticker", "date", "market_cap_musd"]])

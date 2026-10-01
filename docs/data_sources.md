# Data Sources

What the data layer ingests, why each source exists (mapped to the agents in Ang, Azimbayev &
Kim 2026), how history before each ETF's launch is built, and the remaining gaps.

**Constraints:** public, automatable data plus the project owner's WRDS account (approved
2026-09-15). No paid feeds, no manual inputs. The universe is exactly the paper's 18 asset
classes; proxy funds and indices are used only to extend their history.

## What the paper needs

| Pipeline stage | Data required | Paper reference |
|---|---|---|
| Macro agent | Growth, inflation, monetary-policy and financial-conditions indicators to classify expansion / late-cycle / recession / recovery | §3.2 |
| Historical-analysis skill | Returns, volatility, drawdowns, correlations for the 18 assets, history from Jan 1990 | Exhibit 3 |
| Asset-class agents (6 CMA methods) | Return history + risk-free rate; regime labels; market weights + covariance; dividend yield, growth, valuation; CAPE; survey consensus | Exhibit 4, §3.3 |
| Fixed-income CMA builder | Yields, credit spreads, duration | §3.3 |
| Covariance agent | Asset return history | §3.1 |
| CRO agent | Backtest volatility, VaR, drawdown, factor tilts | §3.5 |
| CIO / backtest | 60/40 benchmark, 1996-2026 backtest | §4.4 |

`config/cma_inputs.yaml` maps each CMA method to datasets and states its data approach.

## Sources

| Source | Connector | Datasets | Access | Used for |
|---|---|---|---|---|
| FRED / ALFRED | `sources/fred.py` | `macro/fred_observations`, `macro/fred_series_meta` | `FRED_API_KEY` | 62 macro, rates, credit and commodity series; revision vintages for GDP, payrolls, PCE, IP, retail sales, CFNAI, GDPNow |
| Yahoo Finance | `sources/yahoo.py` | `market/prices_daily`, `market/fund_snapshot` | public | 18 ETFs + 17 proxy tickers; daily ETF P/E, yield, duration, AUM snapshot |
| Kenneth French library | `sources/french.py` | `factors/french` | public | US/developed/EM market returns (history proxies), factors for CRO tilts |
| U.S. Treasury | `sources/treasury.py` | `rates/treasury_par_curve` | public | Nominal (1990-) and real (2003-) curves for fixed-income and cash CMAs |
| Shiller | `sources/shiller.py` | `valuation/shiller_us_equity` | public | S&P 500 CAPE, dividends, earnings (1871-) |
| Philadelphia Fed SPF | `sources/spf.py` | `surveys/spf_median` | public | Consensus 10-year returns (stocks, bonds, bills), inflation, growth |
| World Bank Pink Sheet | `sources/worldbank.py` | `commodities/worldbank_monthly` | public | Gold prices before 1986 (and before 2000 without WRDS) |
| WRDS (CRSP, Compustat, I/B/E/S, Bond Returns) | `sources/wrds.py` | `wrds/crsp_treasury_indexes`, `wrds/crsp_stock_monthly`, `wrds/crsp_fund_monthly`, `wrds/equity_valuation`, `wrds/corporate_bond_yields`, `wrds/etf_market_caps` | WRDS login, licensed | Treasury and T-bill index history, ETF return cross-check, fund history links; US equity valuation, corporate bond yields and ETF market values for the CMA methods |

## Long-history monthly returns (`market/asset_returns_monthly`)

Built by `src/saa/data/history.py` after every ingestion (or `uv run saa-data build-history`).
Each month uses the ETF when it has a month-end price, otherwise the first available link in the
asset's `history` chain (`config/universe.yaml`). Every row records its `source` and `kind`, and
`market/asset_history_links` reports each link's correlation, tracking error and mean return
difference against the ETF. Links were ordered by comparing candidates on those statistics.
See `docs/asset_data_map.md` for per-asset sources and numbers.

Licensed CRSP links sit first where they tracked better; the public links after them keep the
build working without WRDS credentials.

## Point-in-time handling

- **Revised macro series:** ALFRED vintages from each series' first vintage (1990 at the earliest). Before that, latest values with estimated release dates.
- **Other FRED series, French, Shiller, SPF, World Bank:** `available_from` = period end + release lag.
- **Spliced returns:** carry the lag of their source; `DataStore.asset_returns(as_of=...)` respects it.
- **NBER dates (`USREC`):** evaluation only, excluded from as-of queries.
- **Fund snapshot:** only exists from the first ingestion forward; run ingestion regularly.

The paper notes (§5.1) that LLM training data creates look-ahead bias that data hygiene cannot remove.

## WRDS

Login once with `uv run saa-data wrds-login` (password saved to the PostgreSQL password file,
never the repo), then `uv run saa-data wrds-check` to confirm access. Queries use `psycopg2`
directly because the official `wrds` package pins SQLAlchemy < 2, which pandas 3 cannot use.
The `wrds` source is skipped, not failed, when credentials are missing.

| CRSP table | Dataset | Use |
|---|---|---|
| `crsp.mcti` | `wrds/crsp_treasury_indexes` | 2y, 7y/10y, 20y/30y Treasury and 30-day T-bill history for Short/Intermediate/Long Treasuries and Cash |
| `crsp.msf`, `crsp.stocknames` | `wrds/crsp_stock_monthly` | All 18 ETFs (validation: Yahoo vs CRSP returns) and Central Fund of Canada (gold history) |
| `crsp.fund_names`, `crsp.monthly_tna_ret_nav` | `wrds/crsp_fund_monthly` | ACCBX (IG Corporates), RINSX (International Developed) |
| `crsp.msf_v2`, `comp.funda`, `crsp.ccmxpf_linktable`, `ibes.statsum_epsus`, `wrdsapps_link_crsp_ibes.ibcrsphist` | `wrds/equity_valuation` | Monthly dividend, buyback, issuance, earnings and book yields plus analyst long-term growth for five US groups (below), from 1989 |
| `comp_global_daily.g_secd`, `g_company`, `g_funda`, `g_exrt_mth` | `wrds/equity_valuation` | The same columns for International Developed and Emerging Markets, from 1994: trailing dividend yield, earnings and book yields (no buyback data in Compustat Global) |
| `wrdsapps_bondret.bondret` | `wrds/corporate_bond_yields` | Monthly amount-weighted yield and duration of rated IG and HY corporates, from 2002 |
| `crsp.msf_v2` | `wrds/etf_market_caps` | Monthly market value of the 18 ETFs: point-in-time Black-Litterman weights |

The legacy CRSP files (`crsp.msf`, `crsp.msi`) end 2024-12; CRSP's CIZ files (`*_v2`) end
2025-12 in the current release. The ETFs themselves, from Yahoo, cover all later months.

**US equity groups.** The ETFs report only today's P/E and yield, so
`saa/data/equity_valuation.py` rebuilds rule-based stand-ins each month from firm-level data:
US Large Cap = the 500 largest US common stocks; US Value / US Growth = the largest 1,000 split
at the median book-to-market; US Small Cap = ranks 1,001-3,000; REITs = every REIT. Yields are
cap-weighted aggregates; fundamentals count six months after the fiscal year ends, so each month
sees only what was public. Only these aggregates are stored; firm-level rows are not. Checked
against public data: the large-cap dividend yield tracks Shiller's S&P 500 dividend yield
closely, and the IG yield tracks the ICE index over the years both exist.

**Rejected:** WRDS Bond Returns' `t_spread` (sparse, and benchmarked to Treasury maturities
that often do not match the bond's). Spreads come from FRED instead.

**Licence:** WRDS data is for the account holder's use only. `wrds/` datasets stay in git-ignored
`data/` and must not be committed, published, or embedded in shared dashboards or artifacts.

**International groups.** The 700 largest firms headquartered in today's MSCI EAFE
countries and the 1,200 largest in today's MSCI EM countries, ranked each month by dollar
market cap (primary issue, month-end price x shares, converted through Compustat's GBP cross
rates). Dividends come from the security file's payment records, trailing 12 months over price,
because Compustat Global's annual dividend fields are filled for under a fifth of Australian and
French firms. Banks and insurers are read from the financial-services format (`FS`) as well as
`INDL`, which lifted fundamentals coverage from about 70% to over 90% of market cap. A firm
yield above 25% is treated as a data error (currency redenominations, e.g. Brazil 1994).
Checked against the ETFs' own figures in 2026-09: the developed group's dividend yield is 2.9%
against EFA's 3.1%, and its earnings yield 5.0% against 5.4%.

Limitations: weights are full market cap, so China A-shares weigh more than in MSCI EM, which
includes only part of them; country membership is today's list throughout; and there is no
buyback or reliable issuance data, so international net payout is dividends alone.

## Remaining gaps

| Gap | Affects | Approach |
|---|---|---|
| No international corporate bond history before PICB (2010) | Intl Corporates history | RPIBX (mostly sovereign) as proxy; pre-2010 history equals Intl Sovereigns |
| Commodities proxy is energy-heavy S&P GSCI (7.4% TE) | Commodities history (pre-2006) | Accept and disclose; CRSP commodity funds start 1997 and track no better |
| Gold before 2000: bullion fund (11.4% TE) or World Bank averages (13.7%) | Gold history 1996-2000 in the backtest | Accept and disclose |
| US Value before 1992 via French large-value portfolio (8.0% TE) | US Value history 1980-1992 | Outside the 1996 backtest; disclose for 1990 statistics |
| USD EM debt history starts mid-1993 | Full 1990 sample | Use the common window from 1993-06 |
| ICE BofA credit yields/OAS on FRED cover ~3 years | Fixed-income builder | WRDS Bond Returns yields (2002-), then Moody's Aaa/Baa; no spread for Intl Corporates or yield for USD EM before 2023 |
| CAPE only for the S&P 500 | CAPE-implied ERP, Gordon valuation change | ETF trailing P/E now, WRDS aggregate earnings yield before the first snapshot; no valuation drift outside US Large Cap |
| Asset-class market-cap weights | Black-Litterman | ETF market values (CRSP monthly, fund snapshot AUM): sizes of the ETFs, not of the asset classes |
| Consensus CMAs beyond US stocks/bonds/bills | Survey method | Macro agent view; I/B/E/S growth is ingested for the signals skill |
| International buybacks | Gordon for EFA/EEM | Not in Compustat Global; dividends alone, at reduced confidence |

## Adding a source

1. Add a `DatasetSpec` in `src/saa/data/datasets.py` (schema, keys, `available_from`; `optional=True` for licensed data).
2. Subclass `Source` in `src/saa/data/sources/`, return frames in `FetchResult.tables` (or set `skipped`), and register it in `SOURCE_REGISTRY`.
3. Add settings to `config/data_sources.yaml`, a validation check, and a parser test.
4. Expose a read method on `DataStore` or a history link type in `history.py`.

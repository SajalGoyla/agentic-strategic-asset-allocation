# Data Sources

What the data layer ingests, why each source exists (mapped to the agents in Ang, Azimbayev &
Kim 2026), known gaps, and alternatives worth adding.

## What the paper needs

| Pipeline stage | Data required | Paper reference |
|---|---|---|
| Macro agent | Growth, inflation, monetary-policy and financial-conditions indicators to score 4 dimensions and classify expansion / late-cycle / recession / recovery | §3.2 |
| Historical-analysis skill | Returns, volatility, drawdowns, correlations for 18 asset classes, history from Jan 1990 | Exhibit 3 |
| Asset-class agents (6 CMA methods) | Long return history + risk-free rate; regime labels; market-cap weights + covariance (BL); dividend yield, earnings growth, valuation (Inverse Gordon); CAPE / earnings yield; survey consensus | Exhibit 4, §3.3 |
| Fixed-income CMA builder | Yields, credit spreads, duration | §3.3 |
| Covariance agent | Asset return history | §3.1 step 3 |
| CRO agent | Back-test volatility, VaR, drawdown, factor tilts | §3.5 |
| CIO / backtest | 60/40 benchmark, 1996-2026 backtest window | §4.4 |

`config/cma_inputs.yaml` is the machine-readable version of this mapping.

## Implemented sources

| Source | Connector | Datasets | Key needed | Notes |
|---|---|---|---|---|
| FRED / ALFRED | `sources/fred.py` | `macro/fred_observations`, `macro/fred_series_meta` | Optional (`FRED_API_KEY`) | ~70 series (`config/macro_series.yaml`). With a key: metadata + full revision vintages for revised series (GDP, payrolls, PCE, IP...). Without a key: public CSV, latest vintage only. |
| Yahoo Finance (`yfinance`) | `sources/yahoo.py` | `market/prices_daily`, `market/fund_snapshot` | No | 18 ETFs + 12 long-history index mutual funds for backfill. Snapshot of P/E, distribution yield, duration, AUM appended each run. |
| Kenneth French Data Library | `sources/french.py` | `factors/french` | No | US 3/5 factors, momentum, 2x3 size/value portfolios (1926-), developed ex-US and EM factors (1989/1990-). |
| U.S. Treasury | `sources/treasury.py` | `rates/treasury_par_curve` | No | Daily par nominal (1990-) and real (2003-) curves. |
| Shiller (shillerdata.com) | `sources/shiller.py` | `valuation/shiller_us_equity` | No | S&P 500 price, dividends, earnings, CPI, CAPE (1871-). Download link discovered from the homepage; Yale copy (frozen 2023-09) is the fallback. |
| Philadelphia Fed SPF | `sources/spf.py` | `surveys/spf_median` | No | Median forecasts: STOCK10, BOND10, BILL10 (10-year return expectations), CPI10, RGDP10, inflation/rate paths. |

## Point-in-time handling

Backtests (Phase 4) must not use information that was not yet public:

- **Revised macro series** (`vintages: true`) store ALFRED vintages; `DataStore.macro(as_of=...)` returns the value in force on that date. Requires a FRED API key.
- **Other series** get `available_from = period end + release_lag_days`.
- **French, Shiller, SPF** use a conservative release lag.
- **NBER recession dates** (`USREC`) are `evaluation_only` and excluded from as-of queries.
- **ETF fund snapshots** exist only from the first ingestion onward; run ingestion regularly to build history.

Note the paper's own caveat (§5.1): LLM training data creates look-ahead bias that data hygiene alone cannot remove.

## Known gaps (and how to close them)

| Gap | Affects | Options |
|---|---|---|
| ETF histories start 1993-2010 (PICB limits the common sample to mid-2010) vs. the paper's Jan 1990 index histories | Historical ERP, regime-adjusted ERP, covariance, 1996-2026 backtest | (1) Splice backfill funds / French proxies already ingested (decision for the historical-analysis skill). (2) **WRDS** via Columbia (CRSP mutual fund and index returns, Bloomberg-equivalent index histories where licensed). (3) **Bloomberg Terminal** at Watson Library: total-return indices (SPTR, LBUSTRUU, etc.) as the paper uses. |
| ICE BofA credit yields/OAS on FRED are limited to a rolling ~3 years | Fixed-income builder (IG, HY, EM debt) | Moody's Aaa/Baa (1919-) are ingested as long-history proxies; full ICE history via Bloomberg/WRDS. |
| CAPE / P/E history for non-S&P equity classes | CAPE-implied ERP, Inverse Gordon | **Financial Modeling Prep** (the paper's `apex-data-financial` skill uses FMP + finviz; free tier key), Research Affiliates / Barclays CAPE pages (manual), Bloomberg. |
| Buyback yield | Inverse Gordon (US LC) | S&P Dow Jones Indices buyback data (quarterly press releases; manual), FMP. |
| Asset-class market-cap weights | Black-Litterman equilibrium | Manual, documented input from published global market portfolio estimates (e.g. Doeswijk, Lam & Swinkels), SIFMA bond market size, World Federation of Exchanges. ETF AUM in the snapshot is only a weak proxy. |
| Consensus CMAs beyond S&P 500 / Treasuries | Survey consensus method | Published long-term CMAs (J.P. Morgan LTCMA, BlackRock, Vanguard, Research Affiliates) entered manually each year. |
| Long gold and commodity history | Gold, Commodities CMAs and backfill | World Bank Pink Sheet (monthly prices, 1960-), LBMA gold price (licensed), `GC=F` futures on Yahoo (2000-). |
| Real-time text/news the macro agent searches | Macro narrative | Paper uses web search at runtime; not part of ingestion. |

## Adding a source

1. Add a `DatasetSpec` in `src/saa/data/datasets.py` (schema, keys, `available_from` if relevant).
2. Subclass `Source` in `src/saa/data/sources/`, return frames in `FetchResult.tables`, and register the class in `SOURCE_REGISTRY`.
3. Add settings to `config/data_sources.yaml`, a validation check, and a parser test.
4. Expose a read method on `DataStore`.

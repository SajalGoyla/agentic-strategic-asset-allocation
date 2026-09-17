# Data Quality Validation Report

Phase 1 deliverable (project plan, Week 2: "data quality validation report").
Data as of **2026-09-15**; regenerate with `uv run saa-data validate`, which writes
`data/reports/validation_<run_id>.json`. This document summarises that machine output and the
judgement calls behind it.

## Verdict

**266 checks pass, 1 warning, 0 failures.** Every asset class needed by the paper's 1996-2026
backtest has continuous monthly return history, and no dataset has duplicate keys, stale data
beyond its release schedule, or price errors.

The single warning is expected and documented: USD EM Debt history begins 1993-06 rather than
the paper's Jan 1990, because no public or CRSP fund tracking that asset class exists earlier.

## What is in the lake

| Dataset | Rows | Entities | Coverage |
|---|---|---|---|
| `market/prices_daily` | 265,997 | 35 tickers | 1980-01 .. 2026-09 |
| `market/asset_returns_monthly` | 9,473 | 18 assets | 1980-01 .. 2026-08 |
| `market/asset_history_links` | 54 | 18 assets | proxy diagnostics |
| `market/fund_snapshot` | 36 | 18 ETFs | from 2026-09 (accumulating) |
| `macro/fred_observations` | 417,385 | 62 series | 1960-01 .. 2026-09 |
| `rates/treasury_par_curve` | 126,990 | 2 curves | 1990-01 .. 2026-09 |
| `valuation/shiller_us_equity` | 1,869 | S&P 500 | 1871-01 .. 2026-09 |
| `surveys/spf_median` | 7,996 | 15 variables | 1968-10 .. 2026-07 |
| `commodities/worldbank_monthly` | 50,383 | 71 series | 1960-01 .. 2024-12 |
| `wrds/crsp_treasury_indexes` | 9,400 | 9 indexes | 1926-01 .. 2024-12 |
| `wrds/crsp_stock_monthly` | 4,981 | 19 securities | 1986-05 .. 2024-12 |
| `wrds/crsp_fund_monthly` | 1,073 | 2 funds | 1965-12 .. 2026-06 |

WRDS datasets are licensed and stay in the git-ignored `data/` directory. Without WRDS
credentials the pipeline runs on the public fallbacks in `config/universe.yaml`.

## Checks performed

| Check | Scope | Result |
|---|---|---|
| Primary keys unique | every dataset | pass |
| Freshness vs. each series' release schedule | 62 FRED series, 35 tickers, 2 curves, SPF, Shiller, World Bank | pass |
| ETF history starts at fund inception | 18 ETFs | pass |
| Daily return outliers (>25%) and gaps (>10 days) | 18 ETFs | pass |
| Monthly history continuity (no missing months) | 18 assets | pass |
| History start vs. 1990 target and 1996 backtest | 18 assets | 17 pass, 1 warn (USD EM Debt) |
| Monthly return outliers (>50%) | 18 assets | pass |
| Yahoo adjusted closes vs. CRSP total returns | 18 ETFs | pass (see below) |
| World Bank series used by history present | gold | pass |

## Coverage of the 18 asset classes

- **All 18 have continuous monthly returns from 1993-06** (limited by USD EM Debt), covering the paper's 1996-2026 backtest in full.
- **16 of 18 reach 1990** or earlier; International Developed starts 1990-07.
- **ETFs alone would only overlap from 2010-06** (limited by PICB), which is why pre-ETF proxies exist.

## Independent cross-check: Yahoo vs. CRSP

Yahoo is free and unofficial, so its adjusted closes were checked against CRSP total returns for
all 18 ETFs over every overlapping month (up to 383 months each). Annualised tracking error runs
**0.01% to 0.45%**, with mean return gaps of at most 0.15% a year. The largest gaps (SPY 0.45%,
IEF and LQD 0.31%) come from dividend timing conventions. Yahoo is fit for purpose.

## Proxy quality before each ETF existed

Each pre-ETF proxy was chosen by measuring tracking error against its own ETF over their
overlap; `market/asset_history_links` carries the numbers, and `docs/asset_data_map.md` lists
them per asset. Summary:

| Quality | Assets | Tracking error |
|---|---|---|
| Excellent (below 1%) | US Large Cap, Short Treasuries, Intermediate Treasuries, Cash, REITs (VGSIX) | 0.2-0.8% |
| Good (1-3%) | Long Treasuries, International Sovereigns, International Developed, US Value/Growth (funds), US Small Cap, REITs (FRESX), Gold (futures) | 1.5-3.1% |
| Acceptable (3-5%) | IG Corporates, HY Corporates, International Corporates, Emerging Markets, USD EM Debt | 3.3-5.2% |
| Weak, disclosed | Commodities (S&P GSCI), Gold pre-2000 (bullion fund), US Value pre-1992 (French portfolio) | 7.4-13.7% |

The weak cases are unavoidable with available data; results that depend on them should say so.

## Point-in-time quality

Backtests must not use data published after the date being simulated.

- Every look-ahead-sensitive row carries `available_from`, and `DataStore(as_of=...)` honours it.
- **8 of 62 FRED series carry true ALFRED revision vintages** (GDP, payrolls, industrial production, retail sales, PCE and core PCE, CFNAI, GDPNow). Their vintages start as late as 2011 (CFNAI) and 2016 (GDPNow); earlier dates fall back to revised values with estimated release dates.
- The macro-inputs skill reports this per indicator (`point_in_time`) and per dimension (`pit_quality`), so a regime call can state how point-in-time it really was.
- NBER recession dates are marked `evaluation_only` and are excluded from as-of queries.
- Verified end to end in `tests/test_integration.py`: as of 2020-04-01 the latest payrolls reading is February 2020, and the equity drawdown is the COVID crash as it stood then.

## Known limitations to disclose in results

1. **USD EM Debt** history starts 1993-06; **International Developed** 1990-07.
2. **International Corporates** before 2010 reuse the International Sovereigns proxy, so the two are identical in that period.
3. **Gold before 2000** (bullion fund, 11.4% tracking error) and **commodities before 2006** (S&P GSCI, 7.4%) are the weakest series.
4. **ICE BofA credit spreads** on FRED cover only a rolling ~3 years; Moody's Aaa/Baa (1919-) provide the long history.
5. **CRSP data ends 2024-12**; the ETFs themselves cover later months.
6. **The ETF fundamentals snapshot** only accumulates from 2026-09, so valuation history for non-US equity classes is short.
7. **Look-ahead from the LLM itself** cannot be removed by data hygiene (paper §5.1).

## Reproducing this report

```bash
uv run saa-data ingest      # all sources; WRDS skipped without credentials
uv run saa-data validate    # writes data/reports/validation_<run_id>.json
uv run pytest               # 131 tests, including integration tests when a lake exists
```

Each ingestion writes immutable dataset versions plus `data/runs/<run_id>.json`, and every agent
output records the versions it read, so any result can be traced to exact inputs.

## Sign-off

| Role | Name | Status |
|---|---|---|
| Data layer | Sajal Kumar Goyla | Complete for Phase 1 |
| Review | Shambhawi Bhure | Pending |
| Faculty | Prof. Paul Glasserman | Pending |

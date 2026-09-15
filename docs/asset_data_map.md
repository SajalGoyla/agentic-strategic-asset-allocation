# Asset Data Map

What data each of the 18 IPS asset classes uses, where it comes from, and how good it is.
Proxy funds and indices extend history only; they are not assets.

Sources are public, plus CRSP data from the project owner's WRDS account (licensed: kept in
git-ignored `data/`, never committed or published). Without WRDS credentials the pipeline
falls back to the public links shown below.

Numbers are from the 2026-09-15 build. Regenerate with `DataStore().history_links()` and
`DataStore().asset_returns(field="source")`.

## Data every asset uses

| Data | Dataset | Used by |
|---|---|---|
| Monthly total returns, ETF spliced with proxies | `market/asset_returns_monthly` | Historical-analysis skill, covariance agent, historical and regime-adjusted ERP, BL, CRO, backtests |
| Proxy quality (correlation, tracking error vs. ETF) | `market/asset_history_links` | CMA judge confidence, documentation |
| Daily ETF prices and distributions | `market/prices_daily` | Momentum/trend signals, trailing yield, CRO drawdown/VaR |
| ETF snapshot: AUM, P/E, distribution yield, duration | `market/fund_snapshot` | BL weight proxy (AUM), valuation or yield inputs |
| Risk-free rate | FRED `DTB3`, CRSP 30-day T-bill, French `RF`, Treasury curve | Excess returns, cash CMA |
| Macro regime indicators (growth, inflation, policy, financial conditions) | `macro/fred_observations` | Macro agent, regime-adjusted ERP |

## Return history by asset

TE = annualised tracking error of the proxy against the ETF over their overlapping months.
**Bold** sources come from WRDS (CRSP). Every asset covers the paper's 1996-2026 backtest; the
common start is 1993-06 (USD EM Debt).

| # | Asset | ETF (monthly from) | Pre-ETF sources with WRDS | TE | Public fallback (no WRDS) | Starts |
|---|---|---|---|---|---|---|
| 1 | US Large Cap | SPY (1993-02) | VFINX 1980-02..1993-01 | 0.8% | same | 1980-01 |
| 2 | US Small Cap | IWM (2000-06) | NAESX 1980-02..2000-05 | 3.1% | same | 1980-01 |
| 3 | US Value | IWD (2000-06) | French large-value portfolio 1980..1992-10; VIVAX 1992-11..2000-05 | 8.0%; 2.5% | same | 1980-01 |
| 4 | US Growth | IWF (2000-06) | French large-growth portfolio 1980..1992-10; VIGRX 1992-11..2000-05 | 3.3%; 3.0% | same | 1980-01 |
| 5 | International Developed | EFA (2001-09) | **Russell International Developed Markets fund (RINSX)** 1983-02..2001-08 | 2.5% | French developed ex-US market from 1990-07 (2.9%) | 1983-02 |
| 6 | Emerging Markets | EEM (2003-05) | French EM market 1989-07..1994-05; VEIEX 1994-06..2003-04 | 5.2%; 4.3% | same | 1989-07 |
| 7 | Short-Term Treasuries | SHY (2002-08) | **CRSP 2-year Treasury index** 1980..2002-07 | 0.3% | Synthetic 2y par bond from DGS2 (0.3%) | 1980-01 |
| 8 | Intermediate Treasuries | IEF (2002-08) | **CRSP 7- and 10-year Treasury indexes** 1980..2002-07 | 0.7% | Synthetic from DGS7/DGS10 (0.8%) | 1980-01 |
| 9 | Long-Term Treasuries | TLT (2002-08) | **CRSP 20- and 30-year Treasury indexes** 1980..2002-07 | 1.5% | Synthetic from DGS20/DGS30 (1.5%), VUSTX 1987-93 (2.3%) | 1980-01 |
| 10 | IG Corporates | LQD (2002-08) | **Invesco Corporate Bond fund (ACCBX)** 1980..2002-07 | 3.3% | VWESX to 1993, VFICX to 2002 (4.5%; 3.6%) | 1980-01 |
| 11 | HY Corporates | HYG (2007-05) | VWEHX 1980-02..2007-04 | 4.5% | same | 1980-02 |
| 12 | International Sovereigns | BWX (2007-11) | RPIBX 1986-10..2007-10 | 1.9% | same | 1986-10 |
| 13 | International Corporates | PICB (2010-07) | RPIBX 1986-10..2010-06 | 4.0% | same | 1986-10 |
| 14 | USD EM Debt | EMB (2008-01) | FNMIX 1993-06..2007-12 | 4.8% | same | 1993-06 |
| 15 | REITs | VNQ (2004-10) | FRESX 1986-12..1996-05; VGSIX 1996-06..2004-09 | 2.8%; 0.8% | same | 1986-12 |
| 16 | Gold | GLD (2004-12) | World Bank 1980..1986-04; **Central Fund of Canada bullion fund** 1986-05..2000-08; gold futures 2000-09..2004-11 | 13.7%; 11.4%; 2.2% | World Bank monthly averages to 2000-08 (13.7%) | 1980-01 |
| 17 | Commodities | DBC (2006-03) | S&P GSCI 1984-02..2006-02 | 7.4% | same | 1984-02 |
| 18 | Cash | BIL (2007-06) | **CRSP 30-day T-bill** 1980..2007-05 | 0.2% | French 1-month T-bill (0.2%) | 1980-01 |

How proxies were chosen:

- **Treasuries and cash:** CRSP fixed-term indexes were compared with synthetic par-bond returns and index funds; they match or beat both and are observed index data.
- **Fund search:** all CRSP mutual funds with matching names and history before each ETF were scored against the ETF: 400 international bond funds (PICB), 227 (BWX), 34 EM debt (EMB), 15 commodity (DBC), 60 IG (LQD), 160 high yield (HYG), 39 international equity (EFA). Only IG (ACCBX) and International Developed (RINSX) improved.
- **Rejected on evidence:** PFORX (hedged, 7.6% TE vs BWX), synthetic Moody's Aaa/Baa yields for IG (6.1%), S&P GSCI plus T-bills for commodities, commodity funds from 1997 (7.6%+).
- **Yahoo checked against CRSP:** Yahoo adjusted-close returns match CRSP total returns for all 18 ETFs (tracking 0.01%-0.45%, mean gap at most 0.15%/yr).

## CMA inputs by asset

Which of the six paper methods apply, and the asset-specific data each needs beyond the common
data above. "Macro view" is the paper's allowed alternative when no survey exists.

| Asset | Methods | Valuation / yield (current) | Expectations & survey | FRED building blocks |
|---|---|---|---|---|
| US Large Cap | All 6 + blend | Shiller CAPE, dividends, earnings (1871-); SPY P/E, yield | SPF STOCK10, RGDP10, CPI10 | DGS10, DTB3 |
| US Small Cap, US Value, US Growth | All 6 + blend | ETF trailing P/E, distribution yield | SPF RGDP10, CPI10; STOCK10 or macro view | DGS10, DTB3 |
| International Developed | All 6 + blend | EFA P/E, distribution yield | SPF CPI10; macro view | German, Japanese, UK 10y yields; dollar index |
| Emerging Markets | All 6 + blend | EEM P/E, distribution yield | Macro view | Dollar index |
| Short / Intermediate / Long Treasuries | Historical, regime, BL, fixed-income builder, survey | Treasury par curve, ETF yield and duration | SPF BOND10, BILL10, TBOND path | DGS1-DGS30, real yields, term premium |
| IG Corporates | Historical, regime, BL, fixed-income builder | LQD yield, duration | Macro view | Moody's Aaa/Baa (1919-), Baa-10y spread, ICE IG yield/OAS (last ~3y) |
| HY Corporates | Historical, regime, BL, fixed-income builder | HYG yield, duration | Macro view | ICE HY yield/OAS (last ~3y), Baa-10y spread history |
| International Sovereigns | Historical, regime, BL, fixed-income builder | BWX yield, duration | Macro view | OECD 10y yields: Germany, Japan, UK, France, Canada; dollar index |
| International Corporates | Historical, regime, BL, fixed-income builder | PICB yield, duration | Macro view | OECD 10y yields: Germany, UK |
| USD EM Debt | Historical, regime, BL, fixed-income builder | EMB yield, duration | Macro view | ICE EM corporate yield (last ~3y), DGS10 |
| REITs | All 6 + blend | VNQ P/E, distribution yield | SPF CPI10; macro view | DGS10, 10y real yield |
| Gold | Historical, regime, BL, macro view | None (no income) | T5YIFR inflation expectations | 10y real yield, dollar index |
| Commodities | Historical, regime, BL, macro view | None; T-bill collateral | Inflation expectations | DTB3, WTI, Brent, copper |
| Cash | Yield, survey | Treasury bill curve | SPF BILL10, TBILL path | DTB3, DGS1MO, fed funds |

WRDS also gives access to Compustat, I/B/E/S and CRSP market caps, which can replace the ETF
snapshot for US valuation (CAPE, buyback yield), analyst growth, and Black-Litterman weights.
These are CMA-stage inputs and are not ingested yet.

## Weak spots to disclose in results

- **Gold before 2000:** a gold+silver bullion fund (11.4% TE) with WRDS, or World Bank monthly averages (13.7% TE) without. About 4.5 years of the 1996-2026 backtest use it.
- **Commodities before 2006:** the S&P GSCI is energy-heavy relative to DBC (7.4% TE); no CRSP fund tracks better.
- **US Value 1980-1992:** French large-value portfolio (8.0% TE), before the paper's backtest.
- **International Corporates before 2010:** RPIBX, the same fund as International Sovereigns, so the two have identical returns until PICB launched.
- **USD EM Debt:** history starts 1993-06 (no earlier fund in CRSP), against the paper's Jan-1990 history.
- **Macro revisions:** vintages start at each series' first ALFRED date (e.g. PCE 2000, CFNAI 2011); earlier as-of values are latest revised data.
- **Reproducibility without WRDS:** collaborators without WRDS get the public fallbacks, so five assets' pre-ETF history differs slightly from the WRDS build.

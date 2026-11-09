# Asset Class Analysis Agent — International Developed

**Role:** Produce the 13-section investment case and the capital market assumption for
International Developed (MSCI EAFE).
**Slug:** `intl-developed` | **Index:** MSCI EAFE | **Category:** International Equity |
**ETF:** `EFA` | **History:** Feb 1983-present
**Macro sensitivity:** Growth (+), Rates (-), Inflation (-), Dollar (--)
**Primary valuation lens:** CAPE against the US; local long yields (German, Japanese, UK) as the discount rate

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for International Developed. The
shared methodology — the eight candidate methods, the five judgment steps and the hard range
constraint — lives in `../AGENT.md` and the `cma-judge` skill; what follows is only what is
specific to this asset, and it is read at runtime as Exhibit 3 specifies.

Sensitivity signs give the direction of **this asset's return** when that factor rises, not the
direction of its earnings. `(++)`/`(--)` mark the strongest exposures in the universe. They are
orientation for the narrative; the scored values come from the measured
`dimension_alignment` signal, not from this file.

## Required skills

- `asset-class-report` — the 13-section investment case
- `historical-analysis` — return, risk, drawdowns and per-regime statistics
- `signals` — macro, technical and valuation signals
- `cma-methods` — the eight candidates with confidences and component breakdowns
- `cma-judge` — the shared judgment framework (Exhibit 4)
- `scenarios` — bull, base and bear from the candidate range

## Workflow (Exhibit 3)

1. Load the macro view (`macro/macro-view.json`: regime, dimension scores, confidence).
2. Historical analysis: returns, volatility, drawdowns, correlations against the other 17.
3. Valuation and fundamentals, through this asset's lens: CAPE against the US; local long yields (German, Japanese, UK) as the discount rate.
4. Technical signals: momentum, trend, mean reversion, relative momentum.
5. Sentiment and external data. **Not available to us:** Exhibit 3 step 5 sources fund flows and
   positioning from a runtime web search, which this pipeline does not do (decision 26). Survey
   consensus arrives through the `survey_consensus` candidate instead. Do not claim a flow or
   positioning view you cannot source.
6. Build the CMA: the deterministic candidates plus the confidence-weighted auto-blend.
7. CMA judge: select one, weight several, or accept the blend — within the candidate range.
8. Scenario analysis (bull/bear from the method range) and the 13-section report.

## Key considerations

These are the asset-specific instructions. Read them before judging, and address the ones that
bear on your choice in `rationale`, `valuation_context` or `notes`.

1. **Unhedged, so currency is part of the asset.** The USD share class means the dollar is a first-order driver of both return and volatility. A large part of any historical outperformance or underperformance against the US is currency, not equity. State whether your estimate assumes a currency contribution and of what sign.

2. **Japan and Europe are the index.** Europe is roughly 60% and Japan roughly a fifth, so this is a bet on two quite different cycles aggregated into one number, with Japanese corporate governance reform and European energy costs pulling in different directions.

3. **A structurally different sector mix.** Much less technology and much more financials, industrials and staples than the S&P 500. That alone explains a large part of the persistent valuation discount, so the discount is not automatically an opportunity.

4. **It will always look cheap on CAPE.** EAFE has traded below the US on CAPE for most of the past two decades. A valuation-tilted method will therefore always favour it. The judgement you have to make is how much of the gap is sector mix and governance (structural, not closing) versus sentiment (mean-reverting). The paper's judge marked it down only -0.3%.

5. **The CMA uses local long yields.** `IRLTLT01DEM156N`, `IRLTLT01JPM156N` and `IRLTLT01GBM156N` stand in for the local risk-free rates, so a build-up method here is anchored to Bund, JGB and Gilt yields rather than to Treasuries.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

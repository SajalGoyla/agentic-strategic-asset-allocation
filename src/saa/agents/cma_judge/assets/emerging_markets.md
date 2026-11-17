# Asset Class Analysis Agent — Emerging Markets

**Role:** Produce the 13-section investment case and the capital market assumption for
Emerging Markets (MSCI Emerging Markets).
**Slug:** `emerging-markets` | **Index:** MSCI Emerging Markets | **Category:** International Equity |
**ETF:** `EEM` | **History:** Jul 1989-present
**Macro sensitivity:** Growth (+), Rates (-), Inflation (-), Dollar (--)
**Primary valuation lens:** CAPE, which is the cheapest in the universe and has been for years

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for Emerging Markets. The
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
3. Valuation and fundamentals, through this asset's lens: CAPE, which is the cheapest in the universe and has been for years.
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

1. **The highest-volatility asset in the universe.** Around 22% annualised on our covariance matrix, against roughly 15% for US large cap. Any expected return has to be judged against that, and a risk-based PC method will give it a small weight however attractive the CMA.

2. **Three countries are most of the index.** China, Taiwan and Korea together run near 60% of weight, and Taiwan and Korea are concentrated in semiconductors. This is substantially a China policy position plus a semiconductor cycle position.

3. **The dollar and global liquidity dominate the short run.** EM equity is one of the most dollar-sensitive assets here: a strong dollar tightens local funding conditions and compresses multiples at the same time.

4. **Cheap for reasons that may not close.** Exhibit 8 puts EM at CAPE around 13, the cheapest in the universe, and yet the paper's judge marked it down only -0.2% - treating most of the discount as compensation for governance, state ownership and capital-controls risk rather than as mispricing. Reaching a very different conclusion needs an argument about why the discount should close.

5. **This is unhedged equity, not local-currency debt.** Do not import carry or local-rate reasoning from `usd_em_debt`; the two have different risk drivers despite the shared label.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

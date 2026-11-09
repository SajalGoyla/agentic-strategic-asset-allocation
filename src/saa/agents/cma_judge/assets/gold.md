# Asset Class Analysis Agent — Gold

**Role:** Produce the 13-section investment case and the capital market assumption for
Gold (LBMA Gold Price PM).
**Slug:** `gold` | **Index:** LBMA Gold Price PM | **Category:** Real Assets |
**ETF:** `GLD` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (0), Rates (--), Inflation (+), Dollar (--)
**Primary valuation lens:** no cash flow: real yields (`DFII10`), inflation expectations (`T5YIFR`) and the dollar (`DTWEXBGS`)

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for Gold. The
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
3. Valuation and fundamentals, through this asset's lens: no cash flow: real yields (`DFII10`), inflation expectations (`T5YIFR`) and the dollar (`DTWEXBGS`).
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

1. **There is no cash flow, so every discounted-cash-flow method is inapplicable.** No dividend, no earnings, no coupon. The inverse-Gordon and implied-ERP candidates cannot speak to this asset at all, and a historical-ERP method is measuring a price trend rather than a premium. Build the estimate from real rates, inflation expectations and the dollar, and say which candidates you discarded as structurally inapplicable.

2. **The real 10-year yield is the strongest single driver.** Gold is a zero-coupon real asset, so its price moves against the real opportunity cost of holding it. `DFII10` is in the `cma_series` for exactly that reason.

3. **Central banks have become a large, price-insensitive buyer.** Official-sector demand responds to reserve policy rather than to price, which supports the market in ways the pre-2010 history does not contain.

4. **Its portfolio role is the diversification, not the return.** Correlation with US large cap is roughly zero on our matrix (-0.02), which is why risk-based PC methods give it weight that return-based methods will not justify. Expect that disagreement and address it.

5. **Long-run real return is close to zero, and storage is a small negative carry.** Gold preserves purchasing power over very long periods rather than compounding it. A CMA that implies a sustained real return materially above zero is making a claim about a regime change, not about an asset with a yield.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

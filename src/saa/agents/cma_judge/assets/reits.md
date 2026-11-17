# Asset Class Analysis Agent — REITs

**Role:** Produce the 13-section investment case and the capital market assumption for
REITs (MSCI US IMI Real Estate 25/50).
**Slug:** `reits` | **Index:** MSCI US IMI Real Estate 25/50 | **Category:** Real Assets |
**ETF:** `VNQ` | **History:** Dec 1986-present
**Macro sensitivity:** Growth (+), Rates (--), Inflation (+), Dollar (0)
**Primary valuation lens:** the dividend yield plus NOI growth; cap rates against the real 10-year yield (`DFII10`)

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for REITs. The
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
3. Valuation and fundamentals, through this asset's lens: the dividend yield plus NOI growth; cap rates against the real 10-year yield (`DFII10`).
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

1. **A levered real-asset equity, not a bond substitute.** Correlation of 0.65 with US large cap on our matrix. REITs are equities whose underlying assets happen to be buildings, and balance-sheet leverage amplifies both the rate sensitivity and the equity beta.

2. **Use FFO or AFFO, not GAAP earnings.** Depreciation on long-lived property makes reported earnings and therefore P/E and CAPE close to meaningless for this sector. Dividend yield plus net-operating-income growth is the right build, and the payout is constrained by the REIT distribution requirement.

3. **Cap rates trade against real yields,** which is why `DFII10` is in this asset's `cma_series`. The valuation question is the spread between property cap rates and the real 10-year yield, not the nominal level of rates.

4. **The property mix has changed fundamentally.** Weight has moved away from office and regional retail toward industrial, data centres and communication towers, so sector betas and yields estimated on the long history describe a different asset class from today's index. The paper's judge marked REITs down only -0.2%; ours marked them -0.68%.

5. **Public and private valuations diverge for long stretches.** Listed REITs reprice daily and can trade at a sustained discount or premium to appraised NAV. A discount is information about the forward return, and it is also a reason the listed series is more volatile than the underlying property.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

# Asset Class Analysis Agent — Short-Term Treasuries

**Role:** Produce the 13-section investment case and the capital market assumption for
Short-Term Treasuries (ICE US Treasury 1-3 Year).
**Slug:** `short-treasuries` | **Index:** ICE US Treasury 1-3 Year | **Category:** US Fixed Income |
**ETF:** `SHY` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (-), Rates (-), Inflation (-), Dollar (0)
**Primary valuation lens:** the yield level (`DGS1`, `DGS2`, `DGS3`); carry is almost the whole return

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for Short-Term Treasuries. The
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
3. Valuation and fundamentals, through this asset's lens: the yield level (`DGS1`, `DGS2`, `DGS3`); carry is almost the whole return.
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

1. **Carry is the return.** With duration near two years, price change is a small share of total return over a three-year horizon. The starting yield plus roll-down is close to the whole estimate, which makes this one of the most reliable CMAs in the universe.

2. **Watch the Sharpe ratio it implies.** On our inputs this asset has the highest ex-ante Sharpe of all eighteen - about 0.52 against 0.39 for the next best - because a small term premium divided by 1.7% volatility is a large ratio. That is arithmetically correct and it makes every return-optimised PC method crowd into it. Flag it in your rationale so the downstream agents are not surprised.

3. **It is a near-substitute for cash.** High correlation with `cash` and little independent diversification value. A portfolio holding large weights in both is holding one position.

4. **Roll-down matters when the curve slopes up.** A 3-year bond held for a year becomes a 2-year bond and is repriced at a lower yield, adding return beyond the coupon. An inverted curve reverses that, so the sign of the roll depends on the curve shape today.

5. **Reinvestment risk, not price risk, is the exposure.** Falling short rates hurt this sleeve over a 3-year horizon even though they raise its price today.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

# Asset Class Analysis Agent — International Sovereign Bonds

**Role:** Produce the 13-section investment case and the capital market assumption for
International Sovereign Bonds (Bloomberg Global Treasury ex-US Capped).
**Slug:** `intl-sovereigns` | **Index:** Bloomberg Global Treasury ex-US Capped | **Category:** International Fixed Income |
**ETF:** `BWX` | **History:** Oct 1986-present
**Macro sensitivity:** Growth (-), Rates (-), Inflation (-), Dollar (--)
**Primary valuation lens:** local long yields (German, Japanese, UK, French, Canadian)

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for International Sovereign Bonds. The
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
3. Valuation and fundamentals, through this asset's lens: local long yields (German, Japanese, UK, French, Canadian).
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

1. **This is a currency position wearing a bond label.** Unhedged and USD-denominated, with low local-bond volatility, so exchange rates supply most of the variance. Judging it as a duration asset will produce the wrong answer; say explicitly what you assume the dollar does.

2. **The carry starting point is structurally lower than the US.** Japan and much of Europe spent a decade at or below zero yields, so the long history of this index was earned in conditions that cannot repeat from here. A historical-average method is badly placed on this asset.

3. **The weakest risk-adjusted profile in the universe.** On our inputs it has the lowest ex-ante Sharpe of all eighteen (about 0.05): low yield, meaningful currency volatility. Say so rather than let the number pass unremarked.

4. **Hedged versus unhedged is the biggest definitional choice on this asset,** and we hold the unhedged version. A hedged index would have a quite different return and far lower volatility; do not mix evidence from the two.

5. **It overlaps `intl_corporates` on the currency leg,** so holding both adds less diversification than two line items suggest.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

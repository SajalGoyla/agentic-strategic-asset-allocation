# Asset Class Analysis Agent — Investment-Grade Corporates

**Role:** Produce the 13-section investment case and the capital market assumption for
Investment-Grade Corporates (iBoxx USD Liquid Investment Grade).
**Slug:** `ig-corporates` | **Index:** iBoxx USD Liquid Investment Grade | **Category:** US Fixed Income |
**ETF:** `LQD` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (+), Rates (--), Inflation (-), Dollar (0)
**Primary valuation lens:** the yield level (`BAA`) and the credit spread (`BAMLC0A0CM`)

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for Investment-Grade Corporates. The
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
3. Valuation and fundamentals, through this asset's lens: the yield level (`BAA`) and the credit spread (`BAMLC0A0CM`).
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

1. **Mostly a duration position with a credit kicker.** Duration around eight years, so Treasury yield moves drive more of the return than spread moves do. Decompose the estimate into the Treasury leg and the spread leg, and say which one your view is actually about.

2. **Expected return is the yield minus expected losses, and for IG those losses are small.** Investment-grade default rates are low enough that the spread is mostly compensation for illiquidity and mark-to-market risk rather than for credit loss. That makes the yield a better starting point here than it is for high yield.

3. **The index's credit quality has drifted down.** BBB-rated issuance has grown to roughly half of the investment-grade market, so today's index is lower quality than the one the long history was earned on. A historical-spread average therefore flatters it.

4. **Spreads are mean-reverting, which makes the starting point asymmetric.** Tight spreads cap the upside and leave the downside intact; wide spreads are where the forward return is. The credit-spread signal in `config/signals.yaml` scores wide as bullish for this reason.

5. **The diversification fails when it is needed.** Correlation with equities rises in stress - 0.58 with US large cap on our matrix, and higher in the worst months - so this is not a Treasury substitute for the purpose of hedging an equity drawdown.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

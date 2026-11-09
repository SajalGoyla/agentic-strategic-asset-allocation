# Asset Class Analysis Agent — High-Yield Corporates

**Role:** Produce the 13-section investment case and the capital market assumption for
High-Yield Corporates (iBoxx USD Liquid High Yield).
**Slug:** `hy-corporates` | **Index:** iBoxx USD Liquid High Yield | **Category:** US Fixed Income |
**ETF:** `HYG` | **History:** Feb 1980-present
**Macro sensitivity:** Growth (++), Rates (-), Inflation (0), Dollar (0)
**Primary valuation lens:** the yield level (`BAMLH0A0HYM2EY`) and the spread (`BAMLH0A0HYM2`)

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for High-Yield Corporates. The
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
3. Valuation and fundamentals, through this asset's lens: the yield level (`BAMLH0A0HYM2EY`) and the spread (`BAMLH0A0HYM2`).
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

1. **The yield is not the expected return.** Subtract expected credit losses: the long-run default rate has averaged roughly 4% a year with recoveries near 40%, which is a haircut of around 2.4pp on the headline yield. A CMA that uses yield-to-worst untouched is systematically too high, and this is the single most common error on this asset.

2. **Yield-to-worst already understates the call problem.** High-yield bonds are callable, so issuers refinance when spreads tighten and investors keep the downside. The realised return distribution is left-skewed beyond what volatility shows.

3. **It behaves like equity when it matters.** Correlation of 0.72 with US large cap on our matrix. In a growth shock this sleeve is an equity position with a coupon, which is why the Growth sensitivity is the strongest in the fixed-income group.

4. **Short duration, so spread risk not rate risk.** Duration around three to four years means much less Treasury sensitivity than IG. A view on this asset should be a view on the credit cycle, not on the Fed.

5. **The index excludes the weakest part of the market.** Liquid high-yield indices skip the smallest and least traded issues, so index default experience understates the asset class's and the available history is cleaner than the opportunity set.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

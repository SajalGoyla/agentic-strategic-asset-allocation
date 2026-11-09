# Asset Class Analysis Agent — Long-Term Treasuries

**Role:** Produce the 13-section investment case and the capital market assumption for
Long-Term Treasuries (ICE US Treasury 20+ Year).
**Slug:** `long-treasuries` | **Index:** ICE US Treasury 20+ Year | **Category:** US Fixed Income |
**ETF:** `TLT` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (-), Rates (---), Inflation (---), Dollar (0)
**Primary valuation lens:** the yield level (`DGS20`, `DGS30`) and the term premium

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for Long-Term Treasuries. The
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
3. Valuation and fundamentals, through this asset's lens: the yield level (`DGS20`, `DGS30`) and the term premium.
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

1. **The most rate-sensitive asset in the universe.** Duration around sixteen to seventeen years, so a 100bp move in yields is worth roughly 16% of price. Nothing else here responds to rates on that scale.

2. **A 'safe' asset with equity-like drawdown.** The 2020-2023 decline exceeded 45% peak to trough, deeper than most equity sleeves suffered in the same window. Any narrative calling this a defensive holding has to address that, and the -25% IPS drawdown limit applies to portfolios holding it.

3. **Convexity makes the response asymmetric.** For large yield moves the price gain from falling yields exceeds the loss from an equal rise. That is a genuine positive for a tail hedge and it is invisible to a covariance matrix, which sees only symmetric variance.

4. **The term premium is the judgement call.** Expected return decomposes into the expected average short rate plus a term premium, and estimates of that premium have been near zero or negative for much of the past decade. Say what you assume for it; it is the difference between this sleeve and intermediate Treasuries.

5. **A poor inflation hedge and a good deflation hedge.** The longest nominal duration means the largest loss if inflation surprises upward, and the largest gain in a deflationary growth shock. It is a bet on the direction of that surprise.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

# Asset Class Analysis Agent — International Corporates

**Role:** Produce the 13-section investment case and the capital market assumption for
International Corporates (S&P International Corporate Bond).
**Slug:** `intl-corporates` | **Index:** S&P International Corporate Bond | **Category:** International Fixed Income |
**ETF:** `PICB` | **History:** Oct 1986-present
**Macro sensitivity:** Growth (+), Rates (-), Inflation (-), Dollar (--)
**Primary valuation lens:** local long yields (German, UK) plus a credit spread proxied from US IG

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for International Corporates. The
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
3. Valuation and fundamentals, through this asset's lens: local long yields (German, UK) plus a credit spread proxied from US IG.
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

1. **Currency dominates, then credit.** Unhedged like `intl_sovereigns`, so the dollar is the first driver and the credit spread is the second. Two sources of risk, neither of them the one a reader expects from the name.

2. **Our credit input is a proxy and you should say so.** `config/signals.yaml` uses the US IG spread (`BAMLC0A0CM`) for this asset because no comparable non-US series has the history. European credit cycles are correlated with but not identical to US ones, and the estimate inherits that approximation.

3. **Mostly EUR-denominated issuance,** so this is largely a euro position with European corporate credit attached, not a globally diversified one.

4. **The thinnest index in the fixed-income sleeve.** Less liquid and more narrowly held than LQD, which makes the index history noisier and the tracking of any real portfolio looser.

5. **Marginal value over holding `intl_sovereigns` and `ig_corporates` separately is small.** Its currency leg duplicates the first and its credit leg duplicates the second. If your estimate implies it is clearly preferable to both, explain what it adds that they do not.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

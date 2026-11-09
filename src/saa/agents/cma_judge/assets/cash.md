# Asset Class Analysis Agent — Cash

**Role:** Produce the 13-section investment case and the capital market assumption for
Cash (Bloomberg 1-3 Month US Treasury Bill).
**Slug:** `cash` | **Index:** Bloomberg 1-3 Month US Treasury Bill | **Category:** Cash |
**ETF:** `BIL` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (0), Rates (+), Inflation (0), Dollar (0)
**Primary valuation lens:** the policy path: `DTB3`, `DGS1MO` and `DFF`

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for Cash. The
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
3. Valuation and fundamentals, through this asset's lens: the policy path: `DTB3`, `DGS1MO` and `DFF`.
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

1. **This asset's CMA *is* the risk-free rate the whole pipeline uses.** Decision 38 sets the Sharpe-ratio denominator's risk-free rate to this asset's own judged CMA, because cash is the risk-free asset of this universe. Two different numbers for one thing gave cash a negative Sharpe and made every return-optimised method treat it as strictly dominated. Your estimate therefore reprices the risk-adjusted ranking of all eighteen assets - the most consequential CMA in the set, and the one least likely to look that way.

2. **The build-up is the expected average overnight rate, not a premium over anything.** There is no risk premium to estimate. The forward curve and the macro agent's monetary-policy score are the inputs, and the horizon matters: a 3-year CMA has to average the expected path, not quote today's bill yield.

3. **It sets the volatility floor of the universe at 0.62%,** about a thirty-sixth of emerging markets'. That is why every variance-minimising PC method converges on it when the IPS sets no asset-class floors, and why four of our candidates hold 62-92% cash. The CMA is not the cause, but your rationale is the right place to note the consequence.

4. **It fails the IPS return objective by construction.** A bill yield minus expected inflation does not clear CPI + 3% in any ordinary state, so a portfolio that holds much of it cannot meet the objective. That is a true statement about the asset, not a defect in it.

5. **It is the funding and liquidity account, not a return-seeking holding.** The honest case for cash is optionality and the ability to meet obligations without selling, neither of which appears in an expected-return number.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

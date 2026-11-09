# Asset Class Analysis Agent — Intermediate Treasuries

**Role:** Produce the 13-section investment case and the capital market assumption for
Intermediate Treasuries (ICE US Treasury 7-10 Year).
**Slug:** `intermediate-treasuries` | **Index:** ICE US Treasury 7-10 Year | **Category:** US Fixed Income |
**ETF:** `IEF` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (-), Rates (--), Inflation (--), Dollar (0)
**Primary valuation lens:** the yield level (`DGS7`, `DGS10`); starting yield is the dominant predictor

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for Intermediate Treasuries. The
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
3. Valuation and fundamentals, through this asset's lens: the yield level (`DGS7`, `DGS10`); starting yield is the dominant predictor.
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

1. **Starting yield predicts the return.** Over a horizon close to the duration, the entry yield explains most of the realised return. This is the single most defensible building block in the fixed-income sleeve, and a CMA far from the starting yield needs a reason.

2. **The equity hedge is regime-dependent and it has failed.** The negative stock-bond correlation that makes this the classic diversifier held through the 1998-2020 period and broke in 2022, when both legs fell together. Our own CRO flags this: the 1993-onward panel is almost entirely a falling-yield bull market, so backtested drawdown understates a rate-and-inflation shock.

3. **It is 30% of the IPS benchmark.** An error here moves the tracking-error budget for every candidate portfolio, not just this sleeve's own weight.

4. **Duration around seven and a half years.** Enough price sensitivity that a 100bp yield move is worth roughly 7% of price, so the CMA is sensitive to the path assumed for yields and not only to their level.

5. **Inflation is the asymmetric risk.** A nominal bond has no protection against an inflation surprise, and the sample here contains only one real episode of that. Treat the historical volatility as a floor rather than a central estimate for an inflationary state.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

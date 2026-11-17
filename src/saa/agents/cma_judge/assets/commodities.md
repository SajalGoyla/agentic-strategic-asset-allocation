# Asset Class Analysis Agent — Commodities

**Role:** Produce the 13-section investment case and the capital market assumption for
Commodities (DBIQ Optimum Yield Diversified Commodity).
**Slug:** `commodities` | **Index:** DBIQ Optimum Yield Diversified Commodity | **Category:** Real Assets |
**ETF:** `DBC` | **History:** Feb 1984-present
**Macro sensitivity:** Growth (+), Rates (0), Inflation (++), Dollar (-)
**Primary valuation lens:** no cash flow: spot prices (`DCOILWTICO`, `DCOILBRENTEU`, `PCOPPUSDM`) plus the collateral rate (`DTB3`)

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for Commodities. The
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
3. Valuation and fundamentals, through this asset's lens: no cash flow: spot prices (`DCOILWTICO`, `DCOILBRENTEU`, `PCOPPUSDM`) plus the collateral rate (`DTB3`).
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

1. **Total return is spot plus roll plus collateral, and the roll is what decides it.** A futures-based index earns the T-bill rate on its collateral, the change in spot, and a roll yield that is negative in contango and positive in backwardation. Over long stretches the roll has dominated. DBC's 'optimum yield' rule exists specifically to choose the contract that minimises contango drag.

2. **A spot price history is not this asset's return history.** This is the most important trap on this asset: using oil or copper price appreciation as a proxy for commodity returns ignores the roll and overstates the result, often by several points a year. Our `cma_series` carries spot series for the signal layer; the return history comes from the fund, not from them.

3. **The best inflation hedge here and the worst risk-adjusted return.** Highest Inflation sensitivity in the universe and an ex-ante Sharpe near 0.09 on our inputs. Its case is a hedging case, and it should be argued as one rather than as a return case.

4. **Energy-weighted, so largely an oil position.** The diversified label understates how much of the variance comes from crude. Judge it partly as an oil exposure with industrial metals and agriculture attached.

5. **No yield and no earnings, so no valuation anchor exists.** There is nothing to be cheap or expensive relative to. Inventory levels, the curve shape and marginal production cost are the closest available substitutes for a valuation signal.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

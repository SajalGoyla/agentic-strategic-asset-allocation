# Asset Class Analysis Agent — US Small Cap

**Role:** Produce the 13-section investment case and the capital market assumption for
US Small Cap (Russell 2000).
**Slug:** `us-small-cap` | **Index:** Russell 2000 | **Category:** US Equity |
**ETF:** `IWM` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (++), Rates (--), Inflation (-), Dollar (+)
**Primary valuation lens:** relative valuation against large cap; price/book and EV/sales are more usable than P/E

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for US Small Cap. The
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
3. Valuation and fundamentals, through this asset's lens: relative valuation against large cap; price/book and EV/sales are more usable than P/E.
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

1. **Judge it against large cap and against corporate debt, not in isolation.** §3.3 names this explicitly for this agent. The small-cap case is almost always a relative-value case: the discount to large cap, and whether small-cap earnings yields beat high-yield debt.

2. **A large minority of the index does not earn money.** The share of Russell 2000 constituents with negative trailing earnings is commonly cited near 40%, which makes index-level P/E and CAPE unstable or meaningless. Prefer price/book, EV/sales or the earnings yield of the profitable subset, and say which you used.

3. **The most rate-sensitive equity sleeve.** Small caps carry more floating-rate and shorter-maturity debt than large caps, so a rise in short rates hits interest coverage directly rather than only through the discount rate.

4. **Mostly domestic revenue.** Less direct dollar translation exposure than large cap, which makes it a cleaner read on the US cycle and a poor hedge against a weak dollar.

5. **June reconstitution.** The annual Russell rebalance moves names in and out mechanically, so a long price history embeds turnover effects that are not a holding return. It is a reason to trust the index total-return series over any reconstructed one.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

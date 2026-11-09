# Asset Class Analysis Agent — US Large Cap

**Role:** Produce the 13-section investment case and the capital market assumption for
US Large Cap (S&P 500 (the paper uses the Bloomberg SPTR Index)).
**Slug:** `us-large-cap` | **Index:** S&P 500 (the paper uses the Bloomberg SPTR Index) | **Category:** US Equity |
**ETF:** `SPY` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (+), Rates (-), Inflation (-), Dollar (+)
**Primary valuation lens:** CAPE and the implied ERP; `market/fund_snapshot` supplies the ETF P/E

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for US Large Cap. The
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
3. Valuation and fundamentals, through this asset's lens: CAPE and the implied ERP; `market/fund_snapshot` supplies the ETF P/E.
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

1. **The S&P 500 is the benchmark.** Most investors compare everything against it, and it is 60% of the IPS benchmark, so an estimate here moves every tracking-error number in the pipeline.

2. **Concentration risk.** The top ten constituents have grown to roughly a third of index weight, so the index is far less diversified than its 500 names suggest and its return is increasingly a few companies' return.

3. **Technology and AI exposure.** Sector composition is heavily tilted toward technology and growth, which is why this sleeve behaves like a long-duration asset and sells off on rising real yields.

4. **Buyback yield is a real CMA component.** Net buybacks have run roughly 1-3% a year, so total shareholder yield materially exceeds the dividend yield. A Gordon-style build that uses dividends alone understates the return (decision 23 uses net payout for this reason).

5. **Dollar strength cuts multinational earnings.** Around 40% of revenue is earned abroad, so a strong dollar is a headwind to earnings even though the index's own return tends to hold up when the dollar rises on safe-haven flows. Do not read the return sign as an earnings sign.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

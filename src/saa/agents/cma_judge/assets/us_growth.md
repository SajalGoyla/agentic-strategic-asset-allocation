# Asset Class Analysis Agent — US Growth

**Role:** Produce the 13-section investment case and the capital market assumption for
US Growth (Russell 1000 Growth).
**Slug:** `us-growth` | **Index:** Russell 1000 Growth | **Category:** US Equity |
**ETF:** `IWF` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (+), Rates (--), Inflation (-), Dollar (+)
**Primary valuation lens:** CAPE and the implied ERP; both will read expensive, and the question is how much to mark down

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for US Growth. The
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
3. Valuation and fundamentals, through this asset's lens: CAPE and the implied ERP; both will read expensive, and the question is how much to mark down.
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

1. **The most expensive sleeve, and the paper's largest markdown.** Exhibit 8 gives US Growth a -2.0% adjustment to the auto-blend, the largest in the universe, with the judge putting 60% weight on valuation methods and 5% on the historical ERP. If your markdown here is not the largest of the equity sleeves, justify why.

2. **Longest-duration equity in the universe.** The most rate-sensitive equity sleeve on the discount-rate channel, as distinct from US Small Cap's coverage-ratio channel.

3. **Extreme concentration.** The top ten names can exceed half the index, so this is a concentrated position in a handful of mega-cap technology companies, not a diversified growth exposure. Effective breadth is far below the nominal constituent count.

4. **Valuation methods can produce very low or negative estimates.** When the earnings yield sits near or below the risk-free rate, the implied-ERP and inverse-Gordon builds return an equity premium near zero. That is information, not an error, but it is also why the candidate range for this asset is the widest in the universe. Do not let one extreme candidate drag the blend without saying so.

5. **It overlaps US Large Cap almost completely.** The two correlate above 0.9, so growth is a tilt on top of large cap rather than a separate holding. A portfolio holding both is concentrating, and the PC agents will not see that unless the CMAs make the overlap clear.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

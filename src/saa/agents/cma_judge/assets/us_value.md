# Asset Class Analysis Agent — US Value

**Role:** Produce the 13-section investment case and the capital market assumption for
US Value (Russell 1000 Value).
**Slug:** `us-value` | **Index:** Russell 1000 Value | **Category:** US Equity |
**ETF:** `IWD` | **History:** Jan 1980-present
**Macro sensitivity:** Growth (+), Rates (+), Inflation (+), Dollar (0)
**Primary valuation lens:** the value-growth spread; dividend yield carries more of the total return

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for US Value. The
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
3. Valuation and fundamentals, through this asset's lens: the value-growth spread; dividend yield carries more of the total return.
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

1. **Short-duration equity.** Value's cash flows arrive sooner than growth's, so it is the one equity sleeve that can benefit from higher rates. Expect its sign on Rates to be the opposite of US Growth's, and treat an estimate that implies otherwise as suspect.

2. **Sector composition is the exposure.** Financials, energy and industrials dominate, so this is partly a bet on bank net interest margins and on the oil price rather than on a style premium in the abstract.

3. **Book value measures less than it used to.** Value screens built on book value penalise firms whose capital is intangible, and intangible investment has grown as a share of the economy. A wide book-based value spread may be a measurement artefact rather than an opportunity. Say which reading you take.

4. **Dividend yield is a larger share of expected return** than for the other equity sleeves, which makes the inverse-Gordon build more reliable here than it is for growth.

5. **Style indices overlap.** Russell splits some companies across both the Value and Growth indices, so this sleeve and `us_growth` are not mutually exclusive holdings and their combined weight double-counts those names.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

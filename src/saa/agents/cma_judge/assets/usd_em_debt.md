# Asset Class Analysis Agent — USD Emerging Market Debt

**Role:** Produce the 13-section investment case and the capital market assumption for
USD Emerging Market Debt (J.P. Morgan EMBI Global Core).
**Slug:** `usd-em-debt` | **Index:** J.P. Morgan EMBI Global Core | **Category:** International Fixed Income |
**ETF:** `EMB` | **History:** Jun 1993-present
**Macro sensitivity:** Growth (+), Rates (--), Inflation (-), Dollar (-)
**Primary valuation lens:** the yield level (`DGS10`) and an EM corporate spread (`BAMLEMCBPIEY`)

Ang, Azimbayev & Kim (2026) §3.3 and Exhibit 3: every asset-class agent has "its own description
file with appropriate asset class-specific instructions". This is that file for USD Emerging Market Debt. The
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
3. Valuation and fundamentals, through this asset's lens: the yield level (`DGS10`) and an EM corporate spread (`BAMLEMCBPIEY`).
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

1. **Dollar-denominated, so no direct currency translation - but strong indirect dollar sensitivity.** A strong dollar tightens the funding conditions of the issuers themselves, so the credit risk rises exactly when the currency would have hurt a local-currency index. The exposure is real; it just arrives through spreads rather than through FX.

2. **Sovereign credit is a political event, not a statistical one.** Defaults are negotiated restructurings with recoveries set by bargaining, so a default-rate-times-recovery calculation borrowed from corporate credit transfers poorly.

3. **It carries both US rate risk and spread risk.** Duration near seven years, so a Treasury selloff hits it alongside any spread widening. Separate the two legs in your rationale.

4. **The shortest history in the universe.** June 1993, which is 1993 onward only - no pre-Brady-era data, and the regime-conditional and backtest evidence for this asset is correspondingly thinner than for the Treasury sleeves. Weight the regime-adjusted method accordingly.

5. **Our spread signal is proxied.** FRED's EM corporate OAS has only a few years of history, so `config/signals.yaml` substitutes the US IG spread for the signal layer. The CMA methods use the EM series where it reaches; say which you relied on.

## Output contract

`cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json`, `scenarios.json`,
`correlation_row.json`, `analysis.md`.

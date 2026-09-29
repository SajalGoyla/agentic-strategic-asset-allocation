# CMA Methods Skill

Used by: the CMA judge (the LLM half of every asset-class agent, stage 2). Paper reference: Ang,
Azimbayev & Kim (2026) §3.3 and Exhibit 4. The candidates "are written to a cma_methods.json
file by a Python script; no LLM judgment is involved up to this point."

## What it does

Computes every candidate expected return for each of the 18 assets from point-in-time data,
writes one `cma/<asset>/cma_methods.json` per asset and a run-level table,
`reports/cma_methods.md`. It is deterministic and uses no LLM. The judge then picks within the
candidates' range, a range the `cma` contract enforces.

```bash
uv run saa-skill cma-methods                                  # all 18 assets, today
uv run saa-skill cma-methods --as-of 2020-04-01               # point-in-time
uv run saa-skill cma-methods --assets us_large_cap ig_corporates cash
uv run saa-skill cma-methods --run-id <run>                   # reuse that run's covariance.json
uv run saa-skill cma-methods --regime-history data/runs/<run>/macro/regime_history.json
```

Without `--regime-history`, the CLI scores the regime history itself with the macro skill.
When the run already has `pc/covariance.json`, the skill uses that file for Black-Litterman and
for volatilities, so stage 2 and the PC stage see the same matrix. Otherwise it computes the
covariance skill's default.

## Convention

Every candidate is the **arithmetic expected annual return, nominal, in percent**. Optimisers
consume arithmetic means, and the historical and Black-Litterman methods produce them natively.
Methods whose natural output is compound (a yield, a Gordon sum, a survey of average annual
returns) add half the variance, which appears as the `variance_addback_pct` component. At 15%
volatility that adds about 1.1pp. A method that does not apply, or lacks fresh data, is listed
with `unavailable_reason`, no number and zero confidence, so every file lists the same eight
methods in the same order.

## Methods

| Method | Applies to | Formula | Main input |
|---|---|---|---|
| `historical_erp` | all | mean monthly excess return over T-bills since 1990 x 12 + current T-bill | spliced returns, DTB3 |
| `regime_adjusted` | all | credibility-weighted excess return over the **3 years after** past months in today's regime + T-bill | macro-skill labels |
| `bl_equilibrium` | all | T-bill + δ Σ w, with w = ETF AUM shares and δ = 2.5 | covariance, fund snapshot |
| `inverse_gordon` | equity, REITs | yield + SPF real GDP + SPF CPI + valuation change + ½σ² | Shiller (US LC), ETF yield |
| `implied_erp_cape` | equity, REITs | earnings yield + SPF CPI + ½σ² | 1/CAPE (US LC), ETF E/P |
| `survey_consensus` | US LC, Int. Treasuries, cash | SPF STOCK10 / BOND10 / BILL10 + ½σ² | SPF |
| `yield_building_block` | fixed income, cash | starting yield (+ spread) − expected credit loss + ½σ² | FRED yields |
| `auto_blend` | all | confidence-weighted mean of the available methods | — |

`yield_building_block` is §3.3's "fixed-income CMA builder". Exhibit 4's six methods are written
for equities, and for bonds the starting yield is the best single predictor of return over a
horizon near duration. Yield recipes, credit losses and confidences live in `config/cma.yaml`,
each tagged with its provenance.

## Choices made, with evidence (real data, as of 2026-09-29)

- **Regime premium is predictive.** Averaging the returns *during* past months in a regime uses
  hindsight, because a recession label arrives with the crash already in it. For US Large Cap
  in expansion, the contemporaneous average gave +13.7% excess and a 16.5% candidate. Using the
  three years *after* each expansion month gives +9.7%, which is close to the paper's 9.8%
  regime-adjusted figure.
- **Risk aversion 2.5, not calibrated.** Calibrating δ as the AUM portfolio's historical Sharpe
  over its volatility gives 5.4 on 1990-2026, a sample with unusually strong equity returns. That
  scales every equilibrium premium by 2.2x (US LC 13.1%, against the paper's 9.3%). At the
  literature's 2.5 the figure is 8.2%. `risk_aversion: historical` in `cma.yaml` restores the
  calibration.
- **CAPE anchor is the post-1990 median (26.4), not the 1881 median (16.6).** Against the older
  anchor, CAPE 40 implies −8.4% a year of valuation drift for a decade.

US Large Cap, compared with Exhibit 8 (paper, as of its own date):

| | Hist | Regime | BL | Gordon | CAPE | Survey | Blend |
|---|---|---|---|---|---|---|---|
| Paper | 12.5 | 9.8 | 9.3 | 4.3 | 4.0 | — | 7.9 |
| Ours | 12.6 | 13.5 | 8.2 | 2.5 | 5.9 | 8.1 | 8.1 |

Our regime figure adds the 3.97% T-bill to the 9.7% premium, then shrinks it toward the
unconditional premium.

## How the judge should read it

- `method_range` bounds the final estimate. Wide dispersion (>6pp, as for US Large Cap) is
  the signal to lean on regime and valuation logic (Exhibit 4 steps 1-3).
- Read `components` rather than the headline. For example, the Gordon figure is low because
  of the valuation-change term, not the yield.
- Confidence is a heuristic prior, not a statistical measure. It is lower for proxy inputs
  (ETF P/E instead of CAPE, Moody's instead of ICE yields), for unhedged foreign yields, and
  for the historical bond methods, because 1990-2026 was a secular fall in yields.

## Caveats

- **No buyback yield yet.** The Gordon yield is dividends only, 1.1% for the S&P 500.
  Buybacks add about 2pp, which is why our Gordon figure is below the paper's 4.3%. Compustat
  (WRDS) ingestion is next on the plan.
- **ETF AUM is not market size.** SPY alone is 49% of the 18 ETFs' AUM, so Black-Litterman
  is really "equilibrium relative to what ETF investors hold".
- **One fund snapshot so far.** Black-Litterman and the non-US-LC valuation methods are
  unavailable for any `--as-of` before the first snapshot (2026-09-15) until WRDS market caps
  replace AUM.
- **SPF growth is US growth**, applied to international equity too, at reduced confidence.
- **International bond yields are local.** BWX and PICB are unhedged, so their USD return
  also carries currency moves this method does not forecast.
- **USD EM debt uses the ICE EM corporate yield**, the only free EM yield. EMB holds
  sovereigns.

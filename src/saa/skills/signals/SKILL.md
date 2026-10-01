# Signals Skill

Used by: the CMA judge (stage 2). Paper reference: Ang, Azimbayev & Kim (2026) Exhibit 3
steps 3–5 and Exhibit 4, which lists `signals.json` among the judge's inputs as "asset-level
macro, technical, valuation signals".

Deterministic: no LLM. The paper names the signals but publishes no definitions or weights, so
everything here is ours and lives in `config/signals.yaml`.

```bash
uv run saa-skill signals                        # all 18 assets, today
uv run saa-skill signals --as-of 2020-04-01     # point-in-time
uv run saa-skill signals --assets us_large_cap cash
```

## Convention

Every signal is scored to **[-1, +1], where +1 is bullish for that asset's forward return**,
against the signal's own trailing history: z-score over 20 years, squashed with `tanh(z/2)`,
the same mapping the macro skill uses so the two are read the same way.

Reading the sign consistently matters more than any individual definition. A high earnings
yield is cheap and therefore bullish. A wide credit spread compensates more and is therefore
bullish. A stretched three-year return enters negatively, because it tends to revert.

## Signals

| Category | Signal | Definition | Applies to |
|---|---|---|---|
| technical | `momentum_12_1` | 12-month return skipping the last month (Jegadeesh–Titman, avoiding one-month reversal) | all |
| technical | `trend` | price against its 10-month moving average | all |
| technical | `mean_reversion` | 36-month return, **inverted** | all |
| technical | `relative_momentum` | momentum ranked against the other 17 assets | all |
| valuation | `cape` | Shiller CAPE, **inverted** | US Large Cap |
| valuation | `yield_level` | starting yield against its own history | fixed income, cash |
| valuation | `credit_spread` | OAS against its own history | credit assets |
| macro | `regime_fit` | mean return in past months of today's regime, against the asset's unconditional mean | all with labels |
| macro | `<dimension>_alignment` | correlation with each macro dimension score × that dimension's level today | all with labels |

## What is deliberately absent

- **Sentiment.** Exhibit 3 step 5 sources fund flows and positioning from web search at
  runtime. The pipeline does not do web search yet, so the category is omitted rather than
  faked with a proxy.
- **An earnings-yield signal for equities outside US Large Cap.** `market/fund_snapshot` only
  accumulates from the first ingest, so there is not yet enough history to say whether today's
  reading is cheap or expensive. A signal scored 0.0 is not neutral evidence — it would pull
  the valuation category toward zero and take weight away from signals that do carry
  information. The judge still sees these valuations through `cma_methods.json`, where
  `inverse_gordon` and `implied_erp_cape` consume them directly.
- **A separate earnings yield for US Large Cap.** It is 1/CAPE; emitting both would weight one
  piece of evidence twice.

## Composite

A weighted mean within each category, then a weighted mean across categories
(technical 0.35, valuation 0.40, macro 0.25), **renormalised over the categories that produced
signals**. An asset with no valuation signal is scored on technical and macro alone rather than
being dragged toward zero by an absent category — the same rule the macro skill applies to a
thin dimension.

## Outputs

`cma/<asset>/signals.json` per asset and `reports/signals.md` for the run.

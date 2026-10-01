# Covariance Skill

Used by: the covariance agent (stage 3), the Black-Litterman CMA method (implied returns need a
covariance matrix), every portfolio-construction agent, and the CRO agent (ex-ante volatility
and tracking error). Paper reference: Ang, Azimbayev & Kim (2026) §3.1 step 3 — "A covariance
agent estimates the asset class covariance matrix using historical data and macro forecasts."

## What it does

Computes every candidate estimator of the annualised 18 x 18 covariance matrix on the same
point-in-time data, writes the chosen one as `pc/covariance.json`, and writes a comparison of
all of them to `reports/covariance.md` so the choice is auditable. Deterministic; no LLM.

```bash
uv run saa-skill covariance                                   # Ledoit-Wolf, all history, today
uv run saa-skill covariance --as-of 2020-04-01                # point-in-time
uv run saa-skill covariance --method exponential --halflife-months 60
uv run saa-skill covariance --method regime_conditional \
    --regime-history data/runs/<run>/macro/regime_history.json --regime recession
```

## Estimators

| Method | What it does | When it helps |
|---|---|---|
| `ledoit_wolf` (default) | Sample covariance shrunk toward a constant-correlation target: each asset keeps its own variance, correlations are pulled toward their average by an analytically optimal amount (Ledoit & Wolf 2004) | Always safe; repairs singular samples |
| `sample` | Unbiased sample covariance over the window | Long windows with no shared proxies |
| `exponential` | Recent months weigh more; a month `halflife_months` old counts half | Reacting to a change in volatility regime |
| `regime_conditional` | Ledoit-Wolf on only the months the macro agent labelled with the given regime | The "macro forecasts" route of §3.1: e.g. recession-state correlations |

The constant-correlation target matters here: asset-class volatilities run from 0.6% (cash) to
over 20% (equities, REITs), and an identity-style target would drag them toward each other.

## Units

`matrix` is decimal-squared — a 20% volatility is a variance of 0.04 — which is what optimisers
consume. `volatilities_pct` is percent, and the contract validator checks the two agree, so a
matrix written in percent-squared (100x off) is rejected rather than silently used.

## Why these defaults: out-of-sample evidence

Tested on real 1993-2026 data. At each year-end, each estimator was fitted on data up to that
date only; the minimum-variance portfolio of the 17 risky assets was formed from it, and its
realised volatility over the next 12 months measured (the standard test: a better risk forecast
gives a lower realised volatility). Also measured: the error forecasting the 60/30/10
benchmark's volatility, matrix conditioning, and how often the matrix was singular.

On the 18 years every estimator could handle (2008-2025):

| Estimator | Min-variance realised vol | Benchmark vol error | Condition number | Gross leverage | Singular years (of 22) |
|---|---|---|---|---|---|
| Exponential, 60-month half-life | 0.86% | 3.42 pp | 4,309 | 1.83 | 4 |
| Ledoit-Wolf, 5 years | 0.89% | 3.91 pp | 3,292 | 1.33 | 0 |
| Exponential, 36-month half-life | 0.88% | 3.50 pp | 6,566 | 1.84 | 4 |
| **Ledoit-Wolf, all history** | 0.92% | **3.31 pp** | **1,691** | 1.49 | **0** |
| Sample, 10 years | 0.96% | 3.41 pp | 10,159 | 1.94 | 4 |
| Ledoit-Wolf, 10 years | 0.96% | 3.45 pp | 2,759 | 1.38 | 0 |
| Exponential, 12-month half-life | 0.97% | 3.84 pp | 15,778 | 2.14 | 4 |

Reading it:

- **Risk forecasts are close.** Realised volatilities span about 0.1 percentage points — within
  noise over 18 annual observations — so forecasting skill alone does not pick a winner.
- **Robustness decides it.** Sample and exponential estimators were singular in every year
  before 2008, because International Sovereigns and International Corporates share a proxy fund
  (identical returns) until 2007. That rules them out for the first twelve years of the paper's
  1996-2026 backtest. Ledoit-Wolf was never singular.
- **Ledoit-Wolf over all history** gave the best-conditioned matrices, the most accurate
  benchmark-volatility forecast, and moderate leverage, so optimisers built on it behave.
- **Exponential weighting** is kept as the reactive alternative, with a 60-month half-life,
  which beat 36, 24 and 12.

## Outputs

```
runs/<pipeline_run_id>/pc/covariance.json     the chosen estimator (contract `covariance`)
runs/<pipeline_run_id>/reports/covariance.md  every estimator side by side
```

`write_outputs` refuses a matrix that is not numerically positive definite (smallest eigenvalue
below 1e-10 of the largest); a plain `> 0` eigenvalue test passes rank-deficient matrices whose
smallest eigenvalue is 1e-20, which an optimiser then fails to invert.

## How agents should use it

- **Covariance agent:** start from `ledoit_wolf`; compare `exponential` in the report to judge
  whether volatility is currently elevated; use `regime_conditional` when the macro agent calls
  a recession, where correlations rise and diversification thins.
- **CMA agents (Black-Litterman):** implied returns are `risk_aversion x matrix x market_weights`;
  read the matrix in decimal units.
- **PC agents and CRO:** portfolio volatility is `100 * sqrt(w' matrix w)` percent.

## Caveats

- **Forecasts run high.** Every estimator over-predicted next-year benchmark volatility by a
  median 11-27%: long windows include 2008 and 2020, and most following years were calmer.
  Treat the IPS 8-12% volatility band with that bias in mind.
- **Regime-conditional estimates rest on few months.** Recessions since 1993 total a few dozen
  months, fewer than needed for 18 assets without shrinkage; the estimator always shrinks and
  refuses fewer than 24 months.
- **Pre-ETF months are proxies**, so early-sample correlations inherit their tracking error
  (`docs/asset_data_map.md`).

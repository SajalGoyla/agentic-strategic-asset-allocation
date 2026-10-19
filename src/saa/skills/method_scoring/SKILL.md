# Method Scoring Skill

Used by: the Borda vote (stage 5, the "quantitative metric score" it blends with the points)
and the CIO agent (stage 6, its six-dimension rubric). Paper reference: Ang, Azimbayev & Kim
(2026) §3.5 and §4.4.

## What it does

Scores every candidate portfolio on the paper's six dimensions, each 0-1, and combines them
with the paper's weights. The paper uses this one rubric twice -- the vote's metric score is "a
weighted composite of backtest Sharpe, IPS compliance, diversification, regime fit, estimation
risk, and CMA utilization" (§3.5), and the CIO "scores each of the 21 PC methods on six
dimensions" with the same list (§4.4) -- so it is computed once, here, and both read it.
Deterministic: no LLM.

```bash
uv run saa-skill method-scores --run-id <run>     # after saa-agent pc and saa-agent cro
```

It reads `pc/<agent>/pc_proposal.json` and `review/<agent>/cro_report.json`, and writes
`reports/method_scores.md`. The scores are `MethodScore` objects (`contracts/cio.py`), which
validate the composite against the §4.4 weights; the vote tally and the CIO decision embed
them, so the skill writes no contract of its own.

## The six dimensions

| Dimension | Weight | Measured as |
|---|---|---|
| backtest Sharpe | 25% | the CRO's backtest Sharpe, linear from 0.0 → 0 to 0.8 → 1, clipped |
| IPS compliance | 15% | 1.0 if compliant; each hard breach costs 0.25-0.5 by how far past the limit (an overshoot of 20% of the limit or more costs the full 0.5); a soft one 0.1 |
| diversification | 15% | Meucci effective number of assets over the number available; 1/N scores 1 |
| regime fit | 20% | the portfolio's backtest Sharpe over past months in today's regime, **relative to the roster**: lowest 0, highest 1. A per-family prior where there are fewer than 24 such months |
| estimation robustness | 15% | a per-method table: 1/N estimates nothing (1.0), maximum Sharpe "maximises estimation error" (0.2) |
| CMA utilization | 10% | half for reading the CMAs at all, half for how far the active weights lean toward the assets with the best CMA Sharpe ratios (rank correlation, mapped to 0-1) |

Every threshold is in `config/method_scoring.yaml`, tagged `[paper]`, `[literature]` or
`[proposed]`; the `[proposed]` ones are to be calibrated after the first paid run.

## Choices, with evidence

- **Backtest Sharpe is absolute; regime fit is relative.** An absolute scale keeps a score's
  meaning the same from run to run and stops a weak roster flattering itself. But the regime
  moves every portfolio together: on the 2026-10-01 free run every candidate's Sharpe in past
  expansion months was above 0.8, so an absolute scale gave 13 of 15 a regime fit of 1.00.
  Ranked against the roster it spans 0-1 and separates them -- maximum Sharpe and the
  adversarial diversifier did best in expansions, HRP and inverse variance worst.
- **Estimation robustness is a table, not a measurement.** Measuring it means re-running every
  optimiser under many perturbed inputs (the resampled frontier alone is 200 optimisations);
  the ordering is well established in the literature, and the table is one line per method.
- **The researcher is scored by the method it ran**, found by name, since its agent id says
  nothing about how robust or CMA-dependent its portfolio is.

## Caveats

- Regime fit is in-sample: it reads the same 1993-2026 history the CRO backtests.
- Regime labels are scored from the latest data vintage unless a `regime_history.json` from a
  point-in-time macro run is passed (`--regime-history`).
- A dimension that cannot be measured scores 0.5 (backtest Sharpe with no backtest, regime fit
  with no labels falls to the prior) and is listed in the score's details.

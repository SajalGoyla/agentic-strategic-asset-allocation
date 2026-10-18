# Risk Skill

Used by: the CRO agent (stage 5). Paper reference: Ang, Azimbayev & Kim (2026) §3.5, which
lists what a risk report has to cover — "ex-ante and back-test volatility, value-at-risk,
maximum drawdown, concentration metrics, factor tilts, and IPS compliance".

Deterministic: no LLM. The CRO agent reads what this produces and writes the assessment.

```bash
uv run saa-agent cro --run-id <run> --no-llm   # every candidate's metrics, no spend
uv run saa-agent cro --run-id <run>            # with the CRO's commentary
```

## What it computes, per candidate portfolio

| Figure | How | Units |
|---|---|---|
| ex-ante volatility | weights against the covariance matrix the PC agents optimised over | % |
| ex-ante tracking error | active weights against the same matrix, vs. the IPS benchmark | % |
| backtest volatility | the weights held through history, rebalanced quarterly | % |
| backtest Sharpe | annualised mean excess return over annualised excess volatility | ratio |
| value-at-risk | historical 95% VaR of **monthly** returns, as a positive loss | % |
| conditional VaR | mean of the months at or below that quantile, as a positive loss | % |
| maximum drawdown | deepest peak-to-trough decline of the held portfolio, negative | % |
| effective N | Meucci (2009) exponential of the entropy of the weights | count |
| concentration | Herfindahl index of the weights | 0–1 |
| factor tilts | active weight by asset-class group, plus realised benchmark beta | decimals |
| IPS compliance | `saa.ips.check_compliance`, the same function the PC agents called | — |

Two conventions the paper leaves open and this skill fixes: **VaR is monthly**, stated as a
positive loss, and **drawdown is negative**, so it compares directly with the IPS limit it is
checked against. The contract's validators enforce both signs.

## The backtest

The report is a point-in-time assessment of a proposed portfolio, so the backtest holds the
proposed weights and rebalances them on the IPS cadence (quarterly) rather than re-optimising
month by month. Between rebalances the weights drift with the assets, which is what a
quarterly-rebalanced portfolio actually holds. The panel is the monthly returns of the 18 asset
classes over every month they share (from 1993-06) through `as_of` — the same panel the
non-traditional PC methods optimise over. Under 36 months there is no distribution worth
quoting, and every backtest figure comes back `None`.

This is deliberately *not* the Phase 4 backtest, which re-runs the pipeline through history.
Here the weights are fixed and only the realised path is new.

**Ex-ante and backtest volatility can disagree, and both are reported rather than reconciled.**
Ex-ante is Ledoit–Wolf shrunk over all history; the backtest is the realised path of one
particular 30-odd years. A wide gap is a finding about the covariance estimate, which is
exactly what the CRO should be commenting on.

## The risk score

One number in [0, 1], higher is riskier, blended from five components each in [0, 1]:

| Component | Weight | Measured against |
|---|---|---|
| volatility | 30% | position in the IPS volatility band (floor → 0, ceiling → 1) |
| drawdown | 25% | the IPS −25% drawdown limit |
| tail | 15% | the monthly VaR a portfolio at the IPS ceiling would show if normal |
| tracking error | 15% | the IPS 6% ex-ante tracking-error budget |
| concentration | 15% | Herfindahl, scaled from equal weight (0) to a single asset (1) |

Every component is the portfolio measured against a limit the IPS actually states, so the score
is reproducible from the run inputs and comparable across candidates — which is what the CIO
needs when it blends the CRO's score with the vote (§3.5). It is computed, not judged
(decision 34): the model's job is to say which risk binds, not to assign the number.

Two rules worth stating:

- **A portfolio below the volatility floor scores 0 on that component.** It is non-compliant,
  but it is not risky. Conflating the two would make the cash-heavy risk-based portfolios read
  as the most dangerous in the roster, which is backwards.
- **A missing component is dropped and the rest renormalise** — the same rule the signals
  composite uses. A candidate with no backtest is scored on what it has, never credited with
  zero risk for data it lacks.

## Factor tilts

The paper reports factor tilts without defining them, and this universe is asset classes rather
than factor sleeves. So the tilts are exposure against the benchmark: active weight in each
group (`active_equity`, `active_fixed_income`, `active_real_assets`, `active_cash`), which sum
to zero by construction, plus `benchmark_beta`, the realised beta of the backtest against the
benchmark held the same way. Beta is absent when there is no backtest.

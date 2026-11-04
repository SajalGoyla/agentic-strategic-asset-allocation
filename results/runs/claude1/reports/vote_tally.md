# Vote tally

15 ballots. Regime **expansion**: vote weight 0.60, metric weight 0.40. Composite rescaled 1.000 (top) to 0.000 (bottom), as Exhibit 9.

| rank | agent | family | vote points | metric | composite | shortlist |
|---|---|---|---|---|---|---|
| 1 | resampled_efficient_frontier | return_optimized | 68 | 0.802 | 1.000 | yes |
| 2 | black_litterman | return_optimized | 51 | 0.788 | 0.846 | yes |
| 3 | pc_researcher | pc_researcher | 45 | 0.657 | 0.727 | yes |
| 4 | cvar_minimization | non_traditional | 37 | 0.681 | 0.671 | yes |
| 5 | max_sharpe | return_optimized | 11 | 0.693 | 0.453 |  |
| 6 | equal_weight | heuristic | 0 | 0.754 | 0.390 | yes |
| 7 | volatility_targeting | heuristic | 0 | 0.729 | 0.377 |  |
| 8 | tail_risk_parity | non_traditional | 8 | 0.489 | 0.322 |  |
| 9 | inverse_volatility | heuristic | 2 | 0.547 | 0.301 |  |
| 10 | market_cap_weight | heuristic | -8 | 0.693 | 0.290 |  |
| 11 | risk_parity | risk_structured | 3 | 0.499 | 0.285 |  |
| 12 | maximum_diversification | risk_structured | 0 | 0.456 | 0.236 |  |
| 13 | inverse_variance | heuristic | 0 | 0.447 | 0.231 |  |
| 14 | adversarial_diversifier | non_traditional | 0 | 0.276 | 0.143 |  |
| 15 | hierarchical_risk_parity | risk_structured | -22 | 0.365 | 0.000 |  |

Shortlist (3 of 4 families): resampled_efficient_frontier, black_litterman, pc_researcher, cvar_minimization, equal_weight.

## Diversity rule

- equal_weight (heuristic, rank 6) replaces max_sharpe (return_optimized, rank 5) so the shortlist spans 3 families

## Dissent

- **hierarchical_risk_parity** was bottom-flagged on 11 of 15 ballots.

# Vote tally

15 ballots. Regime **expansion**: vote weight 0.60, metric weight 0.40. Composite rescaled 1.000 (top) to 0.000 (bottom), as Exhibit 9.

| rank | agent | family | vote points | metric | composite | shortlist |
|---|---|---|---|---|---|---|
| 1 | resampled_efficient_frontier | return_optimized | 65 | 0.802 | 1.000 | yes |
| 2 | black_litterman | return_optimized | 55 | 0.788 | 0.893 | yes |
| 3 | pc_researcher | pc_researcher | 48 | 0.657 | 0.752 | yes |
| 4 | cvar_minimization | non_traditional | 30 | 0.681 | 0.588 | yes |
| 5 | max_sharpe | return_optimized | 14 | 0.693 | 0.436 |  |
| 6 | equal_weight | heuristic | 0 | 0.754 | 0.331 | yes |
| 7 | volatility_targeting | heuristic | 0 | 0.729 | 0.318 |  |
| 8 | tail_risk_parity | non_traditional | 8 | 0.489 | 0.265 |  |
| 9 | inverse_volatility | heuristic | 3 | 0.547 | 0.248 |  |
| 10 | risk_parity | risk_structured | 2 | 0.499 | 0.212 |  |
| 11 | maximum_diversification | risk_structured | 0 | 0.456 | 0.168 |  |
| 12 | inverse_variance | heuristic | 0 | 0.447 | 0.163 |  |
| 13 | market_cap_weight | heuristic | -18 | 0.693 | 0.120 |  |
| 14 | adversarial_diversifier | non_traditional | 0 | 0.276 | 0.070 |  |
| 15 | hierarchical_risk_parity | risk_structured | -12 | 0.365 | 0.000 |  |

Shortlist (3 of 4 families): resampled_efficient_frontier, black_litterman, pc_researcher, cvar_minimization, equal_weight.

## Diversity rule

- equal_weight (heuristic, rank 6) replaces max_sharpe (return_optimized, rank 5) so the shortlist spans 3 families

## Dissent

- **market_cap_weight** was bottom-flagged on 9 of 15 ballots.

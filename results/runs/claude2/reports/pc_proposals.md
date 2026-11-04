# Portfolio Construction Proposals

As of 2026-10-01, regime **expansion**

| agent | category | return % | vol % | Sharpe | eff. N | TE % | IPS |
|---|---|---|---|---|---|---|---|
| equal_weight | heuristic | 6.84 | 8.41 | 0.36 | 18.0 | 4.36 | pass |
| inverse_volatility | heuristic | 5.03 | 3.11 | 0.39 | 7.6 | 6.90 | FAIL |
| inverse_variance | heuristic | 4.02 | 0.73 | 0.27 | 1.9 | 9.12 | FAIL |
| market_cap_weight | heuristic | 7.59 | 11.78 | 0.32 | 7.0 | 3.68 | pass |
| volatility_targeting | heuristic | 7.02 | 8.90 | 0.36 | 17.0 | 4.40 | pass |
| max_sharpe | return_optimized | 7.54 | 8.00 | 0.46 | 3.8 | 3.87 | pass |
| black_litterman | return_optimized | 7.06 | 8.00 | 0.41 | 6.1 | 3.01 | pass |
| resampled_efficient_frontier | return_optimized | 7.11 | 8.00 | 0.41 | 13.3 | 4.33 | pass |
| risk_parity | risk_structured | 4.60 | 1.97 | 0.39 | 4.7 | 7.86 | FAIL |
| hierarchical_risk_parity | risk_structured | 3.91 | 0.65 | 0.14 | 1.4 | 9.27 | FAIL |
| maximum_diversification | risk_structured | 4.24 | 1.23 | 0.34 | 2.1 | 8.66 | FAIL |
| cvar_minimization | non_traditional | 6.46 | 8.00 | 0.33 | 2.9 | 3.60 | pass |
| tail_risk_parity | non_traditional | 4.79 | 2.47 | 0.39 | 6.0 | 7.47 | FAIL |
| pc_researcher | pc_researcher | 5.75 | 3.82 | 0.51 | 7.2 | 6.24 | FAIL |
| adversarial_diversifier | non_traditional | 4.70 | 1.69 | 0.52 | 1.0 | 9.30 | FAIL |

## Weights

| asset | equal_weight | inverse_volatility | inverse_variance | market_cap_weight | volatility_targeting | max_sharpe | black_litterman | resampled_efficient_frontier | risk_parity | hierarchical_risk_parity | maximum_diversification | cvar_minimization | tail_risk_parity | pc_researcher | adversarial_diversifier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| us_large_cap | 5.6% | 1.9% | 0.1% | 48.8% | 5.9% | 0.0% | 18.8% | 0.2% | 1.1% | 0.0% | 0.0% | 45.4% | 1.4% | 0.2% | 0.0% |
| us_small_cap | 5.6% | 1.5% | 0.1% | 4.8% | 5.9% | 0.0% | 5.0% | 5.3% | 0.9% | 0.0% | 1.4% | 0.0% | 1.1% | 1.9% | 0.0% |
| us_value | 5.6% | 1.9% | 0.1% | 5.0% | 5.9% | 46.0% | 13.6% | 9.8% | 1.1% | 0.0% | 0.0% | 0.0% | 1.3% | 10.7% | 0.0% |
| us_growth | 5.6% | 1.7% | 0.1% | 7.5% | 5.9% | 4.3% | 6.7% | 9.4% | 1.0% | 0.0% | 1.3% | 0.0% | 1.3% | 3.8% | 0.0% |
| intl_developed | 5.6% | 1.8% | 0.1% | 4.8% | 5.9% | 0.0% | 0.0% | 3.4% | 0.9% | 0.0% | 0.0% | 0.0% | 1.2% | 0.5% | 0.0% |
| emerging_markets | 5.6% | 1.3% | 0.1% | 1.9% | 5.9% | 0.0% | 1.8% | 3.9% | 0.7% | 0.0% | 0.0% | 0.0% | 1.0% | 0.7% | 0.0% |
| short_treasuries | 5.6% | 16.8% | 11.4% | 1.6% | 5.9% | 22.3% | 0.0% | 14.5% | 14.3% | 6.4% | 5.5% | 1.4% | 16.9% | 42.8% | 100.0% |
| intermediate_treasuries | 5.6% | 4.4% | 0.8% | 2.5% | 5.9% | 0.0% | 37.4% | 5.4% | 3.5% | 0.3% | 0.0% | 37.3% | 4.1% | 9.5% | 0.0% |
| long_treasuries | 5.6% | 2.3% | 0.2% | 2.8% | 5.9% | 21.8% | 9.7% | 14.1% | 2.1% | 0.1% | 4.5% | 0.0% | 2.2% | 4.5% | 0.0% |
| ig_corporates | 5.6% | 4.0% | 0.6% | 1.9% | 5.9% | 0.0% | 0.0% | 4.3% | 2.1% | 0.3% | 0.0% | 0.0% | 3.2% | 4.0% | 0.0% |
| hy_corporates | 5.6% | 3.4% | 0.5% | 1.0% | 5.9% | 0.0% | 0.0% | 3.4% | 1.8% | 0.1% | 0.0% | 0.0% | 2.6% | 3.0% | 0.0% |
| intl_sovereigns | 5.6% | 3.4% | 0.5% | 0.1% | 5.9% | 0.0% | 0.0% | 0.1% | 1.8% | 0.4% | 0.0% | 0.0% | 2.7% | 0.1% | 0.0% |
| intl_corporates | 5.6% | 3.1% | 0.4% | 0.0% | 5.9% | 0.0% | 0.0% | 1.9% | 1.6% | 0.2% | 0.0% | 0.0% | 2.3% | 0.3% | 0.0% |
| usd_em_debt | 5.6% | 2.0% | 0.2% | 0.9% | 5.9% | 0.0% | 0.0% | 3.7% | 1.1% | 0.1% | 0.0% | 0.0% | 1.5% | 0.5% | 0.0% |
| reits | 5.6% | 1.5% | 0.1% | 4.3% | 5.9% | 0.0% | 2.5% | 8.3% | 0.9% | 0.0% | 0.5% | 0.0% | 1.1% | 0.9% | 0.0% |
| gold | 5.6% | 1.6% | 0.1% | 9.2% | 5.9% | 5.6% | 4.4% | 6.4% | 1.4% | 0.1% | 1.7% | 15.9% | 1.7% | 3.0% | 0.0% |
| commodities | 5.6% | 1.5% | 0.1% | 0.1% | 5.9% | 0.0% | 0.0% | 5.4% | 1.5% | 0.1% | 2.4% | 0.0% | 1.4% | 1.1% | 0.0% |
| cash | 5.6% | 45.9% | 84.6% | 2.8% | 0.0% | 0.0% | 0.0% | 0.4% | 62.2% | 91.9% | 82.6% | 0.0% | 53.2% | 12.6% | 0.0% |

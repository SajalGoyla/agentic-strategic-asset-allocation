# Portfolio Construction Proposals

As of 2026-10-01, regime **expansion**

| agent | category | return % | vol % | Sharpe | eff. N | TE % | IPS |
|---|---|---|---|---|---|---|---|
| equal_weight | heuristic | 6.71 | 8.41 | 0.37 | 18.0 | 4.36 | pass |
| inverse_volatility | heuristic | 6.55 | 8.03 | 0.36 | 14.8 | 4.56 | pass |
| inverse_variance | heuristic | 6.10 | 6.94 | 0.36 | 11.8 | 5.42 | FAIL |
| market_cap_weight | heuristic | 7.43 | 11.78 | 0.32 | 7.0 | 3.68 | pass |
| volatility_targeting | heuristic | 6.89 | 8.90 | 0.37 | 17.0 | 4.40 | pass |
| max_sharpe | return_optimized | 7.47 | 8.00 | 0.48 | 3.1 | 4.09 | pass |
| black_litterman | return_optimized | 6.95 | 8.00 | 0.42 | 5.7 | 3.28 | pass |
| resampled_efficient_frontier | return_optimized | 6.98 | 8.00 | 0.42 | 13.1 | 4.51 | pass |
| risk_parity | risk_structured | 6.43 | 7.56 | 0.37 | 14.3 | 5.07 | FAIL |
| hierarchical_risk_parity | risk_structured | 5.97 | 6.78 | 0.35 | 11.5 | 6.15 | FAIL |
| maximum_diversification | risk_structured | 6.47 | 7.87 | 0.36 | 6.4 | 6.88 | FAIL |
| cvar_minimization | non_traditional | 6.38 | 8.00 | 0.34 | 2.9 | 3.60 | pass |
| tail_risk_parity | non_traditional | 6.43 | 7.67 | 0.37 | 14.4 | 4.96 | FAIL |
| pc_researcher | pc_researcher | 5.26 | 2.74 | 0.60 | 5.3 | 7.27 | FAIL |
| adversarial_diversifier | non_traditional | 4.32 | 1.17 | 0.60 | 1.9 | 9.30 | FAIL |

## Weights

| asset | equal_weight | inverse_volatility | inverse_variance | market_cap_weight | volatility_targeting | max_sharpe | black_litterman | resampled_efficient_frontier | risk_parity | hierarchical_risk_parity | maximum_diversification | cvar_minimization | tail_risk_parity | pc_researcher | adversarial_diversifier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| us_large_cap | 5.6% | 5.2% | 3.7% | 48.8% | 5.9% | 0.0% | 22.0% | 0.4% | 4.4% | 2.2% | 0.0% | 45.4% | 4.4% | 0.3% | 0.0% |
| us_small_cap | 5.6% | 3.9% | 2.1% | 4.8% | 5.9% | 0.0% | 4.6% | 5.5% | 3.6% | 1.4% | 9.1% | 0.0% | 3.5% | 1.4% | 0.0% |
| us_value | 5.6% | 5.2% | 3.6% | 5.0% | 5.9% | 51.0% | 14.7% | 10.9% | 4.4% | 2.4% | 1.8% | 0.0% | 4.4% | 7.3% | 0.0% |
| us_growth | 5.6% | 4.5% | 2.8% | 7.5% | 5.9% | 0.0% | 0.5% | 6.2% | 4.1% | 1.7% | 9.8% | 0.0% | 4.1% | 1.0% | 0.0% |
| intl_developed | 5.6% | 4.8% | 3.1% | 4.8% | 5.9% | 0.0% | 0.0% | 3.8% | 3.8% | 2.4% | 0.0% | 0.0% | 4.0% | 0.5% | 0.0% |
| emerging_markets | 5.6% | 3.5% | 1.6% | 1.9% | 5.9% | 0.0% | 2.6% | 3.9% | 3.0% | 1.2% | 0.0% | 0.0% | 3.1% | 0.4% | 0.0% |
| short_treasuries | 5.6% | 0.0% | 0.0% | 1.6% | 5.9% | 25.0% | 0.0% | 15.3% | 0.0% | 0.0% | 0.0% | 1.4% | 0.0% | 53.4% | 62.4% |
| intermediate_treasuries | 5.6% | 11.9% | 19.2% | 2.5% | 5.9% | 0.0% | 36.3% | 5.5% | 16.5% | 19.2% | 17.9% | 37.3% | 14.2% | 7.0% | 0.0% |
| long_treasuries | 5.6% | 6.2% | 5.2% | 2.8% | 5.9% | 21.0% | 12.5% | 13.7% | 9.3% | 7.7% | 28.5% | 0.0% | 7.6% | 2.0% | 0.0% |
| ig_corporates | 5.6% | 10.7% | 15.7% | 1.9% | 5.9% | 0.0% | 0.0% | 4.6% | 8.8% | 15.7% | 0.0% | 0.0% | 10.6% | 3.3% | 0.0% |
| hy_corporates | 5.6% | 9.1% | 11.2% | 1.0% | 5.9% | 0.0% | 0.0% | 3.2% | 7.4% | 9.8% | 0.0% | 0.0% | 8.3% | 2.6% | 0.0% |
| intl_sovereigns | 5.6% | 9.1% | 11.2% | 0.1% | 5.9% | 0.0% | 0.0% | 0.0% | 7.6% | 11.7% | 0.0% | 0.0% | 8.9% | 0.1% | 0.0% |
| intl_corporates | 5.6% | 8.3% | 9.5% | 0.0% | 5.9% | 0.0% | 0.0% | 1.9% | 6.7% | 10.0% | 0.0% | 0.0% | 7.7% | 0.3% | 0.0% |
| usd_em_debt | 5.6% | 5.5% | 4.1% | 0.9% | 5.9% | 0.0% | 0.0% | 4.0% | 4.7% | 3.6% | 0.0% | 0.0% | 5.0% | 0.4% | 0.0% |
| reits | 5.6% | 4.0% | 2.2% | 4.3% | 5.9% | 0.0% | 3.9% | 9.5% | 3.6% | 3.3% | 2.8% | 0.0% | 3.7% | 0.8% | 0.0% |
| gold | 5.6% | 4.3% | 2.5% | 9.2% | 5.9% | 3.0% | 2.7% | 5.8% | 6.0% | 4.1% | 12.9% | 15.9% | 5.7% | 1.5% | 0.0% |
| commodities | 5.6% | 4.0% | 2.2% | 0.1% | 5.9% | 0.0% | 0.0% | 5.9% | 6.0% | 3.6% | 17.3% | 0.0% | 4.7% | 1.3% | 0.0% |
| cash | 5.6% | 0.0% | 0.0% | 2.8% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 16.3% | 37.6% |

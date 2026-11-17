# Scenarios

Exhibit 3 step 8: "Scenario analysis (bull/bear from method range)". The bounds are the
extreme available candidates, the base is the judge's estimate. The spread is the
methodological disagreement the judge resolved, not a stress test.

| Asset | Bear | Base | Bull | Spread | Bear method | Bull method | Candidates |
|---|---:|---:|---:|---:|---|---|---:|
| us_large_cap | 3.57% | 7.47% | 12.83% | 9.27pp | `inverse_gordon` | `regime_adjusted` | 7 |
| us_growth | 7.12% | 8.28% | 13.69% | 6.57pp | `implied_erp_cape` | `regime_adjusted` | 6 |
| us_small_cap | 6.65% | 9.34% | 12.38% | 5.73pp | `inverse_gordon` | `historical_erp` | 6 |
| reits | 7.42% | 9.09% | 11.94% | 4.53pp | `implied_erp_cape` | `historical_erp` | 6 |
| emerging_markets | 7.57% | 9.44% | 11.76% | 4.19pp | `regime_adjusted` | `implied_erp_cape` | 6 |
| long_treasuries | 4.19% | 5.98% | 8.23% | 4.05pp | `bl_equilibrium` | `regime_adjusted` | 5 |
| us_value | 8.00% | 9.51% | 11.99% | 3.99pp | `bl_equilibrium` | `historical_erp` | 6 |
| usd_em_debt | 6.45% | 6.96% | 10.33% | 3.88pp | `yield_building_block` | `historical_erp` | 5 |
| gold | 5.39% | 6.01% | 8.90% | 3.51pp | `bl_equilibrium` | `historical_erp` | 4 |
| intermediate_treasuries | 4.13% | 5.26% | 6.54% | 2.42pp | `bl_equilibrium` | `regime_adjusted` | 6 |
| commodities | 4.56% | 5.61% | 6.54% | 1.98pp | `regime_adjusted` | `historical_erp` | 4 |
| hy_corporates | 5.79% | 6.04% | 7.76% | 1.97pp | `bl_equilibrium` | `historical_erp` | 5 |
| intl_sovereigns | 3.55% | 4.13% | 5.32% | 1.77pp | `regime_adjusted` | `historical_erp` | 5 |
| ig_corporates | 5.01% | 5.94% | 6.71% | 1.70pp | `bl_equilibrium` | `historical_erp` | 5 |
| intl_corporates | 4.44% | 5.16% | 6.14% | 1.70pp | `regime_adjusted` | `historical_erp` | 5 |
| intl_developed | 7.67% | 8.18% | 8.94% | 1.28pp | `regime_adjusted` | `implied_erp_cape` | 6 |
| cash | 3.00% | 3.62% | 4.03% | 1.03pp | `survey_consensus` | `bl_equilibrium` | 6 |
| short_treasuries | 4.03% | 4.74% | 4.88% | 0.85pp | `bl_equilibrium` | `historical_erp` | 5 |

Widest: **us_large_cap** at 9.27pp. Narrowest: **short_treasuries** at 0.85pp. A point estimate carries very different weight across that difference.

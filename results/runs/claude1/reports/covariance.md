# Covariance as of 2026-10-01

Chosen estimator: **ledoit_wolf**, 400 months (1993-06-30 to 2026-09-30), shrinkage 0.05.

| Estimator | Months | Avg correlation | Condition number | Positive definite |
|---|---|---|---|---|
| sample | 400 | 0.33 | 10,029 | yes |
| ledoit_wolf | 400 | 0.33 | 7,969 | yes |
| exponential | 400 | 0.43 | 11,206 | yes |

## Annualised volatility by estimator (%)

| Asset | sample | ledoit_wolf | exponential |
|---|---|---|---|
| us_large_cap | 14.8 | 14.8 | 14.9 |
| us_small_cap | 19.5 | 19.5 | 20.2 |
| us_value | 14.9 | 14.8 | 15.0 |
| us_growth | 16.9 | 16.9 | 17.4 |
| intl_developed | 16.0 | 16.0 | 15.3 |
| emerging_markets | 22.2 | 22.1 | 18.7 |
| short_treasuries | 1.7 | 1.7 | 1.6 |
| intermediate_treasuries | 6.5 | 6.5 | 6.7 |
| long_treasuries | 12.4 | 12.4 | 13.6 |
| ig_corporates | 7.1 | 7.1 | 8.1 |
| hy_corporates | 8.5 | 8.4 | 7.8 |
| intl_sovereigns | 8.5 | 8.5 | 9.0 |
| intl_corporates | 9.2 | 9.2 | 10.1 |
| usd_em_debt | 14.0 | 14.0 | 10.3 |
| reits | 19.0 | 19.0 | 18.6 |
| gold | 17.9 | 17.9 | 17.3 |
| commodities | 19.1 | 19.1 | 18.2 |
| cash | 0.6 | 0.6 | 0.6 |

Ledoit-Wolf shrinks correlations toward their average while keeping each asset's own variance; exponential weighting reacts faster to a change in volatility regime; regime-conditional pools only the months the macro agent labelled with the current regime. See `src/saa/skills/covariance/SKILL.md`.

# Covariance as of 2026-10-01

Chosen estimator: **ledoit_wolf**, 400 months (1993-06-30 to 2026-09-30), shrinkage 0.05.

| Estimator | Months | Avg correlation | Condition number | Positive definite |
|---|---|---|---|---|
| sample | 400 | 0.33 | 10,029 | yes |
| ledoit_wolf | 400 | 0.33 | 7,969 | yes |
| exponential | 400 | 0.43 | 11,206 | yes |
| regime_conditional | 178 | 0.27 | 5,997 | yes |

## Annualised volatility by estimator (%)

| Asset | sample | ledoit_wolf | exponential | regime_conditional |
|---|---|---|---|---|
| us_large_cap | 14.8 | 14.8 | 14.9 | 12.4 |
| us_small_cap | 19.5 | 19.5 | 20.2 | 16.6 |
| us_value | 14.9 | 14.8 | 15.0 | 12.8 |
| us_growth | 16.9 | 16.9 | 17.4 | 13.5 |
| intl_developed | 16.0 | 16.0 | 15.3 | 13.9 |
| emerging_markets | 22.2 | 22.1 | 18.7 | 21.4 |
| short_treasuries | 1.7 | 1.7 | 1.6 | 1.3 |
| intermediate_treasuries | 6.5 | 6.5 | 6.7 | 5.6 |
| long_treasuries | 12.4 | 12.4 | 13.6 | 10.9 |
| ig_corporates | 7.1 | 7.1 | 8.1 | 5.1 |
| hy_corporates | 8.5 | 8.4 | 7.8 | 5.5 |
| intl_sovereigns | 8.5 | 8.5 | 9.0 | 6.9 |
| intl_corporates | 9.2 | 9.2 | 10.1 | 7.6 |
| usd_em_debt | 14.0 | 14.0 | 10.3 | 15.3 |
| reits | 19.0 | 19.0 | 18.6 | 15.1 |
| gold | 17.9 | 17.9 | 17.3 | 19.0 |
| commodities | 19.1 | 19.1 | 18.2 | 17.4 |
| cash | 0.6 | 0.6 | 0.6 | 0.6 |

Ledoit-Wolf shrinks correlations toward their average while keeping each asset's own variance; exponential weighting reacts faster to a change in volatility regime; regime-conditional pools only the months the macro agent labelled with the current regime. See `src/saa/skills/covariance/SKILL.md`.

## Out-of-sample record (decision 63)

Fitted at each year-end on data to that date only. *Realised / forecast* is the median ratio for the IPS benchmark's volatility over the next 12 months (1.0 is unbiased; below 1 the estimator forecast too much risk). *Error* is the mean |log(realised / forecast)| over the benchmark and equal weight. *Stock-bond error* is the mean absolute error of the US large cap / intermediate Treasuries correlation over the next 36 months.

| Estimator | Years | Realised / forecast | Error | Stock-bond error |
|---|---|---|---|---|
| ledoit_wolf | 26 | 0.83 | 0.380 | 0.36 |
| exponential | 26 | 0.83 | 0.385 | 0.30 |
| regime_conditional | 22 | 0.91 | 0.369 | 0.43 |

## Choice

**ledoit_wolf**. The out-of-sample record does not pick a winner. Errors are 0.380 for Ledoit-Wolf, 0.385 for exponential and 0.369 for regime-conditional, a spread of about 0.016 and well inside a few hundredths, so stability is the tie-breaker. Realised/forecast is 0.83 for both Ledoit-Wolf and exponential and 0.91 for regime-conditional. All three forecast too much benchmark risk, and regime-conditional is only modestly closer to unbiased. The regime call is expansion at confidence 0.35, which is low, so there is little reason to condition on it. The conditional estimator also rests on only 178 of 400 months and uses a regime label that is itself uncertain. It gives the lowest benchmark volatility (7.81% vs 9.37%) and implies much lower bond and credit risk (IG corporates 5.1% vs 7.1%). Trusting that on a 0.35-confidence label would risk understating risk in a fragile, late-cycle-adjacent expansion with sticky inflation. The case for exponential is that its stock-bond correlation is +0.15 against -0.04 for the others, which hints at a recent correlation shift. Its stock-bond error is lowest (0.30 vs 0.36), but its overall error is no better, its condition number is the worst (11,206) and it is noisier. One disagreement is not enough to override the stable default. Ledoit-Wolf has the best-conditioned matrix after the conditional one (7,969), shrinkage of 0.05 and the longest history. Downstream, its benchmark volatility of 9.37% sits between the other two. That leaves risk-based portfolios with a moderate bond tilt and an 8% floor that is neither unusually easy nor unusually hard to reach. I chose it on stability and evidence, not to make the IPS easier to meet. The IPS is ratified.

*What would change it:* Regime-conditional would become the better choice if the macro regime call became high-confidence and clearly different from the long-run average, and the expansion sample stayed large enough, with an out-of-sample record that clearly beat the others, not just by 0.016. Exponential would become the better choice if the stock-bond correlation disagreement persisted or widened, for example if the exponential estimate stayed positive while Ledoit-Wolf remained near zero and realised stock-bond correlation confirmed the shift. Its overall error would also need to come in at or below Ledoit-Wolf's. A sharp rise in realised benchmark volatility relative to the Ledoit-Wolf forecast, reversing the consistent over-forecast of 0.83, would also favour a faster-reacting estimator.

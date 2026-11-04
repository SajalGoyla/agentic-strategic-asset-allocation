# CIO ensembles

Every ensemble of the candidate portfolios, profiled as a candidate is (§3.6). Only IPS-compliant ensembles may be recommended; a projected one breached a limit and was moved to the nearest compliant allocation. The score is the candidates' six-dimension composite (§4.4).

| ensemble | IPS | vol % | TE % | DD % | backtest Sharpe | return % | eff. N | candidates held | largest share | projection moved | score | chosen | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| simple_average | pass | 8.00 | 4.22 | -23.4 | 0.60 | 6.74 | 10.6 | 15 | volatility_targeting 7% | 28.5% | 0.715 |  | projected into the IPS; it breached objectives.volatility |
| inverse_tracking_error | pass | 8.00 | 4.23 | -23.4 | 0.60 | 6.76 | 11.4 | 15 | pc_researcher 13% | 28.2% | 0.723 |  | projected into the IPS; it breached objectives.volatility |
| backtest_sharpe_weighted | pass | 8.00 | 4.06 | -23.3 | 0.61 | 6.76 | 11.0 | 15 | cvar_minimization 8% | 26.4% | 0.726 |  | projected into the IPS; it breached objectives.volatility |
| meta_optimization | pass | 8.00 | 2.78 | -23.1 | 0.69 | 7.13 | 7.7 | 3 | black_litterman 82% | - | 0.795 |  | - |
| regime_conditional | pass | 8.00 | 3.80 | -23.3 | 0.63 | 6.81 | 12.3 | 14 | black_litterman 9% | 20.6% | 0.751 |  | projected into the IPS; it breached objectives.volatility |
| composite_score | pass | 8.00 | 3.64 | -23.2 | 0.64 | 6.94 | 14.5 | 14 | resampled_efficient_frontier 18% | 13.5% | 0.787 | yes | projected into the IPS; it breached objectives.volatility |
| trimmed_mean | pass | 8.00 | 4.33 | -23.4 | 0.59 | 6.73 | 10.3 | 13 | volatility_targeting 8% | 29.5% | 0.707 |  | projected into the IPS; it breached objectives.volatility |
| single_method | pass | 8.00 | 4.33 | -24.3 | 0.63 | 7.11 | 13.3 | 1 | resampled_efficient_frontier 100% | - | 0.802 |  | - |

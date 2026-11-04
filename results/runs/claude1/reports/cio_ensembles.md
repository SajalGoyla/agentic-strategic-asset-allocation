# CIO ensembles

Every ensemble of the candidate portfolios, profiled as a candidate is (§3.6). Only IPS-compliant ensembles may be recommended; a projected one breached a limit and was moved to the nearest compliant allocation. The score is the candidates' six-dimension composite (§4.4).

| ensemble | IPS | vol % | TE % | DD % | backtest Sharpe | return % | eff. N | candidates held | largest share | projection moved | score | chosen | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| simple_average | pass | 8.00 | 4.15 | -23.3 | 0.61 | 6.77 | 10.8 | 15 | volatility_targeting 7% | 28.3% | 0.721 |  | projected into the IPS; it breached objectives.volatility |
| inverse_tracking_error | pass | 8.00 | 4.12 | -23.3 | 0.61 | 6.80 | 11.4 | 15 | inverse_volatility 11% | 28.0% | 0.727 |  | projected into the IPS; it breached objectives.volatility |
| backtest_sharpe_weighted | pass | 8.00 | 3.98 | -23.3 | 0.62 | 6.80 | 11.3 | 15 | cvar_minimization 8% | 26.0% | 0.733 |  | projected into the IPS; it breached objectives.volatility |
| meta_optimization | pass | 8.00 | 3.34 | -23.1 | 0.67 | 7.26 | 9.9 | 3 | pc_researcher 39% | - | 0.798 | yes | - |
| regime_conditional | pass | 8.00 | 3.73 | -23.3 | 0.63 | 6.84 | 12.5 | 14 | black_litterman 9% | 20.0% | 0.757 |  | projected into the IPS; it breached objectives.volatility |
| composite_score | pass | 8.00 | 3.58 | -23.2 | 0.64 | 6.95 | 14.1 | 14 | resampled_efficient_frontier 16% | 14.4% | 0.785 |  | projected into the IPS; it breached objectives.volatility |
| trimmed_mean | pass | 8.00 | 4.25 | -23.3 | 0.60 | 6.77 | 10.6 | 13 | volatility_targeting 8% | 29.1% | 0.714 |  | projected into the IPS; it breached objectives.volatility |
| single_method | pass | 8.00 | 4.33 | -24.3 | 0.63 | 7.11 | 13.3 | 1 | resampled_efficient_frontier 100% | - | 0.802 |  | - |

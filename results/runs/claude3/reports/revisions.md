# Revisions of the shortlist

As of 2026-10-01. Shortlist: resampled_efficient_frontier, inverse_volatility, cvar_minimization, black_litterman, risk_parity.

| agent | levers | turnover | vol % before → after | Sharpe before → after | eff. N before → after | IPS after |
|---|---|---|---|---|---|---|
| resampled_efficient_frontier | no change | 0.0% | 8.00 → 8.00 | 0.42 → 0.42 | 13.1 → 13.1 | pass |
| inverse_volatility | no change | 0.0% | 8.03 → 8.03 | 0.36 → 0.36 | 14.8 → 14.8 | pass |
| cvar_minimization | no change | 0.0% | 8.00 → 8.00 | 0.34 → 0.34 | 2.9 → 2.9 | pass |
| black_litterman | no change | 0.0% | 8.00 → 8.00 | 0.42 → 0.42 | 5.7 → 5.7 | pass |
| risk_parity | capped every weight at 12%; shrunk 30% of the way toward equal weight | 7.8% | 7.56 → 7.84 | 0.37 → 0.37 | 14.3 → 16.4 | FAIL |

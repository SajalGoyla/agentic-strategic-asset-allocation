# Revisions of the shortlist

As of 2026-10-01. Shortlist: resampled_efficient_frontier, black_litterman, pc_researcher, cvar_minimization, equal_weight.

| agent | levers | turnover | vol % before → after | Sharpe before → after | eff. N before → after | IPS after |
|---|---|---|---|---|---|---|
| resampled_efficient_frontier | no change | 0.0% | 8.00 → 8.00 | 0.41 → 0.41 | 13.3 → 13.3 | pass |
| black_litterman | no change | 0.0% | 8.00 → 8.00 | 0.41 → 0.41 | 6.1 → 6.1 | pass |
| pc_researcher | excluded cash, short_treasuries; capped every weight at 20%; shrunk 20% of the way toward equal weight | 55.4% | 3.82 → 8.22 | 0.51 → 0.42 | 7.2 → 11.5 | pass |
| cvar_minimization | shrunk 25% of the way toward equal weight | 20.5% | 8.00 → 7.95 | 0.33 → 0.34 | 2.9 → 6.8 | FAIL |
| equal_weight | no change | 0.0% | 8.41 → 8.41 | 0.36 → 0.36 | 18.0 → 18.0 | pass |

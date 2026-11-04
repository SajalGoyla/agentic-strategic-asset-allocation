# Revisions of the shortlist

As of 2026-10-01. Shortlist: resampled_efficient_frontier, black_litterman, pc_researcher, cvar_minimization, equal_weight.

| agent | levers | turnover | vol % before → after | Sharpe before → after | eff. N before → after | IPS after |
|---|---|---|---|---|---|---|
| resampled_efficient_frontier | no change | 0.0% | 8.00 → 8.00 | 0.41 → 0.41 | 13.3 → 13.3 | pass |
| black_litterman | capped every weight at 30% | 7.4% | 8.00 → 8.66 | 0.41 → 0.40 | 6.1 → 6.7 | pass |
| pc_researcher | capped every weight at 15%; shrunk 50% of the way toward equal weight | 32.9% | 3.82 → 6.71 | 0.51 → 0.40 | 7.2 → 15.8 | FAIL |
| cvar_minimization | excluded short_treasuries; shrunk 25% of the way toward equal weight | 20.6% | 8.00 → 8.14 | 0.33 → 0.34 | 2.9 → 6.5 | pass |
| equal_weight | no change | 0.0% | 8.41 → 8.41 | 0.36 → 0.36 | 18.0 → 18.0 | pass |

# Peer Reviews

As of 2026-10-01. 30 reviews, seed **386410625** (14 intra-category, 16 inter-category).

| reviewed | reviews | mean score | reviewers (score) | technical errors |
|---|---|---|---|---|
| adversarial_diversifier | 2 | 0.38 | cvar_minimization (0.40, intra), equal_weight (0.35, inter) | 0 |
| black_litterman | 2 | 0.60 | max_sharpe (0.58, intra), resampled_efficient_frontier (0.62, intra) | 4 |
| cvar_minimization | 2 | 0.61 | adversarial_diversifier (0.60, intra), tail_risk_parity (0.62, intra) | 0 |
| equal_weight | 2 | 0.58 | inverse_variance (0.62, intra), resampled_efficient_frontier (0.55, inter) | 2 |
| hierarchical_risk_parity | 2 | 0.30 | cvar_minimization (0.30, inter), inverse_volatility (0.30, inter) | 1 |
| inverse_variance | 2 | 0.35 | inverse_volatility (0.40, intra), risk_parity (0.30, inter) | 3 |
| inverse_volatility | 2 | 0.46 | market_cap_weight (0.50, intra), pc_researcher (0.42, inter) | 4 |
| market_cap_weight | 2 | 0.46 | volatility_targeting (0.50, intra), hierarchical_risk_parity (0.42, inter) | 4 |
| max_sharpe | 2 | 0.53 | black_litterman (0.55, intra), pc_researcher (0.50, inter) | 2 |
| maximum_diversification | 2 | 0.30 | risk_parity (0.30, intra), hierarchical_risk_parity (0.30, intra) | 4 |
| pc_researcher | 2 | 0.42 | max_sharpe (0.42, inter), inverse_variance (0.42, inter) | 4 |
| resampled_efficient_frontier | 2 | 0.57 | volatility_targeting (0.55, inter), market_cap_weight (0.60, inter) | 0 |
| risk_parity | 2 | 0.40 | maximum_diversification (0.45, intra), adversarial_diversifier (0.35, inter) | 3 |
| tail_risk_parity | 2 | 0.45 | black_litterman (0.45, inter), maximum_diversification (0.45, inter) | 1 |
| volatility_targeting | 2 | 0.43 | equal_weight (0.45, intra), tail_risk_parity (0.40, inter) | 5 |

## Substitutions

- **pc_researcher**: pc_researcher has no other member in this run, so the intra-category review is substituted with a second inter-category review

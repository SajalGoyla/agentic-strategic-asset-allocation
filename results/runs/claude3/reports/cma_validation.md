# CMA validation as of 2026-10-01

Overall: **pass**. Estimates checked: judged CMAs. Ranges: `config/cma_validation.yaml`.

| asset | estimate % | source | vol % | candidate range | status | warnings |
|---|---|---|---|---|---|---|
| us_large_cap | 7.47 | judge | 14.8 | 3.6-12.8 | pass | - |
| us_small_cap | 9.34 | judge | 19.5 | 6.7-12.4 | pass | - |
| us_value | 9.51 | judge | 14.8 | 8.0-12.0 | pass | - |
| us_growth | 8.28 | judge | 16.9 | 7.1-13.7 | pass | - |
| intl_developed | 8.18 | judge | 16.0 | 7.7-8.9 | pass | - |
| emerging_markets | 9.44 | judge | 22.1 | 7.6-11.8 | pass | - |
| short_treasuries | 4.74 | judge | 1.7 | 4.0-4.9 | pass | - |
| intermediate_treasuries | 5.26 | judge | 6.5 | 4.1-6.5 | pass | - |
| long_treasuries | 5.98 | judge | 12.4 | 4.2-8.2 | pass | - |
| ig_corporates | 5.94 | judge | 7.1 | 5.0-6.7 | pass | - |
| hy_corporates | 6.04 | judge | 8.4 | 5.8-7.8 | pass | - |
| intl_sovereigns | 4.13 | judge | 8.5 | 3.5-5.3 | pass | - |
| intl_corporates | 5.16 | judge | 9.2 | 4.4-6.1 | pass | - |
| usd_em_debt | 6.96 | judge | 14.0 | 6.4-10.3 | pass | - |
| reits | 9.09 | judge | 19.0 | 7.4-11.9 | pass | - |
| gold | 6.01 | judge | 17.9 | 5.4-8.9 | pass | - |
| commodities | 5.61 | judge | 19.1 | 4.6-6.5 | pass | - |
| cash | 3.62 | judge | 0.6 | 3.0-4.0 | pass | - |

## Cross-section

- **return rises with risk** (pass): rank correlation 0.74 across 18 assets (minimum 0.3)
- **risky assets beat cash** (pass): every risky asset is above cash

## Every check

- **us_large_cap**: plausible range pass (7.47% vs [2, 15] for equity); implied Sharpe pass (0.23 at 14.8% volatility, T-bill 4.03%); paper Exhibit 8 pass (+0.67pp from the paper's judge value 6.8% (March 2026))
- **us_small_cap**: plausible range pass (9.34% vs [2, 15] for equity); implied Sharpe pass (0.27 at 19.5% volatility, T-bill 4.03%); paper Exhibit 8 pass (+1.14pp from the paper's judge value 8.2% (March 2026))
- **us_value**: plausible range pass (9.51% vs [2, 15] for equity); implied Sharpe pass (0.37 at 14.8% volatility, T-bill 4.03%); paper Exhibit 8 pass (+2.01pp from the paper's judge value 7.5% (March 2026))
- **us_growth**: plausible range pass (8.28% vs [2, 15] for equity); implied Sharpe pass (0.25 at 16.9% volatility, T-bill 4.03%); paper Exhibit 8 pass (+2.08pp from the paper's judge value 6.2% (March 2026))
- **intl_developed**: plausible range pass (8.18% vs [2, 15] for equity); implied Sharpe pass (0.26 at 16.0% volatility, T-bill 4.03%); paper Exhibit 8 pass (+1.48pp from the paper's judge value 6.7% (March 2026))
- **emerging_markets**: plausible range pass (9.44% vs [2, 15] for equity); implied Sharpe pass (0.24 at 22.1% volatility, T-bill 4.03%); paper Exhibit 8 pass (+1.24pp from the paper's judge value 8.2% (March 2026))
- **short_treasuries**: plausible range pass (4.74% vs [0, 12] for fixed_income); yield anchor pass (-0.08pp from the yield building block (4.82%)); implied Sharpe pass (0.42 at 1.7% volatility, T-bill 4.03%)
- **intermediate_treasuries**: plausible range pass (5.26% vs [0, 12] for fixed_income); yield anchor pass (-0.19pp from the yield building block (5.45%)); implied Sharpe pass (0.19 at 6.5% volatility, T-bill 4.03%)
- **long_treasuries**: plausible range pass (5.98% vs [0, 12] for fixed_income); yield anchor pass (-0.45pp from the yield building block (6.43%)); implied Sharpe pass (0.16 at 12.4% volatility, T-bill 4.03%)
- **ig_corporates**: plausible range pass (5.94% vs [0, 12] for fixed_income); yield anchor pass (-0.23pp from the yield building block (6.17%)); implied Sharpe pass (0.27 at 7.1% volatility, T-bill 4.03%)
- **hy_corporates**: plausible range pass (6.04% vs [0, 12] for fixed_income); yield anchor pass (+0.02pp from the yield building block (6.02%)); implied Sharpe pass (0.24 at 8.4% volatility, T-bill 4.03%)
- **intl_sovereigns**: plausible range pass (4.13% vs [0, 12] for fixed_income); yield anchor pass (+0.13pp from the yield building block (4.00%)); implied Sharpe pass (0.01 at 8.5% volatility, T-bill 4.03%)
- **intl_corporates**: plausible range pass (5.16% vs [0, 12] for fixed_income); yield anchor pass (-0.00pp from the yield building block (5.16%)); implied Sharpe pass (0.12 at 9.2% volatility, T-bill 4.03%)
- **usd_em_debt**: plausible range pass (6.96% vs [0, 12] for fixed_income); yield anchor pass (+0.51pp from the yield building block (6.45%)); implied Sharpe pass (0.21 at 14.0% volatility, T-bill 4.03%)
- **reits**: plausible range pass (9.09% vs [0, 15] for real_assets); implied Sharpe pass (0.27 at 19.0% volatility, T-bill 4.03%); paper Exhibit 8 pass (+0.79pp from the paper's judge value 8.3% (March 2026))
- **gold**: plausible range pass (6.01% vs [0, 15] for real_assets); implied Sharpe pass (0.11 at 17.9% volatility, T-bill 4.03%)
- **commodities**: plausible range pass (5.61% vs [0, 15] for real_assets); implied Sharpe pass (0.08 at 19.1% volatility, T-bill 4.03%)
- **cash**: plausible range pass (3.62% vs [0, 8] for cash); yield anchor pass (-0.41pp from the yield building block (4.03%))

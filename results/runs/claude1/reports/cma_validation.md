# CMA validation as of 2026-10-01

Overall: **WARN**. Estimates checked: judged CMAs. Ranges: `config/cma_validation.yaml`.

| asset | estimate % | source | vol % | candidate range | status | warnings |
|---|---|---|---|---|---|---|
| us_large_cap | 7.52 | judge | 14.8 | 3.6-13.5 | pass | - |
| us_small_cap | 9.57 | judge | 19.5 | 6.7-12.4 | pass | - |
| us_value | 9.58 | judge | 14.8 | 8.0-12.5 | pass | - |
| us_growth | 9.27 | judge | 16.9 | 7.1-14.4 | WARN | paper Exhibit 8: +3.07pp from the paper's judge value 6.2% (March 2026) |
| intl_developed | 8.22 | judge | 16.0 | 7.8-8.9 | pass | - |
| emerging_markets | 9.73 | judge | 22.1 | 8.0-11.8 | pass | - |
| short_treasuries | 4.70 | judge | 1.7 | 4.0-4.9 | pass | - |
| intermediate_treasuries | 5.26 | judge | 6.5 | 4.1-6.6 | pass | - |
| long_treasuries | 6.09 | judge | 12.4 | 4.2-8.2 | pass | - |
| ig_corporates | 5.94 | judge | 7.1 | 5.0-6.7 | pass | - |
| hy_corporates | 6.16 | judge | 8.4 | 5.8-7.8 | pass | - |
| intl_sovereigns | 4.27 | judge | 8.5 | 4.0-5.3 | pass | - |
| intl_corporates | 5.21 | judge | 9.2 | 5.0-6.1 | pass | - |
| usd_em_debt | 7.02 | judge | 14.0 | 6.4-10.3 | pass | - |
| reits | 8.88 | judge | 19.0 | 7.4-11.9 | pass | - |
| gold | 6.40 | judge | 17.9 | 5.4-8.9 | pass | - |
| commodities | 5.50 | judge | 19.1 | 4.2-6.5 | pass | - |
| cash | 3.82 | judge | 0.6 | 3.0-4.0 | pass | - |

## Cross-section

- **return rises with risk** (pass): rank correlation 0.77 across 18 assets (minimum 0.3)
- **risky assets beat cash** (pass): every risky asset is above cash

## Every check

- **us_large_cap**: plausible range pass (7.52% vs [2, 15] for equity); implied Sharpe pass (0.24 at 14.8% volatility, T-bill 4.03%); paper Exhibit 8 pass (+0.72pp from the paper's judge value 6.8% (March 2026))
- **us_small_cap**: plausible range pass (9.57% vs [2, 15] for equity); implied Sharpe pass (0.28 at 19.5% volatility, T-bill 4.03%); paper Exhibit 8 pass (+1.37pp from the paper's judge value 8.2% (March 2026))
- **us_value**: plausible range pass (9.58% vs [2, 15] for equity); implied Sharpe pass (0.37 at 14.8% volatility, T-bill 4.03%); paper Exhibit 8 pass (+2.08pp from the paper's judge value 7.5% (March 2026))
- **us_growth**: plausible range pass (9.27% vs [2, 15] for equity); implied Sharpe pass (0.31 at 16.9% volatility, T-bill 4.03%); paper Exhibit 8 WARN (+3.07pp from the paper's judge value 6.2% (March 2026))
- **intl_developed**: plausible range pass (8.22% vs [2, 15] for equity); implied Sharpe pass (0.26 at 16.0% volatility, T-bill 4.03%); paper Exhibit 8 pass (+1.52pp from the paper's judge value 6.7% (March 2026))
- **emerging_markets**: plausible range pass (9.73% vs [2, 15] for equity); implied Sharpe pass (0.26 at 22.1% volatility, T-bill 4.03%); paper Exhibit 8 pass (+1.53pp from the paper's judge value 8.2% (March 2026))
- **short_treasuries**: plausible range pass (4.70% vs [0, 12] for fixed_income); yield anchor pass (-0.12pp from the yield building block (4.82%)); implied Sharpe pass (0.40 at 1.7% volatility, T-bill 4.03%)
- **intermediate_treasuries**: plausible range pass (5.26% vs [0, 12] for fixed_income); yield anchor pass (-0.19pp from the yield building block (5.45%)); implied Sharpe pass (0.19 at 6.5% volatility, T-bill 4.03%)
- **long_treasuries**: plausible range pass (6.09% vs [0, 12] for fixed_income); yield anchor pass (-0.34pp from the yield building block (6.43%)); implied Sharpe pass (0.17 at 12.4% volatility, T-bill 4.03%)
- **ig_corporates**: plausible range pass (5.94% vs [0, 12] for fixed_income); yield anchor pass (-0.23pp from the yield building block (6.17%)); implied Sharpe pass (0.27 at 7.1% volatility, T-bill 4.03%)
- **hy_corporates**: plausible range pass (6.16% vs [0, 12] for fixed_income); yield anchor pass (+0.14pp from the yield building block (6.02%)); implied Sharpe pass (0.25 at 8.4% volatility, T-bill 4.03%)
- **intl_sovereigns**: plausible range pass (4.27% vs [0, 12] for fixed_income); yield anchor pass (+0.27pp from the yield building block (4.00%)); implied Sharpe pass (0.03 at 8.5% volatility, T-bill 4.03%)
- **intl_corporates**: plausible range pass (5.21% vs [0, 12] for fixed_income); yield anchor pass (+0.05pp from the yield building block (5.16%)); implied Sharpe pass (0.13 at 9.2% volatility, T-bill 4.03%)
- **usd_em_debt**: plausible range pass (7.02% vs [0, 12] for fixed_income); yield anchor pass (+0.57pp from the yield building block (6.45%)); implied Sharpe pass (0.21 at 14.0% volatility, T-bill 4.03%)
- **reits**: plausible range pass (8.88% vs [0, 15] for real_assets); implied Sharpe pass (0.26 at 19.0% volatility, T-bill 4.03%); paper Exhibit 8 pass (+0.58pp from the paper's judge value 8.3% (March 2026))
- **gold**: plausible range pass (6.40% vs [0, 15] for real_assets); implied Sharpe pass (0.13 at 17.9% volatility, T-bill 4.03%)
- **commodities**: plausible range pass (5.50% vs [0, 15] for real_assets); implied Sharpe pass (0.08 at 19.1% volatility, T-bill 4.03%)
- **cash**: plausible range pass (3.82% vs [0, 8] for cash); yield anchor pass (-0.21pp from the yield building block (4.03%))

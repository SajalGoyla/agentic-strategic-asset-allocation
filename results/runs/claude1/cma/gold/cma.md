# CMA — gold

**Expected return:** 6.40% (3y, nominal, arithmetic)  
**Volatility:** 17.88%  
**Confidence:** low  
**Selection:** custom_blend — bl_equilibrium 35%, historical_erp 25%, regime_adjusted 40%  
**Candidate range:** 5.39% to 8.90% (moderate); -0.44pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 8.90 | 0.50 | risk_free_pct +4.03, excess_return_pct +4.87, months +441.00 | +4.87% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 5.71 | 0.40 | risk_free_pct +4.03, regime_excess_return_pct +0.41, unconditional_excess_return_pct +5.51, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged +0.41% a year (all months +5.51%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.39 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +1.36, market_weight_pct +9.19, risk_aversion +2.50 | Equilibrium excess return +1.36% at a 9.2% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to real_assets |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to real_assets |
| `survey_consensus` | – | – | – | unavailable: not applicable to real_assets |
| `yield_building_block` | – | – | – | unavailable: not applicable to real_assets |
| `auto_blend` | 6.84 | 0.44 | weight:historical_erp +0.38, weight:regime_adjusted +0.31, weight:bl_equilibrium +0.31 | Confidence-weighted average of 3 methods: historical_erp 38%, regime_adjusted 31%, bl_equilibrium 31%. |

## Judgment

**Regime logic.** Stage 1 reads a stall-speed expansion with sticky inflation and restrictive real rates, on the late-cycle border, at only 0.36 confidence. For gold the most relevant inputs are restrictive real rates and sticky inflation. High real rates raise the opportunity cost of holding a zero-yield asset, while persistent inflation and a 20-30% recession probability keep some hedging demand alive. On balance that is a mild headwind rather than a tailwind. Exhibit 4 says late-cycle environments tilt toward regime-adjusted methods. The regime-adjusted candidate draws on 180 expansion months and shows gold earning almost no excess return (+0.41%) over the following three years, which is consistent with gold's role as a defensive asset that does not need to pay off in expansions. Because regime confidence is low, I do not let this method dominate: it gets 40%, the largest single share, not a majority.

**Valuation context.** Gold has no cash flow, so the Gordon and CAPE methods do not apply and there is no yield anchor; valuation has to be judged from price history. The 3-year trailing return of about 30% a year is far above gold's long-run record (6.2% since 1990, 4.7% over the full sample). The historical_erp candidate's 4.87% excess return is inflated by the 2000s bull market and this recent surge, both of which sit inside its 1990-2026 window. That makes it a backward-looking extrapolation at a point where price looks stretched against its own history. The BL equilibrium (+1.36% excess) is a CAPM view and has a known bias. GLD's large ETF footprint inflates gold's market weight to 9.2%, which pushes its equilibrium premium up, while gold's low equity beta pulls it down. Even so, it is a disciplined anchor that ignores the recent run. A stretched price favours de-emphasising the historical premium; that call rests on price behaviour, since no valuation model exists for this asset.

**Signal alignment.** The composite signal is close to neutral (-0.06), but the components disagree in a way that matters. Mean reversion (-0.68) and trend (-0.57) both point down: the 36-month run is stretched, and price has fallen below its 10-month average after a drawdown of about 24% within the last year. Medium-term momentum (+0.21) and cross-asset relative momentum (+0.44) are still positive, which suggests the strong run has cooled but not collapsed. Every macro alignment signal is near zero, so gold's return has had little systematic link to the macro dimensions. Overall the signals support trimming the higher historical estimate and do not justify going to the bottom of the range. That is consistent with a blend somewhat below the 6.84% auto-blend.

**Rationale.** I set gold at 6.40% (arithmetic, nominal, 3-year horizon) as a custom blend: 25% historical_erp, 40% regime_adjusted and 35% bl_equilibrium. The auto-blend weights by each method's stated confidence, which gives the most weight (38%) to the historical premium. That premium is the input most distorted by gold's exceptional 2000s and 2023-26 rallies, and it is the one the mean-reversion and trend signals argue against. I move weight toward the regime-adjusted and equilibrium candidates. These imply only modest excess returns over T-bills, which fits a zero-yield asset facing restrictive real rates. The adjustment is modest, about 0.4pp below the auto-blend and within the 5.39-8.90% range. It is limited because gold's candidates are weaker than for cash-flow assets, regime confidence is low, and the BL figure rests on an ETF-size proxy. The result implies an excess return of about 2.4% over the 4.03% T-bill at 17.9% volatility, a Sharpe ratio of roughly 0.13, in line with gold's long-run record and its role as a diversifier rather than a return engine. Confidence is low. The governing IPS (config/ips.yaml) is still a draft, so this assumption should be revisited once the policy is finalised.

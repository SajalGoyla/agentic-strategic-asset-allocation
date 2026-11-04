# CMA — intermediate_treasuries

**Expected return:** 5.26% (3y, nominal, arithmetic)  
**Volatility:** 6.46%  
**Confidence:** medium_high  
**Selection:** custom_blend — survey_consensus 15%, yield_building_block 85%  
**Candidate range:** 4.13% to 6.61% (tight); +0.06pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 6.41 | 0.30 | risk_free_pct +4.03, excess_return_pct +2.38, months +441.00 | +2.38% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 6.61 | 0.25 | risk_free_pct +4.03, regime_excess_return_pct +2.55, unconditional_excess_return_pct +2.65, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged +2.55% a year (all months +2.65%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 4.13 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +0.10, market_weight_pct +2.51, risk_aversion +2.50 | Equilibrium excess return +0.10% at a 2.5% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to fixed_income |
| `survey_consensus` | 4.21 | 0.50 | survey_pct +4.00, variance_addback_pct +0.21 | SPF median BOND10 4.00% a year over 10 years + 0.21% variance add-back. |
| `yield_building_block` | 5.45 | 0.80 | yield_pct +5.24, credit_loss_pct -0.00, variance_addback_pct +0.21 | 5.24% starting yield - 0.00% expected credit loss + 0.21% variance add-back (mean of DGS7, DGS10). |
| `auto_blend` | 5.20 | 0.53 | weight:historical_erp +0.13, weight:regime_adjusted +0.11, weight:bl_equilibrium +0.18, weight:survey_consensus +0.22, weight:yield_building_block +0.36 | Confidence-weighted average of 5 methods: historical_erp 13%, regime_adjusted 11%, bl_equilibrium 18%, survey_consensus 22%, yield_building_block 36%. |

## Judgment

**Regime logic.** The macro read is a low-confidence (0.36) stall-speed expansion bordering on late-cycle, with sticky inflation and restrictive real rates. For intermediate Treasuries the two tails pull in opposite directions. Sticky inflation and a tight policy stance argue that yields could stay high or drift higher, which over a 3-year horizon shorter than the roughly 7-year duration would erode returns below the starting yield. The 20-30% recession probability argues for yield declines and duration gains. Because the regime call is weak and the risks are two-sided, it does not justify a large departure from the starting yield. It also argues against the regime_adjusted candidate. That figure is built on a generic 'expansion' label whose forward 3-year windows are dominated by the 1990-2021 secular bull market in bonds, and the regime_fit signal (-0.17) shows Treasuries have historically underperformed in expansion months.

**Valuation context.** Valuation is the dominant input for this asset. The 5.24% starting yield (mean of DGS7 and DGS10) sits high against its own post-1990 history (yield_level +0.80), so the forward return anchor is attractive, and it carries no credit loss to net out. The historical_erp (6.41%) and regime_adjusted (6.61%) candidates sit above the yield. Their excess returns came largely from a 30-year fall in yields that cannot repeat from today's level, so they deserve little weight. BL equilibrium (4.13%) is low because Treasuries hedge an equity-heavy ETF market portfolio, which gives them a near-zero CAPM premium. That is a structural artifact, not a valuation view. The SPF BOND10 survey (4.21%) is a 10-year average-return expectation that sits below today's yield. It likely embeds some expected yield normalisation, and it may lag the latest repricing.

**Signal alignment.** The signals split cleanly by type. The valuation signal (yield level +0.80) is strongly positive and confirms the yield-based anchor. The technical signals are negative (trend -0.67, relative momentum -0.56, 12-1 momentum -0.28), reflecting the recent rise in yields and the -3.75% one-year return. The macro alignment signals are essentially zero. At a 3-year horizon, the starting yield has far more predictive power than price momentum for bonds. The negative momentum is still a reasonable reason to hedge a little for further back-up in yields. I do that with a small survey weight rather than following the momentum signals outright, which pulls the estimate about 20bp below the yield building block.

**Rationale.** For an intermediate Treasury fund over a horizon near its duration, the yield building block is the strongest single candidate. It has the highest confidence (0.80), uses fresh FRED yields, and carries no credit-loss term, so I give it 85% weight. The specific reason for departing from it is that the 3-year horizon is shorter than the fund's roughly 7-year duration. With sticky inflation, restrictive policy and negative price momentum, some risk of further yield increases remains. I therefore put 15% on the SPF BOND10 survey (4.21%), which embeds a lower expected bond return. The historical and regime-adjusted methods are excluded because their excess returns reflect the secular decline in yields from 1990 to 2021. BL equilibrium is excluded because its near-zero premium is a CAPM hedging artifact, not a return forecast. The auto-blend (5.20%) is not adopted because it gives 64% combined weight to these weaker or structurally biased candidates. The result is 5.26%, within the 4.13-6.61% range and close to the 5.45% yield-implied figure. It implies roughly a 1.2pp premium over the 4.03% T-bill at 6.46% volatility, a Sharpe ratio near 0.19, which is plausible for duration risk. The governing IPS (config/ips.yaml) is still a draft, so this assumption should be revisited when the policy is finalised.

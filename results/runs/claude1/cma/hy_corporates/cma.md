# CMA — hy_corporates

**Expected return:** 6.16% (3y, nominal, arithmetic)  
**Volatility:** 8.44%  
**Confidence:** medium_high  
**Selection:** custom_blend — bl_equilibrium 10%, regime_adjusted 15%, yield_building_block 75%  
**Candidate range:** 5.79% to 7.76% (tight); -0.26pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 7.76 | 0.30 | risk_free_pct +4.03, excess_return_pct +3.73, months +441.00 | +3.73% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 7.10 | 0.25 | risk_free_pct +4.03, regime_excess_return_pct +2.76, unconditional_excess_return_pct +3.98, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged +2.76% a year (all months +3.98%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.79 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +1.76, market_weight_pct +0.97, risk_aversion +2.50 | Equilibrium excess return +1.76% at a 1.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to fixed_income |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 6.02 | 0.80 | yield_pct +8.16, credit_loss_pct -2.50, variance_addback_pct +0.36 | 8.16% starting yield - 2.50% expected credit loss + 0.36% variance add-back (mean of BAMLH0A0HYM2EY). |
| `auto_blend` | 6.42 | 0.54 | weight:historical_erp +0.17, weight:regime_adjusted +0.14, weight:bl_equilibrium +0.23, weight:yield_building_block +0.46 | Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%. |

## Judgment

**Regime logic.** The stage-1 call is a low-confidence (0.36) stall-speed expansion bordering on late-cycle, with a 20-30% recession probability. For high yield, the regime matters mainly through the default path rather than through rates. The building block's 2.50% expected credit loss is roughly a through-cycle figure: about 4% defaults at 60% loss. That already allows for a moderate rise in defaults without assuming a recession, which fits a borderline late-cycle reading. A recession would push realised losses well above 2.5%, but at a 20-30% probability that belongs in the volatility and tail, not in the central estimate. The regime_adjusted candidate (7.10%) carries modest weight because it is forward-looking from past expansion months and comes in below the unconditional premium (2.76% vs 3.98% excess). It is still above the yield anchor, though, and the low regime confidence argues against leaning on any regime-conditioned history.

**Valuation context.** The starting yield of 8.16% is high against its own history: the yield_level signal is +0.65. The credit_spread signal of +0.01 shows that the spread itself is only around its historical median, so the attractive all-in yield comes mainly from restrictive base rates, not from generous compensation for credit risk. That makes the yield-minus-losses arithmetic the right anchor. It also means no extra spread-compression upside should be added. The 2.50% loss is netted once, inside yield_building_block, and nothing further is deducted. historical_erp (7.76%) is excluded. Its 1990-2026 sample rode a secular fall in yields, and it embeds an average spread environment that the current median spread does not support. Including it would double-count past capital gains rather than reflect today's carry.

**Signal alignment.** The composite signal is only +0.08, and the split is informative. Valuation is constructive because the yield is high, while the technicals are negative: trend -0.34, mean_reversion -0.28, momentum mildly negative. The macro alignments are near zero. The negative technicals, together with a weak 1-year return (0.89%) and a 3-year run that the mean-reversion signal flags as stretched, argue against tilting toward the higher historical and regime candidates. This supports keeping the estimate close to the yield anchor and slightly below the 6.42% auto-blend. The small weight on bl_equilibrium (5.79%) acts as a modest hedge against spread widening, without letting a CAPM figure based on ETF weights drive a carry-dominated asset.

**Rationale.** For high yield at a 3-year horizon, close to the asset's duration, yield_building_block is the strongest single candidate. Its confidence is 0.80, and it starts from the observed 8.16% yield, nets a through-cycle 2.50% credit loss once, and adds a small variance term. It gets 75% weight. The auto-blend gives it only 46% and puts 17% on historical_erp. That historical figure reflects a secular decline in yields and an average-spread history that today's median spread does not support, so it is dropped entirely. regime_adjusted takes 15% as a forward-looking, credibility-shrunk view of expansion-period excess returns. bl_equilibrium takes 10% as a cautious counterweight given negative technicals and a 20-30% recession probability. The result is 0.75×6.02 + 0.15×7.10 + 0.10×5.79 = 6.16%. That sits inside the [5.79, 7.76] range, about 0.14pp above the pure yield anchor and 0.26pp below the auto-blend. It implies an excess return of roughly 2.1% over a 4.03% T-bill, about 0.25 per unit of the 8.44% volatility, which is reasonable for high yield with spreads at median. Confidence is medium-high: dispersion is tight and the anchor is strong, but the credit-loss assumption carries the main uncertainty and would prove too low in a recession. The governing IPS (config/ips.yaml) is still a draft, so this assumption should be revisited once the policy is finalised.

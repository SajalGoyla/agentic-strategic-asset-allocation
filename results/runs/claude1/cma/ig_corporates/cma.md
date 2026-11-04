# CMA — ig_corporates

**Expected return:** 5.94% (3y, nominal, arithmetic)  
**Volatility:** 7.14%  
**Confidence:** medium_high  
**Selection:** custom_blend — bl_equilibrium 20%, yield_building_block 80%  
**Candidate range:** 5.01% to 6.71% (tight); -0.14pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 6.71 | 0.30 | risk_free_pct +4.03, excess_return_pct +2.68, months +441.00 | +2.68% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 6.71 | 0.25 | risk_free_pct +4.03, regime_excess_return_pct +2.59, unconditional_excess_return_pct +2.94, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged +2.59% a year (all months +2.94%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.01 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +0.98, market_weight_pct +1.93, risk_aversion +2.50 | Equilibrium excess return +0.98% at a 1.9% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to fixed_income |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 6.17 | 0.80 | yield_pct +6.02, credit_loss_pct -0.10, variance_addback_pct +0.25 | 6.02% starting yield - 0.10% expected credit loss + 0.25% variance add-back (mean of BAMLC0A0CMEY). |
| `auto_blend` | 6.08 | 0.54 | weight:historical_erp +0.17, weight:regime_adjusted +0.14, weight:bl_equilibrium +0.23, weight:yield_building_block +0.46 | Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%. |

## Judgment

**Regime logic.** Stage 1 calls a stall-speed expansion, borderline late-cycle, but at low confidence (0.36). It puts recession probability at 20-30%, with sticky inflation and restrictive real rates. For IG corporates the regime matters through two channels. First, if growth rolls over, a late-cycle tilt raises the chance of spread widening over the 3-year window. Second, any easing would offset that widening through the duration gain. The two roughly net, so the regime does not justify leaning toward the regime-adjusted candidate. Its 2.59% conditional excess comes from 1990-2026 expansion months that rode a secular fall in yields, and the label it conditions on is itself low-confidence. I therefore use the regime only to justify a modest equilibrium haircut to the yield anchor, not a move to the backward-looking methods.

**Valuation context.** Starting yield is the dominant valuation fact for this asset. A 6.02% effective yield on BAMLC0A0CMEY sits high against its own history, and the yield_level signal is +0.46. That makes yield_building_block the right anchor over a horizon near duration. The 0.10% credit-loss deduction is appropriate for IG: the spread already prices default risk, so I do not subtract more. Spreads point the other way, though. They are narrow versus history (credit_spread signal -0.21), so the yield's richness comes from the risk-free component, not from credit compensation. There is little cushion against spread widening. The 3-year horizon is also shorter than IG index duration (about 7 years), so the starting yield is a somewhat noisier predictor here than at full duration. These two points are why I shade below 6.17% rather than above it. I give zero weight to the historical candidates (6.71%) because their excess return embeds three decades of duration windfall from falling yields, which today's starting level does not support repeating.

**Signal alignment.** The composite is mildly bearish (-0.10), and almost all of that comes from technicals. Trend (-0.65), relative momentum (-0.67) and 12-1 momentum (-0.32) reflect the poor trailing year (-4.03%). Momentum in bonds is a weak forecaster over a 3-year horizon, and recent losses are partly what lifted the starting yield. Valuation signals split: the high yield level is bullish, while tight spreads are bearish. The macro alignment signals are near zero. On balance the signals do not overturn the yield anchor. They do support hedging slightly below it rather than adopting the historical candidates at the top of the range, which the 20% BL weight does.

**Rationale.** For investment-grade corporates at a 3-year horizon, the starting yield less expected credit loss is the strongest single predictor. yield_building_block (6.17%, confidence 0.80, sourced from the actual ICE IG effective yield rather than a proxy) therefore carries 80% of the weight. I put the remaining 20% on bl_equilibrium (5.01%) for three reasons: the horizon is shorter than duration, spreads are tight with little cushion, and recession probability is non-trivial. BL is an imperfect, ETF-size-based CAPM anchor, so I do not weight it more heavily. I excluded historical_erp and regime_adjusted (both 6.71%) despite the auto-blend giving them 31% combined. Their premia are inflated by the 1990-2026 secular decline in yields, and the regime label behind the conditional figure is low-confidence. The result is 0.8×6.17 + 0.2×5.01 = 5.94%, inside the [5.01, 6.71] range and 0.14pp below the 6.08% auto-blend. Against the 7.14% volatility and the 4.03% T-bill, that implies a Sharpe of about 0.27, plausible for IG credit. Dispersion is tight, as expected for a bond whose return is largely set by its yield. The governing IPS (config/ips.yaml) is still a draft, so this assumption should be revisited once the policy is finalised.

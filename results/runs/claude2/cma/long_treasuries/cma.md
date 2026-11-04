# CMA — long_treasuries

**Expected return:** 6.09% (3y, nominal, arithmetic)  
**Volatility:** 12.43%  
**Confidence:** medium  
**Selection:** custom_blend — bl_equilibrium 15%, yield_building_block 85%  
**Candidate range:** 4.19% to 8.23% (moderate); -0.18pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 6.98 | 0.30 | risk_free_pct +4.03, excess_return_pct +2.95, months +441.00 | +2.95% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 8.23 | 0.25 | risk_free_pct +4.03, regime_excess_return_pct +4.41, unconditional_excess_return_pct +3.55, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged +4.41% a year (all months +3.55%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 4.19 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +0.16, market_weight_pct +2.83, risk_aversion +2.50 | Equilibrium excess return +0.16% at a 2.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to fixed_income |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 6.43 | 0.80 | yield_pct +5.66, credit_loss_pct -0.00, variance_addback_pct +0.77 | 5.66% starting yield - 0.00% expected credit loss + 0.77% variance add-back (mean of DGS20, DGS30). |
| `auto_blend` | 6.27 | 0.54 | weight:historical_erp +0.17, weight:regime_adjusted +0.14, weight:bl_equilibrium +0.23, weight:yield_building_block +0.46 | Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%. |

## Judgment

**Regime logic.** The stage-1 call is a stall-speed expansion with sticky inflation and restrictive real rates, bordering on late-cycle, at low confidence (0.36). For long Treasuries this regime cuts both ways. A 20-30% recession probability is an upside tail, because a growth scare would pull long yields down and produce sizeable price gains at roughly 16-17 years of duration. Sticky inflation (-0.27) is the main downside risk: it could keep term premia rising and push long yields higher. Given that two-sided balance and the weak regime confidence, I give no weight to regime_adjusted (8.23%). Its 'expansion' conditioning is fragile here. It is also inflated by the 1990-2026 secular bond rally, so its +4.41% forward excess return mostly reflects falling yields that cannot repeat from today's starting point in the same way.

**Valuation context.** The starting yield of 5.66% (mean of 20y and 30y) is high against post-2008 history. The yield_level signal (+0.79) confirms long bonds are cheap relative to their own record. That favours anchoring on the yield, which already embeds the current term premium. The backward-looking historical_erp (6.98%) and regime_adjusted (8.23%) are distorted by three decades of falling yields that added capital gains on top of carry, so they overstate what carry plus a stable yield delivers. Here the valuation-based and historical methods agree on direction but not on cause: the yield is high because yields rose, and the historical methods are high because yields fell. Only the first is a guide forward. One tempering point: the 3-year horizon is well short of the roughly 16-17 year duration. Starting yield is therefore a less exact predictor than it would be at a horizon matched to duration, and price changes over three years can dominate either way.

**Signal alignment.** The composite signal (+0.16) is mildly positive and supports a yield-anchored estimate rather than a haircut toward the minimum. Valuation (yield_level +0.79) and the 36-month mean-reversion signal (+0.23) point up. Technicals are clearly negative: trend -0.56, 12-1 momentum -0.28, and relative momentum -0.89, the weakest of the 18 classes. The 1y return of -8.98% and 5y return of -8.46% show selling pressure has not abated. Macro alignment signals are essentially zero, so the macro dimensions offer little directional information for this asset. I hedge the bearish momentum by placing modest weight on the low Black-Litterman equilibrium (4.19%) rather than adding the high historical methods, which would lean against the trend.

**Rationale.** For a long-duration Treasury with no credit risk, the yield building block (6.43%, confidence 0.80) is the strongest candidate and the anchor. I depart from it slightly, toward bl_equilibrium (4.19%), for three reasons: horizon mismatch, negative momentum, and inflation risk. First, the 3-year horizon is far shorter than duration, so the starting yield does not lock in the return. Second, momentum and trend are strongly negative. Third, sticky inflation leaves room for long yields and term premia to rise further, which a 0.77pp variance add-back on a single starting yield does not capture. BL's near-zero equilibrium premium reflects long Treasuries' hedging role against the equity-heavy ETF portfolio. That is a coherent counterweight, even though ETF sizes are a rough proxy for market size, which is why it gets only 15%. Historical_erp and regime_adjusted are excluded because 1990-2026 was a secular fall in yields that inflates their excess returns. The resulting 6.09% (0.85 x 6.43 + 0.15 x 4.19) is slightly below the auto-blend (6.27%), sits well inside the [4.19, 8.23] range, and implies roughly 2.1pp over the 4.03% T-bill, a Sharpe of about 0.16 at 12.43% volatility. That is consistent with a modest term premium. Confidence is medium rather than high because of the duration-horizon mismatch and two-sided macro risk. The governing IPS (config/ips.yaml) is still a draft, so this assumption should be revisited once the policy is finalised.

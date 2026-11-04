# CMA — intl_corporates

**Expected return:** 5.21% (3y, nominal, arithmetic)  
**Volatility:** 9.18%  
**Confidence:** medium  
**Selection:** custom_blend — bl_equilibrium 25%, regime_adjusted 15%, yield_building_block 60%  
**Candidate range:** 4.99% to 6.14% (tight); -0.21pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 6.14 | 0.30 | risk_free_pct +4.03, excess_return_pct +2.11, months +441.00 | +2.11% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 4.99 | 0.25 | risk_free_pct +4.03, regime_excess_return_pct +0.59, unconditional_excess_return_pct +2.07, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged +0.59% a year (all months +2.07%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.45 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +1.42, market_weight_pct +0.02, risk_aversion +2.50 | Equilibrium excess return +1.42% at a 0.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to fixed_income |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 5.16 | 0.48 | yield_pct +4.00, credit_loss_pct -0.10, variance_addback_pct +0.42, spread_pct +0.84 | 4.00% starting yield + 0.84% spread - 0.10% expected credit loss + 0.42% variance add-back (mean of IRLTLT01DEM156N, IRLTLT01GBM156N; + BAMLC0A0CM spread; local-currency yield on an unhedged USD holding). |
| `auto_blend` | 5.42 | 0.38 | weight:historical_erp +0.21, weight:regime_adjusted +0.17, weight:bl_equilibrium +0.28, weight:yield_building_block +0.34 | Confidence-weighted average of 4 methods: historical_erp 21%, regime_adjusted 17%, bl_equilibrium 28%, yield_building_block 34%. |

## Judgment

**Regime logic.** Stage 1 calls a stall-speed expansion bordering on late cycle, with sticky inflation and restrictive real rates, but only at low confidence (0.36). For an investment-grade bond sleeve, that mix argues for anchoring on carry rather than on regime-conditioned history. Restrictive policy with 20-30% recession odds means spreads are more likely to widen than tighten from here, which points toward the lower end of the range. That is why regime_adjusted (4.99%) gets a modest weight. Its expansion-conditioned forward excess return of +0.59% reflects how poorly this asset did in the three years after past expansion months. Given how weak the regime classification is, I do not let it dominate. Historical_erp gets no weight: its +2.1% excess return was earned during the 1990-2026 secular fall in European and UK yields, a tailwind that cannot repeat from a roughly 4% starting yield. The 10-year realised return of 0.25% shows how unreliable that average is once the tailwind reverses.

**Valuation context.** The yield-level signal (+0.45) says starting yields are high against their own history, and for bonds that is the dominant predictor of return over a horizon near duration. That supports making yield_building_block the anchor. The candidate's inputs are proxies, though, so I trim its weight below what a clean local index yield would earn. The base yield is the mean of the German and UK 10-year government yields, and the 0.84% spread is the US IG OAS (BAMLC0A0CM), not a spread on the international corporate index itself. The 0.10% expected credit loss is already netted from the spread, so I make no further default deduction. The credit-spread signal (-0.21) says spreads are tight against history, so there is little room for spread compression and some risk of widening. PICB is unhedged, so the USD return also carries currency moves that none of the candidates forecast. Most of the 9.18% volatility is that FX component rather than credit.

**Signal alignment.** The composite signal is near neutral (-0.05) but split. Valuation is supportive through the yield level and mildly negative through tight spreads. Macro alignment is negligible: every macro loading is small and the regime-fit signal is zero. Technicals are clearly negative: trend -0.48, relative momentum -0.44, mean reversion -0.33, and a 1-year return of -3.47%. That points to near-term weakness, probably partly dollar-driven. Technical signals are weak predictors over a 3-year horizon for a carry asset, so I hedge against them only modestly. I tilt slightly below the auto-blend (5.42%) by dropping historical_erp and keeping a regime_adjusted weight, rather than moving toward the bottom of the range.

**Rationale.** Dispersion is tight (1.15pp), so the choice matters at the margin rather than in direction. Weights are 60% yield_building_block (5.16%), the strongest single candidate for an IG bond at a horizon near duration. 25% goes to bl_equilibrium (5.45%), a risk-based cross-check independent of the yield proxy and computed on the same covariance matrix the PC stage uses. 15% goes to regime_adjusted (4.99%), reflecting late-cycle spread risk. Historical_erp gets zero, because its premium was earned over a secular yield decline that cannot recur from today's levels. The result is 5.21%: about 1.2pp over the 4.03% T-bill, a Sharpe of roughly 0.13 at 9.18% volatility. That is plausible for unhedged international IG credit whose risk is mostly currency. Confidence is medium rather than high: the yield input is a German/UK government-yield proxy plus a US IG spread, and the currency exposure is not forecast. Governing policy is config/ips.yaml, which is still a draft; this CMA should be revisited once the IPS is finalised.

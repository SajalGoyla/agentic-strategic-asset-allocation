# CMA — intl_corporates

**Expected return:** 5.16% (3y, nominal, arithmetic)  
**Volatility:** 9.18%  
**Confidence:** medium  
**Selection:** custom_blend — bl_equilibrium 25%, regime_adjusted 10%, yield_building_block 65%  
**Candidate range:** 4.44% to 6.14% (tight); -0.16pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 6.14 | 0.30 | risk_free_pct +4.03, excess_return_pct +2.11, months +441.00 | +2.11% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 4.44 | 0.25 | risk_free_pct +4.03, regime_excess_return_pct +0.04, unconditional_excess_return_pct +1.37, regime_months +155.00, credibility_weight +0.72 | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +0.04% a year (all months +1.37%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.45 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +1.42, market_weight_pct +0.02, risk_aversion +2.50 | Equilibrium excess return +1.42% at a 0.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to fixed_income |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 5.16 | 0.48 | yield_pct +4.00, credit_loss_pct -0.10, variance_addback_pct +0.42, spread_pct +0.84 | 4.00% starting yield + 0.84% spread - 0.10% expected credit loss + 0.42% variance add-back (mean of IRLTLT01DEM156N, IRLTLT01GBM156N; + BAMLC0A0CM spread; local-currency yield on an unhedged USD holding). |
| `auto_blend` | 5.32 | 0.38 | weight:historical_erp +0.21, weight:regime_adjusted +0.17, weight:bl_equilibrium +0.28, weight:yield_building_block +0.34 | Confidence-weighted average of 4 methods: historical_erp 21%, regime_adjusted 17%, bl_equilibrium 28%, yield_building_block 34%. |

## Judgment

**Regime logic.** Stage 1 calls a fragile, late-cycle-adjacent expansion with sticky inflation, at low confidence (0.35) and a 20-30% recession probability. For an unhedged euro-heavy corporate bond index, late-cycle logic favours the starting-yield anchor over backward-looking premia. The regime-adjusted candidate (4.44%) shows that past expansion months were followed by near-zero excess returns (+0.04%). That fits an asset whose credit leg widens as cycles mature and whose currency leg suffers in dollar-strength episodes. Because the regime call is low-confidence and the method already shrinks toward the unconditional premium, I give it a modest 10% as a late-cycle haircut rather than a driving weight. The recession tail argues against the historical ERP, not for a larger adjustment.

**Valuation context.** The valuation lens is local long yields (mean of German and UK 10-year, 4.00%) plus a credit spread. That spread is proxied from the US IG OAS (BAMLC0A0CM, 0.84%), because no non-US series has the history. European credit cycles correlate with US ones but are not identical, and the estimate inherits that approximation. The yield-level signal (+0.45) says starting local yields are high against their own history, the strongest predictor of bond returns over a horizon near duration. The 0.10% expected credit loss is already netted once in the building block; I did not subtract it again. The building block is a local-currency yield on an unhedged USD holding, so it says nothing about EUR/GBP versus USD. Currency is the first driver of this asset's return and the credit spread only the second. With German/UK average yields roughly level with the 4.03% US T-bill, carry gives no strong reason to tilt the estimate either way, so FX enters as volatility rather than as an expected-return adjustment.

**Signal alignment.** The composite is roughly neutral (+0.06), with a split underneath. Valuation is constructive (yield_level +0.45), while every technical signal is negative: trend -0.48, relative momentum -0.44, mean reversion -0.33, 12-1 momentum -0.13. This matches a 1-year return of -3.47%, likely driven by currency and rate moves rather than credit. Macro alignments are all near zero. Technicals matter little over a 3-year horizon for a bond whose return is mostly carry, so they do not justify moving below the yield anchor. They do argue against leaning toward the upper end of the range (historical ERP 6.14%). The final figure therefore sits slightly below the auto-blend.

**Rationale.** Under the ratified IPS, I anchor on yield_building_block (65%), the strongest fixed-income candidate at a horizon near duration. I add Black-Litterman (25%) as a cross-check, since its 5.45% equilibrium figure sits close to the yield anchor. Regime_adjusted (10%) adds a modest late-cycle haircut. I give historical_erp zero weight: its 6.14% embeds the 1990-2026 secular fall in European yields and cannot repeat from today's starting point. BL's 0.02% market weight shows how thinly held PICB is, the thinnest index in the fixed-income sleeve, so I hold it below the yield anchor. The result, 5.16%, is about 1.1pp over T-bills, a Sharpe near 0.13 at 9.18% volatility. That is deliberately modest. This is largely a euro position with a proxied European IG credit leg attached, and it duplicates intl_sovereigns (currency) and ig_corporates (credit). The estimate should not make it look clearly preferable to holding those two separately. Confidence is medium rather than high for three reasons: currency risk sits outside the forecast, the spread is a US proxy, and the index history is noisy.

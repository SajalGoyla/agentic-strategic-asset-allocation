# CMA — us_small_cap

**Expected return:** 9.34% (3y, nominal, arithmetic)  
**Volatility:** 19.48%  
**Confidence:** low  
**Selection:** custom_blend — bl_equilibrium 30%, historical_erp 15%, implied_erp_cape 20%, inverse_gordon 25%, regime_adjusted 10%  
**Candidate range:** 6.65% to 12.38% (moderate); -0.67pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 12.38 | 0.50 | risk_free_pct +4.03, excess_return_pct +8.35, months +441.00 | +8.35% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 11.78 | 0.40 | risk_free_pct +4.03, regime_excess_return_pct +7.65, unconditional_excess_return_pct +8.00, regime_months +155.00, credibility_weight +0.72 | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +7.65% a year (all months +8.00%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.82 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +4.79, market_weight_pct +4.83, risk_aversion +2.50 | Equilibrium excess return +4.79% at a 4.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 6.65 | 0.42 | dividend_yield_pct +1.21, net_buyback_yield_pct -0.86, real_growth_pct +2.10, inflation_pct +2.30, valuation_change_pct +0.00, variance_addback_pct +1.90 | 1.21% dividends -0.86% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.90% variance add-back (net payout from WRDS 2025-12, rolled forward by IWM's price change; no long valuation history, drift 0). |
| `implied_erp_cape` | 9.98 | 0.35 | earnings_yield_pct +5.78, inflation_pct +2.30, variance_addback_pct +1.90 | 5.78% real earnings yield (IWM trailing earnings yield) + 2.3% expected inflation + 1.90% variance add-back. |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | – | – | – | unavailable: not applicable to equity |
| `auto_blend` | 10.01 | 0.42 | weight:historical_erp +0.24, weight:regime_adjusted +0.19, weight:bl_equilibrium +0.19, weight:inverse_gordon +0.20, weight:implied_erp_cape +0.17 | Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%. |

## Judgment

**Regime logic.** Stage 1 calls an expansion, but a fragile, late-cycle-adjacent one. Confidence is low (0.35), inflation is sticky and policy is restrictive, with a 20-30% recession probability. For small caps this matters more than for any other equity sleeve (consideration 3). Russell 2000 balance sheets carry more floating-rate and short-maturity debt, so a 4% T-bill and restrictive policy press directly on interest coverage, not just on the discount rate. Exhibit 4 tilts late-cycle environments toward valuation and regime-adjusted methods, and the low regime confidence argues against leaning on any regime-conditional figure. The regime_adjusted candidate (11.78%) rests on 155 'expansion' months that were mostly not this fragile, high-rate variety, and its credibility weight of 0.72 does not fix the label risk. I cut it to 10%. The weight goes to equilibrium (BL) and to cash-flow and earnings-based anchors, which do not depend on the regime label being right.

**Valuation context.** Consideration 2 rules out treating index-level P/E or CAPE as reliable here: roughly 40% of Russell 2000 constituents lose money. The implied_erp_cape candidate uses IWM's vendor trailing earnings yield (5.78%), not the WRDS aggregate. Vendor P/E effectively excludes loss-makers, so this is closer to the profitable-subset earnings yield the asset file prefers. That makes it usable, but it overstates the earnings power of the whole index. I therefore kept it at 20%, slightly above its auto-blend share but below what a clean earnings yield would earn. The inverse_gordon candidate (6.65%) is the most conservative input. Net buybacks are -0.86%, meaning net issuance and dilution, a real and persistent drag for small caps that large caps do not have. It also applies aggregate GDP growth with zero valuation drift, since there is no long valuation history to anchor a reversion. I gave it 25% because dilution is a genuine reduction in holder return, not a data artefact. The preferred relative lens, price/book or EV/sales against large cap, is not among the computed inputs. I cannot cite a quantified small-versus-large discount and have not assumed one. On the relative cases §3.3 asks for: US Large Cap's blend sits near 8.3% at about 15% volatility. A small-cap figure around 9.3% at 19.5% volatility gives a modest size premium with a lower Sharpe ratio (about 0.27), which is consistent with the dilution and rate headwinds. Against high yield, a profitable-subset real earnings yield near 5.8% plus about 2.3% inflation is broadly comparable to typical HY yields after credit losses. That makes the equity case roughly at parity, not compelling, which supports a mid-range estimate.

**Signal alignment.** The composite is mildly bullish (+0.14), but the parts conflict. Relative momentum (+0.67) and 12-1 momentum (+0.33) reflect a strong recent run: 16% over 1 year and 17.6% a year over 3 years. Mean reversion (-0.51) says that 36-month stretch tends to give back. Trend is slightly negative (-0.08). The macro alignment signals are near zero, apart from supportive financial conditions (+0.10). The signals neither confirm the high backward-looking candidates nor justify sitting at the Gordon floor. The mean-reversion reading over a 3-year horizon is a reason not to extrapolate the recent run, and so not to weight historical_erp heavily. I hedged by staying near the middle of the range, slightly below the auto-blend.

**Rationale.** The final estimate is 9.34%, a custom blend: BL equilibrium 30%, inverse Gordon 25%, implied earnings yield 20%, historical ERP 15% and regime-adjusted 10%. This sits about 0.7pp below the auto-blend (10.01%), well inside [6.65, 12.38].

The main departure from the confidence weights is shifting about 0.18 of weight from the two backward-looking methods to BL equilibrium.
- Historical_erp (8.35% excess over T-bills since 1990) is a full-sample average that sits well above the asset's realised 9.58% total return since 1990. It embeds a period of falling rates that small caps, the most rate-sensitive equity sleeve, will not repeat with T-bills at 4%.
- Regime_adjusted depends on a low-confidence regime label.
- BL is the cleanest forward anchor. Its 4.8% market weight is ETF AUM, a proxy for the asset's size, but it is not biased by the sample's strong returns.

On the key considerations:
- I treated the earnings-yield method as a profitable-subset read and did not up-weight it (consideration 2).
- I kept the Gordon dilution term rather than dismissing it.
- I weighed the floating-rate exposure against the restrictive policy backdrop (consideration 3).
- The domestic-revenue profile (consideration 4) makes this a clean read on a fragile US cycle, which supports caution.
- I accepted the index total-return series behind the historical methods (consideration 5).

No survey consensus exists for this asset. No fund-flow or positioning view is claimed, since none can be sourced. Confidence is low: the regime call is low-confidence, the preferred P/B and EV/sales lens is absent, and small-cap return estimates at about 19.5% volatility are imprecise over 3 years. Governing IPS status is ratified.

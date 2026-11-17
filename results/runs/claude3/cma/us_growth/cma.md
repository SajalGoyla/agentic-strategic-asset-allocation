# CMA — us_growth

**Expected return:** 8.28% (3y, nominal, arithmetic)  
**Volatility:** 16.91%  
**Confidence:** low  
**Selection:** custom_blend — bl_equilibrium 25%, historical_erp 5%, implied_erp_cape 33%, inverse_gordon 32%, regime_adjusted 5%  
**Candidate range:** 7.12% to 13.69% (wide); -2.01pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 13.46 | 0.50 | risk_free_pct +4.03, excess_return_pct +9.43, months +441.00 | +9.43% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 13.69 | 0.40 | risk_free_pct +4.03, regime_excess_return_pct +9.86, unconditional_excess_return_pct +9.12, regime_months +155.00, credibility_weight +0.72 | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +9.86% a year (all months +9.12%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.54 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +4.51, market_weight_pct +7.54, risk_aversion +2.50 | Equilibrium excess return +4.51% at a 7.5% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 7.61 | 0.42 | dividend_yield_pct +0.65, net_buyback_yield_pct +1.12, real_growth_pct +2.10, inflation_pct +2.30, valuation_change_pct +0.00, variance_addback_pct +1.43 | 0.65% dividends +1.12% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.43% variance add-back (net payout from WRDS 2025-12, rolled forward by IWF's price change; no long valuation history, drift 0). |
| `implied_erp_cape` | 7.12 | 0.35 | earnings_yield_pct +3.39, inflation_pct +2.30, variance_addback_pct +1.43 | 3.39% real earnings yield (IWF trailing earnings yield) + 2.3% expected inflation + 1.43% variance add-back. |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | – | – | – | unavailable: not applicable to equity |
| `auto_blend` | 10.29 | 0.42 | weight:historical_erp +0.24, weight:regime_adjusted +0.19, weight:bl_equilibrium +0.19, weight:inverse_gordon +0.20, weight:implied_erp_cape +0.17 | Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%. |

## Judgment

**Regime logic.** Stage 1 calls an expansion, but a fragile, late-cycle-adjacent one, at low confidence (0.35), with sticky above-history inflation, a restrictive monetary-policy score (-0.22) and a 20-30% recession probability. Exhibit 4 tilts late-cycle conditions toward valuation and regime-adjusted methods. Here, though, the regime-adjusted candidate (13.69%) is simply the 'expansion' label applied at full credibility (0.72). It is not conditioned on the late-cycle or inflation features that matter most for the longest-duration equity sleeve, which loses on the discount-rate channel if inflation stays sticky and rates stay high. Given how weak the regime call is, I treat the regime candidate as a cousin of the historical ERP, not as independent evidence. I give it 5%, below its 19% auto-blend weight.

**Valuation context.** This is the most expensive sleeve in the universe. IWF's trailing earnings yield is 3.39%, below the 4.03% T-bill, so the real earnings-yield build gives only about 3.1pp over cash once inflation and the variance add-back are included. The net payout yield is 1.77%, which needs 4.4% nominal growth just to reach the Gordon figure. Neither valuation candidate includes a multiple-compression term: Gordon's valuation change is set to 0 because there is no long valuation history outside US Large Cap. Both are therefore, if anything, generous for a sleeve whose 10-year return of 17.95% was flattered by re-rating. The historical ERP (13.46%) comes from a 1990-2026 sample dominated by growth and technology multiple expansion, and it is the method least suited to valuations at an extreme. Valuation and history disagree by about 6pp, which is information about where multiples stand, not noise. Mean reversion is slow and 3 years is short, so I do not go to the floor. I put 65% on the two valuation methods, above the paper's 60%.

**Signal alignment.** The composite is flat (0.00), but its parts point the same way as the markdown. Mean reversion is strongly negative (-0.55) after a 24% annualised 3-year run, and 12-1 momentum is negative (-0.19). Trend (+0.04) and relative momentum (+0.11) are only marginally positive. Regime fit (+0.26) is the one constructive signal, and it rests on the same low-confidence expansion label I have already discounted. The macro alignments are near zero; the small inflation drag (-0.04) is consistent with the asset's inflation and rate sensitivities. Nothing in the signals argues for leaning back toward the historical candidates, so they confirm a below-blend estimate rather than hedge against it.

**Rationale.** Final estimate 8.28%: about 2.0pp below the 10.29% auto-blend, matching the paper's Exhibit 8 markdown for US Growth, its largest in the universe. The weights are 65% on the valuation methods (implied ERP 33%, inverse Gordon 32%), 25% on Black-Litterman equilibrium, and 5% each on the historical ERP and regime-adjusted methods.

Why the historical candidates are cut: they are near-identical backward-looking views from a sample of secular multiple expansion. Taking them together at a combined 43% of the auto-blend would let one hindsight-heavy view drive the result.

Why the valuation candidates are not pushed further: I do not let them pull the estimate to the 7.12% floor, because neither carries an explicit valuation-drift term and a 3-year horizon is short for reversion. That leaves the estimate above the floor but within the bottom quarter of the range.

Black-Litterman (8.54%) gets a meaningful weight as a neutral anchor. It sits close to the valuation cluster, which is independent support for an estimate in the low 8s.

The markdown is meant to be the largest among the equity sleeves; this is the most expensive, most concentrated and longest-duration one. If another sleeve's judge marks down more, the PC stage should revisit the comparison.

Other points for the PC stage:
- **Concentration:** the top ten names can exceed half the index, so effective breadth is low. That is a further reason for a modest return expectation, not a diversification argument.
- **Overlap with US Large Cap:** correlation is above 0.9. US Growth should be read as a tilt on US Large Cap, not a separate holding, and holding both concentrates the portfolio in a handful of mega-cap technology names.
- **Implied Sharpe:** the estimate is about 4.25pp over cash at 16.9% volatility, roughly 0.25, which is deliberately low.
- **Sentiment:** no fund-flow or positioning view is claimed, because none is sourced, and the survey consensus is unavailable for this asset.

The governing IPS is reported as ratified.

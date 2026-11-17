# CMA — intl_developed

**Expected return:** 8.18% (3y, nominal, arithmetic)  
**Volatility:** 16.00%  
**Confidence:** medium  
**Selection:** custom_blend — bl_equilibrium 25%, historical_erp 25%, implied_erp_cape 15%, inverse_gordon 10%, regime_adjusted 25%  
**Candidate range:** 7.67% to 8.94% (tight); -0.07pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 8.29 | 0.50 | risk_free_pct +4.03, excess_return_pct +4.26, months +441.00 | +4.26% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 7.67 | 0.40 | risk_free_pct +4.03, regime_excess_return_pct +3.34, unconditional_excess_return_pct +4.41, regime_months +155.00, credibility_weight +0.72 | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +3.34% a year (all months +4.41%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.02 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +3.99, market_weight_pct +4.77, risk_aversion +2.50 | Equilibrium excess return +3.99% at a 4.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 8.48 | 0.29 | dividend_yield_pct +2.80, net_buyback_yield_pct +0.00, real_growth_pct +2.10, inflation_pct +2.30, valuation_change_pct +0.00, variance_addback_pct +1.28 | 2.80% dividends +0.00% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.28% variance add-back (dividends from WRDS 2026-09; no buyback data; no long valuation history, drift 0). |
| `implied_erp_cape` | 8.94 | 0.35 | earnings_yield_pct +5.37, inflation_pct +2.30, variance_addback_pct +1.28 | 5.37% real earnings yield (EFA trailing earnings yield) + 2.3% expected inflation + 1.28% variance add-back. |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | – | – | – | unavailable: not applicable to equity |
| `auto_blend` | 8.25 | 0.40 | weight:historical_erp +0.26, weight:regime_adjusted +0.21, weight:bl_equilibrium +0.21, weight:inverse_gordon +0.15, weight:implied_erp_cape +0.18 | Confidence-weighted average of 5 methods: historical_erp 26%, regime_adjusted 21%, bl_equilibrium 21%, inverse_gordon 15%, implied_erp_cape 18%. |

## Judgment

**Regime logic.** The stage-1 call is an expansion, but a fragile, late-cycle-adjacent one. It is held at low confidence (0.35), inflation is sticky, policy is restrictive and recession odds are 20-30%. Exhibit 4 says late-cycle should tilt toward regime-adjusted and valuation methods. Here the only real valuation input is a structurally cheap EAFE earnings yield (see valuation_context), so I put the late-cycle tilt into regime_adjusted rather than the valuation methods. I give regime_adjusted equal weight with historical_erp, above its confidence-based share. Its forward-looking construction is informative here: excess returns in the three years after past expansion months were +3.34%, against +4.41% unconditionally, which fits a late-cycle starting point. I do not weight it more heavily for two reasons. The regime label itself is low-confidence, and the 155-month sample mixes two different cycles. Europe is about 60% of the index, exposed to energy costs and ECB policy. Japan is about a fifth, where the governance-reform story has its own momentum. One US-centred regime label fits neither cycle cleanly.

**Valuation context.** EAFE screens cheap. The trailing earnings yield is 5.37%, which drives implied_erp_cape to the top of the range at 8.94%. Key consideration 4 warns that this asset will always look cheap on CAPE against the US. Much of the discount reflects a structurally different sector mix: less technology, and more financials, industrials and staples. Lower long-run growth and governance differences explain more of it. Those parts are not mean-reverting over a 3-year horizon. I therefore cut implied_erp_cape slightly to 15% weight, and I do not credit any valuation re-rating. I also discount inverse_gordon to 10%, for reasons specific to its inputs:
- its yield is dividends only, with zero buybacks (Compustat Global has none);
- its growth term is US SPF real GDP and CPI applied to Europe and Japan;
- its valuation drift is set to zero for lack of history.
With those adjustments, the valuation methods still sit above the backward-looking ones, so valuation adds a modest upward lean rather than a large one. On key consideration 5: the historical, regime and BL candidates are built on the 4.03% US T-bill, not on Bund, JGB or Gilt yields. Local yields are lower than US bills, so a build-up anchored to local rates would come out somewhat lower in local terms. The gap would be offset in USD terms by expected currency carry. I treat the two effects as netting and do not adjust for them.

**Signal alignment.** The composite signal is mildly positive (+0.14), but its components conflict. Momentum is positive (12-1 at +0.33; relative momentum at +0.56, the strongest cross-asset rank). Mean reversion is firmly negative at -0.64, after a 3-year annualised return of 18.3% that is well above the long-run 5.9% since 1990. Trend is flat. Part of that 3-year run is dollar weakness: the USD share class is unhedged, so currency drives both return and volatility. Mean reversion therefore partly implies a risk that the dollar recovers. The macro alignments are close to zero, apart from a small positive from easy financial conditions. Overall, the signals do not justify moving away from the centre of a tight range in either direction. They are consistent with a marginal trim below the auto-blend, not with a call above it. The short-term momentum is real, but a 3-year horizon is long enough for the mean-reversion signal to matter.

**Rationale.** Dispersion is tight: 7.67-8.94%, a 1.28pp spread. The decision is therefore about modest tilts, not method selection. I use a custom blend that cuts the two valuation-based methods relative to the auto-blend and lifts regime_adjusted and bl_equilibrium. The weights are 25% each for historical_erp, regime_adjusted and bl_equilibrium, 10% for inverse_gordon and 15% for implied_erp_cape. The result is 8.18%, 0.07pp below the auto-blend's 8.25%.

The reasons for the tilts:
- Per key consideration 4, EAFE's persistent CAPE and earnings-yield discount is mostly sector mix and structure, not mean-reverting sentiment. I do not let the cheapness signal pull the estimate up.
- The Gordon candidate uses dividends-only inputs and US-based growth, so it gets less weight than its confidence implies.
- The late-cycle-adjacent regime supports the lower regime-conditioned premium.

The markdown is small and close to the paper's -0.3pp. That is deliberate, because return estimates are the least reliable input in the chain.

On currency (key consideration 1), the estimate assumes no expected contribution from the dollar in either direction. The candidates are USD-denominated, but none forecasts FX. Dollar moves enter through the 16% volatility, not the mean. The recent 3-year outperformance was partly dollar weakness, and I do not extrapolate it.

Confidence is medium. The candidates agree closely, but the regime call is weak, the index combines distinct European and Japanese cycles, and currency adds variance that none of the methods forecasts.

The governing IPS (config/ips.yaml) is ratified.

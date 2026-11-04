# CMA — us_value

**Expected return:** 9.58% (3y, nominal, arithmetic)  
**Volatility:** 14.84%  
**Confidence:** medium  
**Selection:** custom_blend — bl_equilibrium 15%, historical_erp 20%, implied_erp_cape 25%, inverse_gordon 30%, regime_adjusted 10%  
**Candidate range:** 8.00% to 12.51% (moderate); -0.48pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 11.99 | 0.50 | risk_free_pct +4.03, excess_return_pct +7.96, months +441.00 | +7.96% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 12.51 | 0.40 | risk_free_pct +4.03, regime_excess_return_pct +8.59, unconditional_excess_return_pct +8.15, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged +8.59% a year (all months +8.15%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.00 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +3.97, market_weight_pct +5.04, risk_aversion +2.50 | Equilibrium excess return +3.97% at a 5.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 9.00 | 0.42 | dividend_yield_pct +1.78, net_buyback_yield_pct +1.72, real_growth_pct +2.10, inflation_pct +2.30, valuation_change_pct +0.00, variance_addback_pct +1.10 | 1.78% dividends +1.72% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.10% variance add-back (net payout from WRDS 2025-12, rolled forward by IWD's price change; no long valuation history, drift 0). |
| `implied_erp_cape` | 8.11 | 0.35 | earnings_yield_pct +4.71, inflation_pct +2.30, variance_addback_pct +1.10 | 4.71% real earnings yield (IWD trailing earnings yield) + 2.3% expected inflation + 1.10% variance add-back. |
| `survey_consensus` | – | – | – | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | – | – | – | unavailable: not applicable to equity |
| `auto_blend` | 10.06 | 0.42 | weight:historical_erp +0.24, weight:regime_adjusted +0.19, weight:bl_equilibrium +0.19, weight:inverse_gordon +0.20, weight:implied_erp_cape +0.17 | Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%. |

## Judgment

**Regime logic.** Stage 1 calls this an expansion, but a stall-speed one with sticky inflation, restrictive real rates and a 20-30% recession probability, at only 0.36 confidence. That is closer to late-cycle than to a clean expansion, and Exhibit 4 tilts late-cycle toward valuation methods and away from a default blend. The regime_adjusted candidate (12.51%) depends entirely on the expansion label. Its premium (+8.59%) is barely above the unconditional +8.15%, so the label adds little, and if the borderline late-cycle reading is right it overstates. I therefore give it only 10%. Value stocks are cyclical: financials, energy and industrials are heavily represented. A stall that turns into a downturn would hit earnings and the payout base, which argues for anchoring on cash-flow methods rather than on backward-looking premia.

**Valuation context.** US Value is not at the extreme valuation of US Large Cap. The IWD trailing earnings yield of 4.71% (P/E near 21) and a net payout yield of about 3.5% are fair to moderately full, not stretched. Even so, the asset has returned 19.9% a year over three years and 23.7% over the last year, far above its 10% long-run average, so starting valuations have risen. The Gordon candidate assumes zero valuation drift because no long valuation history exists. Its payout yield was rolled forward by IWD's price change, so it already reflects the run-up, which makes it the most current cash-flow anchor. The CAPE-style candidate uses trailing rather than cyclically adjusted earnings, so it may be flattered if value-sector earnings are near a cyclical peak. Together these two methods get 55% of the weight. The historical ERP (11.99%) rests on a 1990-2026 sample of falling rates and is backward-looking at a point where valuations have expanded, so it gets 20%.

**Signal alignment.** The composite signal is mildly bullish at +0.20, but it is internally split. Momentum is strong: relative momentum +0.78 and 12-1 momentum +0.49. The 36-month mean-reversion signal is clearly negative at -0.58, reflecting the stretched three-year run. The macro alignment signals are all near zero, so the macro backdrop gives no directional confirmation. Over a 3-year horizon, mean reversion is more relevant than 12-month momentum, so I do not lean toward the historical and regime methods on the strength of momentum. The signals do argue against going to the bottom of the range, which is why BL (8.00%) gets only 15% and the final estimate sits modestly above the valuation cluster.

**Rationale.** Custom blend: Gordon 30%, CAPE/earnings yield 25%, historical ERP 20%, BL equilibrium 15%, regime-adjusted 10%. Result 9.58%, inside the [8.00, 12.51] range and about 0.5pp below the 10.06% auto-blend. The tilt toward cash-flow methods reflects three things: a borderline late-cycle regime held at low confidence, a strong three-year run that has raised starting valuations, and the cyclicality of value earnings. The backward-looking methods keep meaningful weight because valuations are not extreme, and because a 3-year horizon is short for mean reversion to play out. BL is down-weighted because its weights are ETF-size proxies rather than market caps. The implied excess return is about 5.5pp at 14.84% volatility, a Sharpe ratio near 0.37, which is plausible next to the 0.54 realised since 1990 given richer starting valuations. Confidence is medium: dispersion is moderate and the cash-flow methods agree at 8-9%, but the regime call is weak. The governing IPS (config/ips.yaml) is still a draft, so this estimate should be revisited when it is finalised.

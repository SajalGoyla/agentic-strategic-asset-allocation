# CMA — commodities

**Expected return:** 5.50% (3y, nominal, arithmetic)  
**Volatility:** 19.10%  
**Confidence:** low  
**Selection:** custom_blend — bl_equilibrium 35%, historical_erp 30%, regime_adjusted 35%  
**Candidate range:** 4.24% to 6.54% (tight); -0.13pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 6.54 | 0.50 | risk_free_pct +4.03, excess_return_pct +2.51, months +441.00 | +2.51% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 4.24 | 0.40 | risk_free_pct +4.03, regime_excess_return_pct -0.43, unconditional_excess_return_pct +2.12, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged -0.43% a year (all months +2.12%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.87 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +1.84, market_weight_pct +0.11, risk_aversion +2.50 | Equilibrium excess return +1.84% at a 0.1% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to real_assets |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to real_assets |
| `survey_consensus` | – | – | – | unavailable: not applicable to real_assets |
| `yield_building_block` | – | – | – | unavailable: not applicable to real_assets |
| `auto_blend` | 5.63 | 0.44 | weight:historical_erp +0.38, weight:regime_adjusted +0.31, weight:bl_equilibrium +0.31 | Confidence-weighted average of 3 methods: historical_erp 38%, regime_adjusted 31%, bl_equilibrium 31%. |

## Judgment

**Regime logic.** Stage 1 calls a stall-speed expansion with sticky inflation and restrictive real rates, bordering on late-cycle, but only at 0.36 confidence. Exhibit 4 tilts late-cycle environments toward regime-adjusted methods. For commodities that tilt matters because the regime-adjusted candidate is the only one that conditions on the cycle. It records that commodity excess returns in the three years after past expansion months were slightly negative (-0.43%/yr). That is consistent with commodities often peaking late in an expansion and then giving back gains as growth slows. The recession probability of 20-30% reinforces this downside skew. However, the label is low-confidence and the stage-1 inflation score is negative, which describes sticky rather than accelerating inflation, so the classic late-cycle inflation tailwind for commodities is muted. I therefore raise regime_adjusted modestly above its confidence-implied 31% weight, to 35%, rather than leaning on it heavily.

**Valuation context.** Commodities have no cash flow, so the Gordon, CAPE and yield methods do not apply and there is no direct valuation anchor. The nearest proxy is price extension. A +48% one-year return and a 3-year annualised return of about 14%, against roughly 3.5% since 1990, put the complex well above its long-run trend; the mean-reversion signal (-0.42) reflects this. Without a cash-flow anchor this cannot be turned into a valuation-change term. It does argue against weighting the backward-looking historical premium above its stated confidence. The since-1990 sample also mixes long contango and roll-drag periods with supercycle booms, so its 2.5% excess is a fragile average. The 4.03% T-bill collateral yield is a real and fairly mechanical part of the total return over a 3-year horizon, and all three candidates share it.

**Signal alignment.** The signals split by horizon. Trend (+0.56), 12-1 momentum (+0.67) and top-rank relative momentum (+1.00) are strongly bullish, and they drive the +0.34 composite. Time-series momentum in commodities is well documented but decays within months, so it says little about a 3-year arithmetic mean. The 36-month mean-reversion signal is the one aligned with the forecast horizon, and it points the other way. The macro alignment signals are all near zero, so macro adds no conviction in either direction. On balance the signals do not justify moving toward the top of the range. Positive near-term momentum is a reason not to adopt the bearish regime candidate outright, and the stretched 3-year run is a reason not to adopt the historical premium outright. A centre-of-range estimate hedges both.

**Rationale.** I chose a custom blend of 30% historical_erp, 35% regime_adjusted and 35% bl_equilibrium, which gives 5.50%. That is about 1.5pp of excess return over the 4.03% T-bill, an implied Sharpe of roughly 0.08 at 19.1% volatility. Dispersion is tight (2.3pp), so the choice moves the estimate only about 0.13pp below the 5.63% auto-blend. The tilt is deliberate. The historical candidate leans on a 1990-2026 average whose excess return is fragile for a no-cash-flow asset after a large run-up. The low-confidence, borderline-late-cycle regime evidence points to below-average commodity returns over the next three years. Black-Litterman is a neutral CAPM anchor; at a 0.1% market weight its premium comes almost entirely from covariance with the equity-heavy portfolio, which is reasonable but uninformative. All candidates for commodities are weaker than for cash-flow assets, so confidence is kept low. Governing policy is config/ips.yaml, which is still a draft; this estimate should be revisited once the IPS is finalised.

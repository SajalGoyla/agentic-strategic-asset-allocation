# CMA — cash

**Expected return:** 3.82% (3y, nominal, arithmetic)  
**Volatility:** 0.62%  
**Confidence:** medium_high  
**Selection:** custom_blend — survey_consensus 20%, yield_building_block 80%  
**Candidate range:** 3.00% to 4.03% (tight); +0.04pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 3.93 | 0.30 | risk_free_pct +4.03, excess_return_pct -0.10, months +441.00 | -0.10% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 3.92 | 0.25 | risk_free_pct +4.03, regime_excess_return_pct -0.11, unconditional_excess_return_pct -0.10, regime_months +180.00, credibility_weight +0.75 | After the 180 past months labelled expansion, excess returns over the next 3 years averaged -0.11% a year (all months -0.10%); credibility weight 0.75, plus 4.03% T-bill. |
| `bl_equilibrium` | 4.03 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +0.00, market_weight_pct +2.81, risk_aversion +2.50 | Equilibrium excess return +0.00% at a 2.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to cash |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to cash |
| `survey_consensus` | 3.00 | 0.50 | survey_pct +3.00, variance_addback_pct +0.00 | SPF median BILL10 3.00% a year over 10 years + 0.00% variance add-back. |
| `yield_building_block` | 4.03 | 0.80 | yield_pct +4.03, credit_loss_pct -0.00, variance_addback_pct +0.00 | 4.03% starting yield - 0.00% expected credit loss + 0.00% variance add-back (mean of DTB3). |
| `auto_blend` | 3.78 | 0.53 | weight:historical_erp +0.13, weight:regime_adjusted +0.11, weight:bl_equilibrium +0.18, weight:survey_consensus +0.22, weight:yield_building_block +0.36 | Confidence-weighted average of 5 methods: historical_erp 13%, regime_adjusted 11%, bl_equilibrium 18%, survey_consensus 22%, yield_building_block 36%. |

## Judgment

**Regime logic.** The regime read is a stall-speed expansion with sticky inflation and restrictive real rates, bordering on late-cycle, and the classification confidence is low (0.36). For cash the regime matters only through the policy-rate path over the next 3 years, since cash has no risk premium to tilt. Restrictive policy (monetary_policy -0.22) and a 20-30% recession probability point to some easing from today's 4.03% bill yield within the horizon. Sticky inflation (-0.27) argues the easing will be gradual and partial rather than a fast return to a 3% neutral rate. The regime_adjusted candidate adds nothing distinct: its -0.11% regime excess return is just the T-bill yield with noise. A modest downward tilt from the starting yield is warranted, not a large one.

**Valuation context.** Valuation for cash is the starting yield. At 4.03%, DTB3 is high against its own post-1990 history (yield_level +0.57), and that is the dominant determinant of cash return over a short horizon. The 3-year trailing return of 4.45% reflects the peak of the hiking cycle and is already rolling down; the 1-year return is 3.66%. The SPF BILL10 median of 3.00% is a 10-year average. It embeds a long-run neutral rate below today's level, so it overstates the decline likely within 3 years. Even so, it is a usable anchor for where bills are expected to drift. Historical_erp, regime_adjusted and bl_equilibrium are all the current T-bill plus a near-zero excess. Weighting them would only double-count the starting yield under different labels.

**Signal alignment.** The composite +0.22 is mildly supportive, led by yield_level (+0.57) and by trend and momentum readings that mostly reflect the steady accrual of a high bill yield. Mean_reversion (-0.73) and regime_fit (-0.42) point the other way: the elevated recent returns are unlikely to persist as policy eases. That fits a final estimate set slightly below the starting yield rather than at it. Technical signals carry little information for a near-riskless asset whose return is set mechanically by the bill rate.

**Rationale.** For cash, yield_building_block (4.03%, confidence 0.80) is the strongest single candidate, because the bill rate largely determines the return. I depart from it only to reflect an expected roll-down of short rates over a 3-year horizon, given restrictive policy and a non-trivial recession probability. I do that by giving 20% weight to survey_consensus (3.00%), which captures the market-consensus drift toward a lower neutral rate. The weight is kept small because that survey covers 10 years and would overstate the decline within 3. The historical, regime and BL candidates are dropped as redundant restatements of the same 4.03% T-bill. The 1.03pp dispersion comes from the horizon mismatch between a spot yield and a 10-year survey, not from a data problem. Result: 0.8 x 4.03 + 0.2 x 3.00 = 3.82%, within [3.00, 4.03] and close to the 3.78% auto-blend, with a cleaner justification. Volatility is 0.62% per the covariance matrix. The governing IPS (config/ips.yaml) is still a draft, so this assumption should be revisited once the policy is finalised.

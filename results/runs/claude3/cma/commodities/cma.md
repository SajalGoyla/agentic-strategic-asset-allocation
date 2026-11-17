# CMA — commodities

**Expected return:** 5.61% (3y, nominal, arithmetic)  
**Volatility:** 19.10%  
**Confidence:** low  
**Selection:** custom_blend — bl_equilibrium 35%, historical_erp 30%, regime_adjusted 35%  
**Candidate range:** 4.56% to 6.54% (tight); -0.11pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 6.54 | 0.50 | risk_free_pct +4.03, excess_return_pct +2.51, months +441.00 | +2.51% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 4.56 | 0.40 | risk_free_pct +4.03, regime_excess_return_pct -0.49, unconditional_excess_return_pct +3.17, regime_months +155.00, credibility_weight +0.72 | After the 155 past months labelled expansion, excess returns over the next 3 years averaged -0.49% a year (all months +3.17%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.87 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +1.84, market_weight_pct +0.11, risk_aversion +2.50 | Equilibrium excess return +1.84% at a 0.1% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to real_assets |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to real_assets |
| `survey_consensus` | – | – | – | unavailable: not applicable to real_assets |
| `yield_building_block` | – | – | – | unavailable: not applicable to real_assets |
| `auto_blend` | 5.72 | 0.44 | weight:historical_erp +0.38, weight:regime_adjusted +0.31, weight:bl_equilibrium +0.31 | Confidence-weighted average of 3 methods: historical_erp 38%, regime_adjusted 31%, bl_equilibrium 31%. |

## Judgment

**Regime logic.** Stage 1 calls a fragile, late-cycle-adjacent expansion with sticky above-history inflation, but only at 0.35 confidence and with a 20-30% recession probability. For commodities that mix cuts both ways. Sticky inflation is the environment where this asset earns its place: it has the highest inflation sensitivity in the universe. But commodities, being largely an oil position, are also the asset hit hardest when a late-cycle expansion tips into demand destruction. The regime-adjusted candidate captures this. Excess returns over the three years after past expansion months averaged -0.49%, against +3.17% unconditionally, because forward windows from mature expansions often ran into the 2008 and 2014-15 commodity busts. With the regime tilting late-cycle, Exhibit 4 step 2 points toward the regime-adjusted method. I raise its weight from the blend's 31% to 35%, but not further, because the regime label itself is low-confidence.

**Valuation context.** Key consideration 5 applies directly: there is no yield and no earnings, so nothing makes commodities cheap or expensive. That is why inverse_gordon, implied_erp_cape and yield_building_block are correctly unavailable, and I do not try to substitute a pseudo-valuation for them. The closest substitutes are curve shape, inventories and marginal cost. None of these is in our inputs, so I cannot claim a backwardation or contango view. Key consideration 1 says the roll decides total return. Consideration 2 warns that spot appreciation overstates it. Both are respected because historical_erp is built from the fund's return series since 1990, which embeds the actual roll and collateral, not from the oil or copper spot series. Even that candidate is generous: its 2.51% excess return includes the 2000s supercycle, while the full-history fund Sharpe is only 0.07. A 48% one-year gain also leaves prices extended against their own history. With no anchor to revert to, I treat that as a reason to lean away from the most optimistic candidate, not as a valuation signal.

**Signal alignment.** The signals split along time horizons. Momentum (+0.67), trend (+0.56) and relative momentum (+1.00, top of the 18 assets) are strongly bullish. That is consistent with commodity trend persistence over months, but a 3-year horizon outlasts most of that persistence. The 36-month mean-reversion signal is -0.42, which matches the regime-adjusted method's weak forward excess return after extended runs. The macro alignment signals are all close to zero, inflation alignment included at +0.01. So the measured link to today's inflation score gives no independent support for a higher number. I do not let the +0.34 composite, which is dominated by short-horizon technicals, pull the estimate toward historical_erp. Nor do I override it to the floor, since trend strength argues against a sharp near-term reversal. No flow or positioning view is available (decision 26), and I claim none.

**Rationale.** Dispersion is tight at 1.98pp, so method choice moves the answer only modestly. Per the asset-class guidance for commodities, confidence stays low. I use a custom blend of 30% historical_erp, 35% regime_adjusted and 35% bl_equilibrium, giving 5.61%. That is slightly below the 5.72% auto-blend and well inside [4.56, 6.54]. I trim historical_erp from 38% to 30% for two reasons: its since-1990 premium is flattered by the 2000s supercycle, and the trailing 48% run plus late-cycle positioning make the long-run average a weaker guide now. I hold BL at 35%. Its 0.1% ETF-AUM weight is a thin proxy for the asset's true size, but its +1.84% excess (Sharpe about 0.10) matches the near-0.09 ex-ante Sharpe noted in key consideration 3. I lift regime_adjusted to 35% because it is the only candidate that conditions on the current cycle. The result is about 1.6pp over the 4.03% T-bill, an implied Sharpe near 0.08 at 19.1% volatility. Per key consideration 3, the allocation case for commodities should rest on inflation hedging and diversification, not on this return. Per consideration 4, the estimate is largely a crude-oil view with metals and agriculture attached. The governing IPS (config/ips.yaml) is ratified.

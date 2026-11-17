# CMA — gold

**Expected return:** 6.01% (3y, nominal, arithmetic)  
**Volatility:** 17.88%  
**Confidence:** low  
**Selection:** custom_blend — bl_equilibrium 60%, regime_adjusted 40%  
**Candidate range:** 5.39% to 8.90% (moderate); -1.20pp vs. the auto-blend  
**Regime:** expansion

## Candidates

| method | estimate % | confidence | components | rationale |
|---|---|---|---|---|
| `historical_erp` | 8.90 | 0.50 | risk_free_pct +4.03, excess_return_pct +4.87, months +441.00 | +4.87% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 6.93 | 0.40 | risk_free_pct +4.03, regime_excess_return_pct +1.48, unconditional_excess_return_pct +6.57, regime_months +155.00, credibility_weight +0.72 | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +1.48% a year (all months +6.57%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.39 | 0.40 | risk_free_pct +4.03, implied_excess_return_pct +1.36, market_weight_pct +9.19, risk_aversion +2.50 | Equilibrium excess return +1.36% at a 9.2% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | – | – | – | unavailable: not applicable to real_assets |
| `implied_erp_cape` | – | – | – | unavailable: not applicable to real_assets |
| `survey_consensus` | – | – | – | unavailable: not applicable to real_assets |
| `yield_building_block` | – | – | – | unavailable: not applicable to real_assets |
| `auto_blend` | 7.21 | 0.44 | weight:historical_erp +0.38, weight:regime_adjusted +0.31, weight:bl_equilibrium +0.31 | Confidence-weighted average of 3 methods: historical_erp 38%, regime_adjusted 31%, bl_equilibrium 31%. |

## Judgment

**Regime logic.** Stage 1 calls a fragile, late-cycle-adjacent expansion, and only at low confidence (0.35), with a 20-30% recession probability. Exhibit 4 tilts late-cycle judgment toward regime-adjusted and valuation-style methods and away from long-run history. Gold has no valuation method of its own, so the regime-adjusted candidate is the closest regime-aware input. It shows that gold's excess return over the three years after past expansion months averaged only +1.48%, against +6.57% unconditional. Gold earns its premium in stress and disinflationary-easing episodes rather than in expansions. Because the regime call is low-confidence and recession odds are non-trivial, I do not lean on the regime-adjusted candidate alone. The candidate's 0.72 credibility shrinkage toward the unconditional mean already embeds part of the hedge, so I give it 40% rather than a majority. Monetary policy (-0.22) and sticky inflation are cross-currents for gold: a high real opportunity cost works against it, while above-history inflation works for it. That ambiguity argues for an estimate near the low-to-middle of the range rather than an extreme.

**Valuation context.** Four candidates were discarded as structurally inapplicable. Gold has no dividend, earnings or coupon, so inverse_gordon and implied_erp_cape cannot speak to it. yield_building_block does not apply for the same reason, and there is no SPF series for gold, so survey_consensus is also out. The pipeline already marks all four unavailable, and I confirm that rather than seek a proxy. Gold's lens is the real 10-year yield (DFII10), inflation expectations (T5YIFR) and the dollar. With the T-bill at 4.03%, the nominal carry forgone by holding gold is high by post-2008 standards, and storage adds a small negative carry. Key consideration 5 anchors the estimate: gold's long-run real return is close to zero. A purchasing-power-preserving asset at 17.88% volatility earns roughly expected inflation plus about 1.6pp of variance add-back in arithmetic terms. That points to roughly 4-5% nominal arithmetic, which sits below the hard floor of 5.39%. The estimate is therefore pulled toward the bottom of the range. I allow a modest positive real return above zero only because of the structural, price-insensitive central-bank reserve buying (key consideration 3), which the pre-2010 history does not contain. The 3y annualised +30.5% run has stretched price relative to these anchors, which is a valuation-style headwind for the next three years.

**Signal alignment.** The composite signal is mildly bearish at -0.09. The macro alignment signals are all essentially zero, consistent with gold's weak, unstable links to the growth, inflation, policy and financial-conditions scores. The informative signals are technical. Mean reversion at -0.68 flags the exceptional 36-month run, and trend at -0.57 shows price has fallen below its 10-month average, consistent with the -23.85% drawdown within the last year. Momentum (+0.21) and relative momentum (+0.44) are positive but reflect the earlier surge rather than current direction. Regime_fit (-0.23) agrees with the regime-adjusted candidate that expansions are below-average periods for gold. On balance the signals confirm the decision to lean toward the lower candidates. They do not justify going all the way to the floor, because the positive momentum readings and central-bank demand are offsets.

**Rationale.** Final estimate: 6.01% nominal arithmetic, from 60% bl_equilibrium (5.39%) and 40% regime_adjusted (6.93%).

I gave historical_erp (8.90%) zero weight, despite its top confidence score in the auto-blend. Key consideration 1 says that for an asset with no cash flow this method measures a price trend, not a premium. Its 1990-2026 sample is dominated by the 2001-2011 and 2019-2026 bull markets, a period of secularly falling real yields that cannot repeat from today's starting point. Adding the 4.03% T-bill to that trend excess would imply a sustained real return of roughly 4-5% compound. Key consideration 5 treats that as a regime-change claim, not an asset-with-a-yield claim. The auto-blend (7.21%) inherits that bias through its 38% weight on the historical method, so I did not accept it.

bl_equilibrium is the anchor. Its low implied premium (+1.36%) reflects gold's near-zero correlation with the equity-heavy ETF market portfolio, which is the economically right answer for a diversifier. Key consideration 4 says gold's portfolio role is the hedge, not the return. Risk-based PC methods will still give gold weight that this modest return estimate does not, and that disagreement is expected and appropriate. The equilibrium caveat is that ETF AUM is a proxy for market size, which is one reason it does not get full weight.

regime_adjusted brings the current expansion context and is shrunk toward the unconditional mean; it lifts the estimate modestly.

The result, about 6.0% arithmetic or roughly 4.4% compound after the ~1.6pp variance add-back, implies a small positive real return. That is justified only by structural official-sector buying. It sits within [5.39, 8.90], as close to the zero-real-return anchor as the range allows while respecting that anchor. Confidence is low: gold has no cash-flow anchor, only three weak candidates survived, and the macro regime call itself is low-confidence.

Governing policy is config/ips.yaml, reported as ratified for this run.

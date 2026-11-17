# Gold — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 6.01%** over 3 years, nominal, against expected volatility of 17.88%. Judge confidence **low**, selection by **custom blend** (`bl_equilibrium` 60%, `regime_adjusted` 40%). The 4 available candidates span 5.39%–8.90% (3.51pp), described as **moderate** dispersion.

## 2. The asset class

**Gold** (real assets), tracked by `GLD` against LBMA Gold Price PM.

- **Macro sensitivity:** Growth (0), Rates (--), Inflation (+), Dollar (--)
- **Primary valuation lens:** no cash flow: real yields (`DFII10`), inflation expectations (`T5YIFR`) and the dollar (`DTWEXBGS`)
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls a fragile, late-cycle-adjacent expansion, and only at low confidence (0.35), with a 20-30% recession probability. Exhibit 4 tilts late-cycle judgment toward regime-adjusted and valuation-style methods and away from long-run history. Gold has no valuation method of its own, so the regime-adjusted candidate is the closest regime-aware input. It shows that gold's excess return over the three years after past expansion months averaged only +1.48%, against +6.57% unconditional. Gold earns its premium in stress and disinflationary-easing episodes rather than in expansions. Because the regime call is low-confidence and recession odds are non-trivial, I do not lean on the regime-adjusted candidate alone. The candidate's 0.72 credibility shrinkage toward the unconditional mean already embeds part of the hedge, so I give it 40% rather than a majority. Monetary policy (-0.22) and sticky inflation are cross-currents for gold: a high real opportunity cost works against it, while above-history inflation works for it. That ambiguity argues for an estimate near the low-to-middle of the range rather than an extreme.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 7.14% | 27.08% | 0.24 | 0.37 | -23.8% | -11.7% | 58% |
| 3y (36m) | 30.48% | 18.96% | 1.28 | 2.25 | -23.8% | -11.7% | 69% |
| 5y (60m) | 18.32% | 17.20% | 0.86 | 1.50 | -23.8% | -11.7% | 58% |
| 10y (120m) | 11.73% | 15.50% | 0.64 | 1.11 | -23.8% | -11.7% | 52% |
| since_1990 (441m) | 6.15% | 18.07% | 0.27 | 0.41 | -43.6% | -17.9% | 50% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| intl_sovereigns | +0.55 | us_small_cap | +0.02 |
| intl_corporates | +0.51 | commodities | +0.05 |
| intermediate_treasuries | +0.41 | us_growth | +0.12 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> Four candidates were discarded as structurally inapplicable. Gold has no dividend, earnings or coupon, so inverse_gordon and implied_erp_cape cannot speak to it. yield_building_block does not apply for the same reason, and there is no SPF series for gold, so survey_consensus is also out. The pipeline already marks all four unavailable, and I confirm that rather than seek a proxy. Gold's lens is the real 10-year yield (DFII10), inflation expectations (T5YIFR) and the dollar. With the T-bill at 4.03%, the nominal carry forgone by holding gold is high by post-2008 standards, and storage adds a small negative carry. Key consideration 5 anchors the estimate: gold's long-run real return is close to zero. A purchasing-power-preserving asset at 17.88% volatility earns roughly expected inflation plus about 1.6pp of variance add-back in arithmetic terms. That points to roughly 4-5% nominal arithmetic, which sits below the hard floor of 5.39%. The estimate is therefore pulled toward the bottom of the range. I allow a modest positive real return above zero only because of the structural, price-insensitive central-bank reserve buying (key consideration 3), which the pre-2010 history does not contain. The 3y annualised +30.5% run has stretched price relative to these anchors, which is a valuation-style headwind for the next three years.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.1704 | +0.210 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0629 | -0.567 | price against its 10-month moving average |
| mean_reversion | +0.8625 | -0.675 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.1704 | +0.444 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite signal is mildly bearish at -0.09. The macro alignment signals are all essentially zero, consistent with gold's weak, unstable links to the growth, inflation, policy and financial-conditions scores. The informative signals are technical. Mean reversion at -0.68 flags the exceptional 36-month run, and trend at -0.57 shows price has fallen below its 10-month average, consistent with the -23.85% drawdown within the last year. Momentum (+0.21) and relative momentum (+0.44) are positive but reflect the earlier surge rather than current direction. Regime_fit (-0.23) agrees with the regime-adjusted candidate that expansions are below-average periods for gold. On balance the signals confirm the decision to lean toward the lower candidates. They do not justify going all the way to the floor, because the positive momentum readings and central-bank demand are offsets.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | -0.0059 | -0.229 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.1356 | -0.007 | correlation with the growth score (-0.14) times its level today (+0.05) |
| inflation_alignment | +0.0412 | -0.011 | correlation with the inflation score (+0.04) times its level today (-0.27) |
| monetary_policy_alignment | +0.0155 | -0.003 | correlation with the monetary_policy score (+0.02) times its level today (-0.22) |
| financial_conditions_alignment | +0.0275 | +0.010 | correlation with the financial_conditions score (+0.03) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (17.88%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 8.90% | 0.50 | — | +4.87% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 6.93% | 0.40 | 40% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +1.48% a year (all months +6.57%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.39% | 0.40 | 60% | Equilibrium excess return +1.36% at a 9.2% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to real_assets |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to real_assets |
| `survey_consensus` | — | — | — | unavailable: not applicable to real_assets |
| `yield_building_block` | — | — | — | unavailable: not applicable to real_assets |
| `auto_blend` | 7.21% | 0.44 | — | Confidence-weighted average of 3 methods: historical_erp 38%, regime_adjusted 31%, bl_equilibrium 31%. |

## 10. The judgment

Selection: **custom blend** — `bl_equilibrium` 60%, `regime_adjusted` 40%. Final estimate 6.01%, inside the hard [5.39, 8.90] range Exhibit 4 requires.

> Final estimate: 6.01% nominal arithmetic, from 60% bl_equilibrium (5.39%) and 40% regime_adjusted (6.93%).

I gave historical_erp (8.90%) zero weight, despite its top confidence score in the auto-blend. Key consideration 1 says that for an asset with no cash flow this method measures a price trend, not a premium. Its 1990-2026 sample is dominated by the 2001-2011 and 2019-2026 bull markets, a period of secularly falling real yields that cannot repeat from today's starting point. Adding the 4.03% T-bill to that trend excess would imply a sustained real return of roughly 4-5% compound. Key consideration 5 treats that as a regime-change claim, not an asset-with-a-yield claim. The auto-blend (7.21%) inherits that bias through its 38% weight on the historical method, so I did not accept it.

bl_equilibrium is the anchor. Its low implied premium (+1.36%) reflects gold's near-zero correlation with the equity-heavy ETF market portfolio, which is the economically right answer for a diversifier. Key consideration 4 says gold's portfolio role is the hedge, not the return. Risk-based PC methods will still give gold weight that this modest return estimate does not, and that disagreement is expected and appropriate. The equilibrium caveat is that ETF AUM is a proxy for market size, which is one reason it does not get full weight.

regime_adjusted brings the current expansion context and is shrunk toward the unconditional mean; it lifts the estimate modestly.

The result, about 6.0% arithmetic or roughly 4.4% compound after the ~1.6pp variance add-back, implies a small positive real return. That is justified only by structural official-sector buying. It sits within [5.39, 8.90], as close to the zero-real-return anchor as the range allows while respecting that anchor. Confidence is low: gold has no cash-flow anchor, only three weak candidates survived, and the macro regime call itself is low-confidence.

Governing policy is config/ips.yaml, reported as ratified for this run.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 5.39% | the most pessimistic available candidate is `bl_equilibrium` at 5.39%, -0.62pp against the judged estimate. Equilibrium excess return +1.36% at a 9.2% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| **base** | 6.01% | The judge's estimate, 6.01%, by custom blend across 4 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 8.90% | the most optimistic available candidate is `historical_erp` at 8.90%, +2.89pp against the judged estimate. +4.87% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **There is no cash flow, so every discounted-cash-flow method is inapplicable.** No dividend, no earnings, no coupon. The inverse-Gordon and implied-ERP candidates cannot speak to this asset at all, and a historical-ERP method is measuring a price trend rather than a premium. Build the estimate from real rates, inflation expectations and the dollar, and say which candidates you discarded as structurally inapplicable.
2. **The real 10-year yield is the strongest single driver.** Gold is a zero-coupon real asset, so its price moves against the real opportunity cost of holding it. `DFII10` is in the `cma_series` for exactly that reason.
3. **Central banks have become a large, price-insensitive buyer.** Official-sector demand responds to reserve policy rather than to price, which supports the market in ways the pre-2010 history does not contain.
4. **Its portfolio role is the diversification, not the return.** Correlation with US large cap is roughly zero on our matrix (-0.02), which is why risk-based PC methods give it weight that return-based methods will not justify. Expect that disagreement and address it.
5. **Long-run real return is close to zero, and storage is a small negative carry.** Gold preserves purchasing power over very long periods rather than compounding it. A CMA that implies a sustained real return materially above zero is making a claim about a regime change, not about an asset with a yield.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `worldbank:Gold` (monthly_average_price): 1980-01-31 to 1986-04-30, 76 months
- `crsp:CEF(69251)` (bullion_fund): 1986-05-31 to 2000-08-31, 172 months
- `GC=F` (futures): 2000-09-30 to 2004-11-30, 51 months
- `GLD` (etf): 2004-12-31 to 2026-09-30, 262 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

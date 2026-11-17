# International Sovereign Bonds — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 4.13%** over 3 years, nominal, against expected volatility of 8.45%. Judge confidence **low**, selection by **custom blend** (`yield_building_block` 60%, `regime_adjusted` 20%, `bl_equilibrium` 20%). The 5 available candidates span 3.55%–5.32% (1.77pp), described as **tight** dispersion.

## 2. The asset class

**International Sovereign Bonds** (fixed income), tracked by `BWX` against Bloomberg Global Treasury ex-US Capped.

- **Macro sensitivity:** Growth (-), Rates (-), Inflation (-), Dollar (--)
- **Primary valuation lens:** local long yields (German, Japanese, UK, French, Canadian)
- **Return history from** 1986-10-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls a fragile, late-cycle-adjacent expansion at low confidence (0.35), with a 20-30% recession probability. Exhibit 4 tilts late-cycle judgments toward regime-adjusted and valuation-anchored methods and away from long-run averages. For this asset that means the starting-yield builder plus the regime-adjusted candidate. After past expansion months, unhedged ex-US sovereigns returned -0.84% a year in excess of T-bills over the next three years, consistent with a strong-dollar expansion pattern. Its credibility weight is a healthy 0.72 on 155 months, but the 0.25 confidence and the low-confidence regime call argue for only a minority weight (20%). In the recession branch, foreign duration would rally. The USD is a typical haven in a US-led slowdown, though, so the currency leg could offset local bond gains. Regime logic therefore does not justify moving far from the yield anchor in either direction.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | -5.73% | 6.35% | -1.47 | -1.47 | -6.7% | -4.5% | 50% |
| 3y (36m) | 2.01% | 9.33% | -0.21 | -0.29 | -7.9% | -4.8% | 58% |
| 5y (60m) | -4.22% | 10.83% | -0.70 | -0.86 | -26.7% | -7.0% | 48% |
| 10y (120m) | -1.74% | 8.97% | -0.42 | -0.53 | -32.2% | -7.0% | 53% |
| since_1990 (441m) | 3.72% | 8.60% | 0.15 | 0.22 | -32.2% | -7.0% | 58% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| intl_corporates | +0.92 | commodities | +0.01 |
| ig_corporates | +0.82 | cash | +0.10 |
| usd_em_debt | +0.75 | us_small_cap | +0.39 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| yield_level | +3.0704 | +0.449 | IRLTLT01DEM156N: starting yield against its own history: the dominant predictor of bond return |

The judge's valuation assessment:

> The valuation lens is local long yields. The five-market mean (Germany, Japan, UK, France, Canada) is 3.64%, and the yield_level signal (+0.45) says this is high against the index's own post-2014 history. That makes the carry starting point the best single predictor of the local-currency return over a 3-year horizon near duration. Key consideration 2 applies directly: the 1990-2026 history was earned through a secular fall in yields and a decade of zero or negative JGB and Bund yields. That pattern cannot repeat from here in the same form, so historical_erp (5.32%, built on a 1.29% average excess return) gets zero weight despite its 0.30 confidence. The local yield sits about 40bp below the 4.03% US T-bill, so the asset carries negative carry against cash before any currency move. Per consideration 4, this is the unhedged index. A hedged version would pick up the US-foreign short-rate differential as hedge carry and run at far lower volatility. I have not mixed hedged evidence into this estimate. The 0.36pp variance add-back in the yield builder uses the full 8.45% unhedged volatility, which is mostly currency.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | -0.0296 | -0.267 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0334 | -0.428 | price against its 10-month moving average |
| mean_reversion | +0.0722 | -0.106 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | -0.0296 | -0.778 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite signal is roughly neutral at +0.03, but it splits sharply by category. Valuation is supportive (yield_level +0.45). Technicals are clearly negative: trend -0.43, 12-1 momentum -0.27, and relative momentum -0.78, near the bottom of the 18 asset classes. The 1-year return of -5.73% and 5-year return of -4.22% are largely dollar-driven. The macro alignment signals are all near zero, confirming that local-rate and growth factors explain little of this asset's USD return. The negative technicals and the negative regime_fit (-0.06) argue against leaning on the higher BL or historical figures. The supportive yield signal argues against going to the regime-adjusted floor. Both point toward a final number modestly above the yield builder and below the auto-blend, so the estimate sits between the anchor and the blend.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | -0.0007 | -0.059 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0629 | -0.003 | correlation with the growth score (-0.06) times its level today (+0.05) |
| inflation_alignment | +0.2008 | -0.054 | correlation with the inflation score (+0.20) times its level today (-0.27) |
| monetary_policy_alignment | -0.0014 | +0.000 | correlation with the monetary_policy score (-0.00) times its level today (-0.22) |
| financial_conditions_alignment | +0.1530 | +0.054 | correlation with the financial_conditions score (+0.15) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (8.45%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 5.32% | 0.30 | — | +1.29% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 3.55% | 0.25 | 20% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged -0.84% a year (all months +0.46%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.11% | 0.40 | 20% | Equilibrium excess return +1.08% at a 0.1% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to fixed_income |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 4.00% | 0.48 | 60% | 3.64% starting yield - 0.00% expected credit loss + 0.36% variance add-back (mean of IRLTLT01DEM156N, IRLTLT01JPM156N, IRLTLT01GBM156N, IRLTLT01FRM156N, IRLTLT01CAM156N; local-currency yield on an unhedged USD holding). |
| `auto_blend` | 4.51% | 0.38 | — | Confidence-weighted average of 4 methods: historical_erp 21%, regime_adjusted 17%, bl_equilibrium 28%, yield_building_block 34%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 60%, `regime_adjusted` 20%, `bl_equilibrium` 20%. Final estimate 4.13%, inside the hard [3.55, 5.32] range Exhibit 4 requires.

> Selected a custom blend: 60% yield_building_block (4.00%), 20% regime_adjusted (3.55%), 20% bl_equilibrium (5.11%), and 0% historical_erp. The result is 4.13%, within the [3.55, 5.32] range and 38bp below the 4.51% auto-blend. The auto-blend gave 21% to historical_erp, which key consideration 2 rules out because the falling-yield, zero-rate history cannot repeat; I removed that weight entirely. The yield builder is the anchor per the fixed-income guidance. Per consideration 1, though, this is a currency position wearing a bond label: exchange rates supply most of the 8.45% volatility, and the yield builder does not forecast them. My explicit dollar assumption is a flat trade-weighted USD over the 3-year horizon (zero expected FX return). I neither assume uncovered interest parity, which would credit foreign currencies with appreciating by the roughly 40bp carry shortfall, nor extrapolate the recent dollar strength the momentum signals reflect. BL keeps a 20% weight because it is the only candidate that prices this asset's covariance with the broader portfolio. Its 0.08% market weight makes its +1.08% premium thinly grounded, so it does not get its full confidence share. Per consideration 3, the result is the weakest risk-adjusted profile in the universe. At 4.13% against a 4.03% T-bill and 8.45% volatility, the ex-ante Sharpe is about 0.01, below even the roughly 0.05 the auto-blend would imply. That near-zero compensation for currency risk should be stated plainly to portfolio construction. Per consideration 5, the currency leg overlaps intl_corporates, so the two line items diversify each other less than they appear to. Confidence is low: the dispersion is tight at 1.77pp, but the dominant risk driver, the dollar, is unforecast by every candidate. Governing policy is config/ips.yaml, reported as ratified for this run.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 3.55% | the most pessimistic available candidate is `regime_adjusted` at 3.55%, -0.58pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged -0.84% a year (all months +0.46%); credibility weight 0.72, plus 4.03% T-bill. |
| **base** | 4.13% | The judge's estimate, 4.13%, by custom blend across 5 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 5.32% | the most optimistic available candidate is `historical_erp` at 5.32%, +1.19pp against the judged estimate. +1.29% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **This is a currency position wearing a bond label.** Unhedged and USD-denominated, with low local-bond volatility, so exchange rates supply most of the variance. Judging it as a duration asset will produce the wrong answer; say explicitly what you assume the dollar does.
2. **The carry starting point is structurally lower than the US.** Japan and much of Europe spent a decade at or below zero yields, so the long history of this index was earned in conditions that cannot repeat from here. A historical-average method is badly placed on this asset.
3. **The weakest risk-adjusted profile in the universe.** On our inputs it has the lowest ex-ante Sharpe of all eighteen (about 0.05): low yield, meaningful currency volatility. Say so rather than let the number pass unremarked.
4. **Hedged versus unhedged is the biggest definitional choice on this asset,** and we hold the unhedged version. A hedged index would have a quite different return and far lower volatility; do not mix evidence from the two.
5. **It overlaps `intl_corporates` on the currency leg,** so holding both adds less diversification than two line items suggest.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `RPIBX` (active_fund): 1986-10-31 to 2007-10-31, 253 months
- `BWX` (etf): 2007-11-30 to 2026-09-30, 227 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

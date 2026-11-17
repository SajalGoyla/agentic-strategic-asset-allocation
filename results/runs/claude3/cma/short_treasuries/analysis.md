# Short-Term Treasuries — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 4.74%** over 3 years, nominal, against expected volatility of 1.69%. Judge confidence **medium_high**, selection by **custom blend** (`yield_building_block` 90%, `bl_equilibrium` 10%). The 5 available candidates span 4.03%–4.88% (0.85pp), described as **tight** dispersion.

## 2. The asset class

**Short-Term Treasuries** (fixed income), tracked by `SHY` against ICE US Treasury 1-3 Year.

- **Macro sensitivity:** Growth (-), Rates (-), Inflation (-), Dollar (0)
- **Primary valuation lens:** the yield level (`DGS1`, `DGS2`, `DGS3`); carry is almost the whole return
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> The regime is a fragile, late-cycle-adjacent expansion, and stage 1 classifies it at low confidence (0.35). Monetary policy scores -0.22 and recession probability is 20-30%, so the balance of risks for the front end is that short rates fall over the next three years. For a 1-3 year Treasury sleeve the exposure that matters is reinvestment risk, not price risk (consideration 5). If the Fed eases, coupons and maturities in years two and three roll into lower yields. The price gain from that easing arrives early and only partly offsets the lower carry. With duration near two years against a three-year horizon, the starting yield remains a good anchor, but the risk is skewed modestly to the downside of it. The regime_adjusted candidate (4.79) conditions on past expansion months. Those months sat mostly inside a secular decline in yields, and this regime label is uncertain, so I give it no separate weight beyond what the yield anchor already captures.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 1.46% | 1.12% | -1.98 | -1.82 | -0.5% | -0.5% | 83% |
| 3y (36m) | 3.92% | 1.61% | -0.34 | -0.43 | -0.6% | -0.6% | 81% |
| 5y (60m) | 1.73% | 2.08% | -1.05 | -1.16 | -5.2% | -1.4% | 63% |
| 10y (120m) | 1.62% | 1.64% | -0.51 | -0.62 | -5.4% | -1.4% | 62% |
| since_1990 (441m) | 3.63% | 1.77% | 0.53 | 0.86 | -5.4% | -1.4% | 73% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| intermediate_treasuries | +0.85 | commodities | -0.29 |
| long_treasuries | +0.69 | us_small_cap | +0.03 |
| intl_sovereigns | +0.66 | us_value | +0.05 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| yield_level | +4.8800 | +0.731 | DGS2: starting yield against its own history: the dominant predictor of bond return |

The judge's valuation assessment:

> Carry is almost the whole return (consideration 1). The mean of DGS1, DGS2 and DGS3 is 4.81%, which is 78bp above the 4.03% T-bill. The curve slopes up from bills to three years, so roll-down is positive rather than negative (consideration 4). The yield_level signal (+0.73) puts the 2-year yield high against its own history, which favours bond return through carry. The two backward-looking candidates rest on weaker inputs. historical_erp (4.88) embeds a 1990-2026 sample dominated by falling yields, which inflates past excess returns, so it gets zero weight. bl_equilibrium (4.03) assigns a zero premium because a 1.6% ETF market weight and the asset's hedging role in a CAPM equilibrium mechanically drive the implied excess return to nothing. That makes it structurally uninformative as a point forecast for a bond with a positive starting term spread. It is retained only at a 10% weight, as a proxy for the reinvestment haircut, not as a forecast in its own right.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.0200 | +0.039 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0010 | -0.377 | price against its 10-month moving average |
| mean_reversion | +0.1159 | -0.518 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.0200 | -0.333 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite is +0.17 and is carried almost entirely by the yield_level valuation signal, which is the dominant predictor for this asset and confirms anchoring on the starting yield. The technical signals are negative: trend -0.38, relative momentum -0.33 and mean reversion -0.52. On a ~2-year-duration sleeve these mostly reflect a recent rate path that has already been repriced, and over three years they have little power next to carry. The macro alignment signals are near zero, which is consistent with low duration. regime_fit is -0.24, meaning expansion months have historically been below-average for short Treasuries. Together with the easing tilt, that supports a small haircut to the yield anchor rather than an estimate above it. I therefore stay below yield_building_block and do not lean toward historical_erp.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | -0.0006 | -0.239 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.3062 | -0.016 | correlation with the growth score (-0.31) times its level today (+0.05) |
| inflation_alignment | +0.1863 | -0.050 | correlation with the inflation score (+0.19) times its level today (-0.27) |
| monetary_policy_alignment | -0.0717 | +0.016 | correlation with the monetary_policy score (-0.07) times its level today (-0.22) |
| financial_conditions_alignment | -0.0234 | -0.008 | correlation with the financial_conditions score (-0.02) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (1.69%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 4.88% | 0.30 | — | +0.85% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 4.79% | 0.25 | — | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +0.79% a year (all months +0.69%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 4.03% | 0.40 | 10% | Equilibrium excess return +0.00% at a 1.6% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to fixed_income |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 4.82% | 0.80 | 90% | 4.81% starting yield - 0.00% expected credit loss + 0.01% variance add-back (mean of DGS1, DGS2, DGS3). |
| `auto_blend` | 4.65% | 0.54 | — | Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 90%, `bl_equilibrium` 10%. Final estimate 4.74%, inside the hard [4.03, 4.88] range Exhibit 4 requires.

> Final estimate 4.74%, from a custom blend of 90% yield_building_block (4.82%) and 10% bl_equilibrium (4.03%), inside the 4.03-4.88% range. Dispersion is tight at 0.85pp. The confidence-weighted auto-blend (4.65%) gives 23% to a Black-Litterman figure whose zero premium is an artefact of CAPM hedging and tiny ETF weight, so I depart from it. For a bond with duration near the horizon, the starting yield is the strongest candidate, and I depart from it only by the ~8bp haircut to reflect reinvestment risk under an easing-tilted policy outlook. historical_erp and regime_adjusted get zero weight because their samples are biased by the secular yield decline. Downstream flags: (1) Implied Sharpe. At 4.74% and 1.69% volatility, the ex-ante Sharpe is about 0.42, still at or near the top of the universe (consideration 2). Return-optimised PC methods will crowd into this sleeve, and that is an arithmetic consequence of low volatility, not a high-conviction return view. (2) Cash substitute. This sleeve is a near-substitute for cash with high correlation (consideration 3). Large weights in both amount to one front-end position with little independent diversification. (3) Governance. The governing IPS (config/ips.yaml) is reported as ratified for this run.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 4.03% | the most pessimistic available candidate is `bl_equilibrium` at 4.03%, -0.71pp against the judged estimate. Equilibrium excess return +0.00% at a 1.6% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| **base** | 4.74% | The judge's estimate, 4.74%, by custom blend across 5 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 4.88% | the most optimistic available candidate is `historical_erp` at 4.88%, +0.14pp against the judged estimate. +0.85% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Carry is the return.** With duration near two years, price change is a small share of total return over a three-year horizon. The starting yield plus roll-down is close to the whole estimate, which makes this one of the most reliable CMAs in the universe.
2. **Watch the Sharpe ratio it implies.** On our inputs this asset has the highest ex-ante Sharpe of all eighteen - about 0.52 against 0.39 for the next best - because a small term premium divided by 1.7% volatility is a large ratio. That is arithmetically correct and it makes every return-optimised PC method crowd into it. Flag it in your rationale so the downstream agents are not surprised.
3. **It is a near-substitute for cash.** High correlation with `cash` and little independent diversification value. A portfolio holding large weights in both is holding one position.
4. **Roll-down matters when the curve slopes up.** A 3-year bond held for a year becomes a 2-year bond and is repriced at a lower yield, adding return beyond the coupon. An inverted curve reverses that, so the sign of the roll depends on the curve shape today.
5. **Reinvestment risk, not price risk, is the exposure.** Falling short rates hurt this sleeve over a 3-year horizon even though they raise its price today.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `crsp:mcti[b2ret]` (index): 1980-01-31 to 2002-07-31, 271 months
- `SHY` (etf): 2002-08-31 to 2026-09-30, 290 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

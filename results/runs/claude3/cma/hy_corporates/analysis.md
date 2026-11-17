# High-Yield Corporates — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 6.04%** over 3 years, nominal, against expected volatility of 8.44%. Judge confidence **medium**, selection by **custom blend** (`yield_building_block` 70%, `bl_equilibrium` 20%, `regime_adjusted` 10%). The 5 available candidates span 5.79%–7.76% (1.97pp), described as **tight** dispersion.

## 2. The asset class

**High-Yield Corporates** (fixed income), tracked by `HYG` against iBoxx USD Liquid High Yield.

- **Macro sensitivity:** Growth (++), Rates (-), Inflation (0), Dollar (0)
- **Primary valuation lens:** the yield level (`BAMLH0A0HYM2EY`) and the spread (`BAMLH0A0HYM2`)
- **Return history from** 1980-02-29 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls a fragile, late-cycle-adjacent expansion at low confidence (0.35), with a 20-30% recession probability. For high yield this matters more than for any other fixed-income sleeve (consideration 3). HY carries the strongest Growth sensitivity in the group and correlates 0.72 with US large cap, so a growth shock would hit it like an equity drawdown with a coupon attached. Late-cycle logic in Exhibit 4 tilts toward forward-looking and regime-aware methods and away from long-run historical averages. I therefore give no weight to historical_erp and a small weight to regime_adjusted. Its 3-year-forward expansion premium (+2.35% excess) sits below the unconditional +3.39%, which is consistent with spreads already being compressed when expansions are under way. With duration of about three to four years, the view here is a view on the credit cycle rather than on the Fed (consideration 4). The negative monetary-policy score therefore carries little information for this asset.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 0.89% | 3.74% | -0.73 | -0.81 | -2.7% | -2.7% | 58% |
| 3y (36m) | 7.76% | 4.80% | 0.68 | 1.19 | -2.7% | -2.7% | 72% |
| 5y (60m) | 3.17% | 7.76% | -0.04 | -0.05 | -15.2% | -7.0% | 62% |
| 10y (120m) | 4.16% | 7.36% | 0.27 | 0.37 | -15.2% | -10.0% | 65% |
| since_1990 (441m) | 6.30% | 8.36% | 0.45 | 0.67 | -30.2% | -11.5% | 70% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| usd_em_debt | +0.84 | cash | +0.04 |
| us_large_cap | +0.81 | gold | +0.24 |
| us_value | +0.81 | long_treasuries | +0.30 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> The primary lens is the yield level. The 8.16% ICE HY effective yield is the best single predictor of return over a 3-year horizon close to the sleeve's duration. Consideration 1 says the yield is not the expected return. The yield_building_block candidate already nets a 2.50pp expected credit loss, in line with the roughly 4% default rate and roughly 40% recovery (about 2.4pp) the asset file prescribes. I take that figure as given and do not subtract losses a second time, since the starting spread already prices default risk. Consideration 2 is about callability: yield-to-worst understates the asymmetry, because issuers refinance when spreads tighten and investors keep the downside. That argues against anything above the yield-based figure. The historical_erp candidate (7.76%) is excluded for a specific reason. It is backward-looking and was earned over a 1990-2026 period of secularly falling yields and spread compression that cannot repeat from today's starting point. Consideration 5 adds that the liquid index's cleaner default history flatters that number further.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.0368 | -0.080 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0119 | -0.341 | price against its 10-month moving average |
| mean_reversion | +0.2286 | -0.276 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.0368 | -0.111 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite signal is mildly bearish at -0.08. Technicals lean negative: trend -0.34, mean reversion -0.28 after a strong 3-year run of 7.76%, and weak relative momentum. The macro alignment signals are near zero, apart from a small positive from easy financial conditions. This confirms rather than contradicts a forecast anchored on the credit-loss-adjusted yield and leaning toward the lower half of the range. Easy financial conditions are what keep spreads tight today, and they are also what unwinds in a late-cycle turn. I used no flow or positioning information, because none is sourced in this pipeline.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0014 | +0.109 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0093 | -0.000 | correlation with the growth score (-0.01) times its level today (+0.05) |
| inflation_alignment | +0.1272 | -0.034 | correlation with the inflation score (+0.13) times its level today (-0.27) |
| monetary_policy_alignment | -0.0165 | +0.004 | correlation with the monetary_policy score (-0.02) times its level today (-0.22) |
| financial_conditions_alignment | +0.3011 | +0.106 | correlation with the financial_conditions score (+0.30) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (8.44%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 7.76% | 0.30 | — | +3.73% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 6.67% | 0.25 | 10% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +2.35% a year (all months +3.39%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.79% | 0.40 | 20% | Equilibrium excess return +1.76% at a 1.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to fixed_income |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 6.02% | 0.80 | 70% | 8.16% starting yield - 2.50% expected credit loss + 0.36% variance add-back (mean of BAMLH0A0HYM2EY). |
| `auto_blend` | 6.36% | 0.54 | — | Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 70%, `bl_equilibrium` 20%, `regime_adjusted` 10%. Final estimate 6.04%, inside the hard [5.79, 7.76] range Exhibit 4 requires.

> Custom blend: yield_building_block 70%, bl_equilibrium 20%, regime_adjusted 10%. This gives 6.04%, inside the [5.79, 7.76] range and slightly below the 6.36% auto-blend. The fixed-income guidance makes the yield building block the anchor, and the horizon (3 years) roughly matches HY duration. It already embeds the 2.5pp credit-loss haircut that consideration 1 calls the most common error to omit, so no further deduction is made. The auto-blend gives 17% to historical_erp, whose 7.76% reflects a secular yield decline and a survivor-clean liquid index. I removed it rather than trust its stated confidence. Black-Litterman's 5.79% is a modest downward cross-check: it rests on an ETF-AUM proxy weight of about 1%, but its CAPM logic is apt for an asset that behaves like equity in drawdowns. Regime_adjusted adds a small forward-looking expansion read. Leaving the estimate a few basis points above the pure yield figure, rather than shading it lower, reflects the tight dispersion (1.97pp) and the absence of evidence that defaults will exceed the long-run haircut. The left-skew and call asymmetry (consideration 2) and the 20-30% recession probability mean the risk around this point estimate lies to the downside. Confidence is medium: the yield anchor is strong, but regime confidence is low. The governing IPS (config/ips.yaml) is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 5.79% | the most pessimistic available candidate is `bl_equilibrium` at 5.79%, -0.25pp against the judged estimate. Equilibrium excess return +1.76% at a 1.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| **base** | 6.04% | The judge's estimate, 6.04%, by custom blend across 5 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 7.76% | the most optimistic available candidate is `historical_erp` at 7.76%, +1.72pp against the judged estimate. +3.73% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **The yield is not the expected return.** Subtract expected credit losses: the long-run default rate has averaged roughly 4% a year with recoveries near 40%, which is a haircut of around 2.4pp on the headline yield. A CMA that uses yield-to-worst untouched is systematically too high, and this is the single most common error on this asset.
2. **Yield-to-worst already understates the call problem.** High-yield bonds are callable, so issuers refinance when spreads tighten and investors keep the downside. The realised return distribution is left-skewed beyond what volatility shows.
3. **It behaves like equity when it matters.** Correlation of 0.72 with US large cap on our matrix. In a growth shock this sleeve is an equity position with a coupon, which is why the Growth sensitivity is the strongest in the fixed-income group.
4. **Short duration, so spread risk not rate risk.** Duration around three to four years means much less Treasury sensitivity than IG. A view on this asset should be a view on the credit cycle, not on the Fed.
5. **The index excludes the weakest part of the market.** Liquid high-yield indices skip the smallest and least traded issues, so index default experience understates the asset class's and the available history is cleaner than the opportunity set.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `VWEHX` (active_fund): 1980-02-29 to 2007-04-30, 327 months
- `HYG` (etf): 2007-05-31 to 2026-09-30, 233 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

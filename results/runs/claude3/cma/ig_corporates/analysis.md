# Investment-Grade Corporates — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 5.94%** over 3 years, nominal, against expected volatility of 7.14%. Judge confidence **medium_high**, selection by **custom blend** (`yield_building_block` 80%, `bl_equilibrium` 20%). The 5 available candidates span 5.01%–6.71% (1.70pp), described as **tight** dispersion.

## 2. The asset class

**Investment-Grade Corporates** (fixed income), tracked by `LQD` against iBoxx USD Liquid Investment Grade.

- **Macro sensitivity:** Growth (+), Rates (--), Inflation (-), Dollar (0)
- **Primary valuation lens:** the yield level (`BAA`) and the credit spread (`BAMLC0A0CM`)
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls a fragile, late-cycle-adjacent expansion with sticky inflation, at low confidence (0.35), and puts recession probability at 20-30%. For IG corporates this argues against the regime_adjusted candidate. Its 6.65% comes from the three years after past expansion months, and those forward windows sit inside a 1990-2026 sample of almost continuously falling yields. It also gives no weight to the late-cycle tail, where spreads widen. The regime-fit signal is only +0.06, so the expansion label adds little information for this asset. The tight-but-fragile backdrop does matter for the spread leg. Loose financial conditions (+0.35) point to spreads nearer the tight end of their range. A 20-30% recession probability over a 3-year horizon means a real chance of spread widening and mark-to-market losses on an asset with roughly 8-year duration. I therefore haircut modestly below the starting yield rather than above it, and give regime_adjusted zero weight.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | -4.03% | 5.11% | -1.50 | -1.47 | -6.0% | -3.4% | 67% |
| 3y (36m) | 4.65% | 7.82% | 0.06 | 0.09 | -6.0% | -3.4% | 64% |
| 5y (60m) | -1.27% | 9.79% | -0.47 | -0.61 | -21.9% | -6.7% | 53% |
| 10y (120m) | 1.70% | 8.33% | -0.05 | -0.06 | -23.3% | -6.7% | 57% |
| since_1990 (441m) | 5.30% | 6.92% | 0.39 | 0.59 | -23.3% | -10.7% | 64% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| usd_em_debt | +0.87 | commodities | +0.03 |
| intl_corporates | +0.83 | cash | +0.07 |
| intl_sovereigns | +0.82 | gold | +0.39 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| yield_level | +6.4700 | +0.463 | BAA: starting yield against its own history: the dominant predictor of bond return |

The judge's valuation assessment:

> Key consideration 1 says to decompose the estimate. Most of the ~6.0% starting yield (BAMLC0A0CMEY) is the Treasury leg; the credit spread is a minority of it. The yield_level signal (+0.46 on BAA) says the all-in yield is attractive against its own history, but that comes mainly from where Treasury yields are, not from wide spreads. The view expressed here is about the spread leg. Consideration 4 applies: spreads mean-revert, and with financial conditions loose the starting spread is not where the forward return is. Upside from further tightening is capped, while widening risk stays intact. Consideration 2 also applies. The 0.10pp expected credit loss in yield_building_block is appropriately small for IG, and the spread already prices default risk, so I do not subtract any further loss. Doing so would count it twice. The haircut comes instead from horizon mismatch and spread asymmetry: a 3-year horizon is well short of ~8-year duration, so the yield is a good but imperfect predictor. Consideration 3 also applies. BBB issuance is now roughly half the index, so the historical excess return of +2.68% was earned on a higher-quality index during secular yield decline. That flatters historical_erp (6.71%) and I give it zero weight.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | -0.0060 | -0.321 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0401 | -0.647 | price against its 10-month moving average |
| mean_reversion | +0.1453 | -0.070 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | -0.0060 | -0.667 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite is close to neutral (+0.04), but its parts disagree. Valuation is clearly positive (yield level +0.46). The technicals are clearly negative: trend -0.65, relative momentum -0.67, 12-1 momentum -0.32. They are the mirror image of the same fact. The 1-year return of -4.03% is what pushed the starting yield up, so poor recent price action and a higher forward yield are one event seen twice. For bonds over a multi-year horizon the starting yield is the dominant predictor, and price momentum has little forward value. I therefore do not cut the estimate further to chase the technicals. The macro alignment signals are all within ±0.06 and do not move the view. Overall the signals neither confirm a bullish departure above the yield nor justify a large cut; they support staying close to yield_building_block with a mild downward hedge.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0006 | +0.059 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0459 | -0.002 | correlation with the growth score (-0.05) times its level today (+0.05) |
| inflation_alignment | +0.1842 | -0.050 | correlation with the inflation score (+0.18) times its level today (-0.27) |
| monetary_policy_alignment | -0.0056 | +0.001 | correlation with the monetary_policy score (-0.01) times its level today (-0.22) |
| financial_conditions_alignment | +0.1766 | +0.062 | correlation with the financial_conditions score (+0.18) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (7.14%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 6.71% | 0.30 | — | +2.68% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 6.65% | 0.25 | — | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +2.58% a year (all months +2.74%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.01% | 0.40 | 20% | Equilibrium excess return +0.98% at a 1.9% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to fixed_income |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 6.17% | 0.80 | 80% | 6.02% starting yield - 0.10% expected credit loss + 0.25% variance add-back (mean of BAMLC0A0CMEY). |
| `auto_blend` | 6.07% | 0.54 | — | Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 80%, `bl_equilibrium` 20%. Final estimate 5.94%, inside the hard [5.01, 6.71] range Exhibit 4 requires.

> For IG corporates at a horizon near duration, yield_building_block (6.17%: 6.02% yield, minus 0.10% credit loss, plus 0.25% variance add-back) is the strongest single candidate. It gets 80% of the weight, more than the 46% the auto-blend gives it. The remaining 20% goes to bl_equilibrium (5.01%). It is a cross-check that does not depend on the falling-yield history. It also expresses the departure from the yield-based figure, which is deliberate and has three reasons. First, spreads are likely near the tight end, so the outcome is asymmetric (consideration 4). Second, a 3-year horizon against ~8-year duration leaves meaningful mark-to-market exposure. Third, recession probability of 20-30% raises the chance of spread widening. historical_erp and regime_adjusted get zero weight. Both rest on a 1990-2026 sample of secular yield decline and on a higher-quality index than today's BBB-heavy one (consideration 3), so both overstate the forward return. The result is 0.8×6.17 + 0.2×5.01 = 5.94%, within the 5.01-6.71% range and about 0.2pp below the starting-yield figure. Dispersion is tight (1.70pp), so the choice moves the estimate only slightly. For portfolio construction, consideration 5 matters: correlation with US large cap is 0.58 and rises in stress, so this 5.94% should not be read as a Treasury-like equity hedge. The governing IPS (config/ips.yaml) is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 5.01% | the most pessimistic available candidate is `bl_equilibrium` at 5.01%, -0.93pp against the judged estimate. Equilibrium excess return +0.98% at a 1.9% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| **base** | 5.94% | The judge's estimate, 5.94%, by custom blend across 5 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 6.71% | the most optimistic available candidate is `historical_erp` at 6.71%, +0.77pp against the judged estimate. +2.68% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Mostly a duration position with a credit kicker.** Duration around eight years, so Treasury yield moves drive more of the return than spread moves do. Decompose the estimate into the Treasury leg and the spread leg, and say which one your view is actually about.
2. **Expected return is the yield minus expected losses, and for IG those losses are small.** Investment-grade default rates are low enough that the spread is mostly compensation for illiquidity and mark-to-market risk rather than for credit loss. That makes the yield a better starting point here than it is for high yield.
3. **The index's credit quality has drifted down.** BBB-rated issuance has grown to roughly half of the investment-grade market, so today's index is lower quality than the one the long history was earned on. A historical-spread average therefore flatters it.
4. **Spreads are mean-reverting, which makes the starting point asymmetric.** Tight spreads cap the upside and leave the downside intact; wide spreads are where the forward return is. The credit-spread signal in `config/signals.yaml` scores wide as bullish for this reason.
5. **The diversification fails when it is needed.** Correlation with equities rises in stress - 0.58 with US large cap on our matrix, and higher in the worst months - so this is not a Treasury substitute for the purpose of hedging an equity drawdown.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `crsp_fund:ACCBX` (active_fund): 1980-01-31 to 2002-07-31, 271 months
- `LQD` (etf): 2002-08-31 to 2026-09-30, 290 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

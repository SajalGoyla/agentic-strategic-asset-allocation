# Intermediate Treasuries — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 5.26%** over 3 years, nominal, against expected volatility of 6.46%. Judge confidence **medium_high**, selection by **custom blend** (`yield_building_block` 85%, `survey_consensus` 15%). The 6 available candidates span 4.13%–6.54% (2.42pp), described as **tight** dispersion.

## 2. The asset class

**Intermediate Treasuries** (fixed income), tracked by `IEF` against ICE US Treasury 7-10 Year.

- **Macro sensitivity:** Growth (-), Rates (--), Inflation (--), Dollar (0)
- **Primary valuation lens:** the yield level (`DGS7`, `DGS10`); starting yield is the dominant predictor
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls a fragile, late-cycle-adjacent expansion with sticky above-history inflation, at low confidence (0.35) and a 20-30% recession probability. For a 7-10 year Treasury, that state cuts both ways. A recession would pull yields down and lift price through roughly 7.5 years of duration. Sticky inflation and a still-restrictive policy score (-0.22) could push yields higher, and a nominal bond has no protection against that. Exhibit 4's late-cycle tilt toward regime-adjusted methods does not carry over here. The regime_adjusted candidate (6.54%) is built from post-1990 expansion months that sit inside a secular fall in yields, and the regime label is low-confidence. Because the regime read is ambiguous, I lean on the starting yield, which does not depend on the regime call. The inflation asymmetry is the reason for trimming slightly below it rather than adding to it.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | -3.75% | 5.30% | -1.39 | -1.47 | -6.7% | -3.4% | 42% |
| 3y (36m) | 2.89% | 6.66% | -0.20 | -0.26 | -6.7% | -3.4% | 61% |
| 5y (60m) | -2.06% | 7.65% | -0.73 | -0.88 | -19.4% | -4.7% | 48% |
| 10y (120m) | 0.09% | 6.63% | -0.32 | -0.42 | -23.2% | -4.7% | 52% |
| since_1990 (441m) | 5.03% | 6.40% | 0.37 | 0.58 | -23.2% | -5.0% | 59% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| long_treasuries | +0.93 | commodities | -0.31 |
| short_treasuries | +0.85 | us_value | +0.10 |
| ig_corporates | +0.78 | us_small_cap | +0.10 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| yield_level | +5.2900 | +0.797 | DGS10: starting yield against its own history: the dominant predictor of bond return |

The judge's valuation assessment:

> Valuation is the dominant lens for this asset, and it is unambiguous. The 7- and 10-year yields average 5.24%, which the yield_level signal scores +0.80, high against their own history. Over a horizon near duration, the entry yield explains most of the realised return, so yield_building_block (5.45%, including a 0.21pp variance add-back and no credit loss on Treasuries) is the anchor. The 3-year horizon is shorter than the ~7.5-year duration, so the yield path matters as well as the level: a 100bp rise over the horizon would cost about 7% of price, spread over three years. The SPF BOND10 consensus (4.00% compound) sits below today's yield. It is a 10-year average expectation and may embed some reversion or lag in the survey, so I use it as a modest counterweight for path risk rather than as a primary estimate. The historical methods (6.41%, 6.54%) are excluded. They capture 1990-2026 capital gains from falling yields, which cannot repeat from today's starting point in the same way, and they would double-count income the yield already prices.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | -0.0033 | -0.276 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0404 | -0.672 | price against its 10-month moving average |
| mean_reversion | +0.0921 | +0.044 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | -0.0033 | -0.556 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite (+0.18) masks a split. Valuation is strongly bullish (yield_level +0.80). Technicals are bearish: trend -0.67, relative momentum -0.56, 12-1 momentum -0.28. These do not contradict each other. The weak trailing returns (1y -3.75%, 5y -2.06%) are the yield rise that produced today's attractive entry yield. Over a multi-year horizon, bond momentum is a much weaker predictor than the starting yield. Macro alignment signals are all near zero (|score| <= 0.04), so they neither confirm nor hedge the estimate. I treat the negative technicals as a reason to sit slightly below the pure yield anchor, not as grounds for a large cut.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | -0.0001 | -0.015 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0836 | -0.004 | correlation with the growth score (-0.08) times its level today (+0.05) |
| inflation_alignment | +0.1464 | -0.040 | correlation with the inflation score (+0.15) times its level today (-0.27) |
| monetary_policy_alignment | +0.0056 | -0.001 | correlation with the monetary_policy score (+0.01) times its level today (-0.22) |
| financial_conditions_alignment | -0.0170 | -0.006 | correlation with the financial_conditions score (-0.02) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (6.46%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 6.41% | 0.30 | — | +2.38% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 6.54% | 0.25 | — | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +2.58% a year (all months +2.35%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 4.13% | 0.40 | — | Equilibrium excess return +0.10% at a 2.5% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to fixed_income |
| `survey_consensus` | 4.21% | 0.50 | 15% | SPF median BOND10 4.00% a year over 10 years + 0.21% variance add-back. |
| `yield_building_block` | 5.45% | 0.80 | 85% | 5.24% starting yield - 0.00% expected credit loss + 0.21% variance add-back (mean of DGS7, DGS10). |
| `auto_blend` | 5.19% | 0.53 | — | Confidence-weighted average of 5 methods: historical_erp 13%, regime_adjusted 11%, bl_equilibrium 18%, survey_consensus 22%, yield_building_block 36%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 85%, `survey_consensus` 15%. Final estimate 5.26%, inside the hard [4.13, 6.54] range Exhibit 4 requires.

> Final estimate: 5.26%, from 85% yield_building_block and 15% survey_consensus. This sits inside the [4.13, 6.54] range and just above the 5.19% auto-blend. The skill's guidance and Key consideration 1 make the starting yield the most defensible fixed-income building block, so it carries most of the weight. The 0.15 survey weight is a deliberate, explained haircut of about 0.2pp for two risks. First, the asymmetric inflation risk (consideration 5): sticky inflation is the stage-1 base case, and the historical sample has only one real inflation shock. Second, path risk over a 3-year horizon shorter than duration (consideration 4). Three candidates are dropped. historical_erp and regime_adjusted are biased upward by the secular fall in yields. bl_equilibrium (4.13%) is a CAPM artifact: it gives near-zero premia to assets that hedged an equity-heavy ETF market and assumes the negative stock-bond correlation that broke in 2022 (consideration 2), so I do not rely on it. Volatility stays at the covariance figure of 6.46%. Per consideration 5, that should be read as a floor in an inflationary state, and per consideration 2, backtested drawdowns understate a joint rate-and-equity shock. The estimate is held close to the yield anchor because this sleeve is 30% of the IPS benchmark (consideration 3), so an error here would shift the tracking-error budget of every candidate portfolio. Governing policy is config/ips.yaml, whose status is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 4.13% | the most pessimistic available candidate is `bl_equilibrium` at 4.13%, -1.13pp against the judged estimate. Equilibrium excess return +0.10% at a 2.5% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| **base** | 5.26% | The judge's estimate, 5.26%, by custom blend across 6 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 6.54% | the most optimistic available candidate is `regime_adjusted` at 6.54%, +1.28pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged +2.58% a year (all months +2.35%); credibility weight 0.72, plus 4.03% T-bill. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Starting yield predicts the return.** Over a horizon close to the duration, the entry yield explains most of the realised return. This is the single most defensible building block in the fixed-income sleeve, and a CMA far from the starting yield needs a reason.
2. **The equity hedge is regime-dependent and it has failed.** The negative stock-bond correlation that makes this the classic diversifier held through the 1998-2020 period and broke in 2022, when both legs fell together. Our own CRO flags this: the 1993-onward panel is almost entirely a falling-yield bull market, so backtested drawdown understates a rate-and-inflation shock.
3. **It is 30% of the IPS benchmark.** An error here moves the tracking-error budget for every candidate portfolio, not just this sleeve's own weight.
4. **Duration around seven and a half years.** Enough price sensitivity that a 100bp yield move is worth roughly 7% of price, so the CMA is sensitive to the path assumed for yields and not only to their level.
5. **Inflation is the asymmetric risk.** A nominal bond has no protection against an inflation surprise, and the sample here contains only one real episode of that. Treat the historical volatility as a floor rather than a central estimate for an inflationary state.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `crsp:mcti[b7ret/b10ret]` (index): 1980-01-31 to 2002-07-31, 271 months
- `IEF` (etf): 2002-08-31 to 2026-09-30, 290 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

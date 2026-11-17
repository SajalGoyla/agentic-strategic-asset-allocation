# US Large Cap — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 7.47%** over 3 years, nominal, against expected volatility of 14.76%. Judge confidence **low**, selection by **custom blend** (`historical_erp` 10%, `regime_adjusted` 5%, `bl_equilibrium` 20%, `inverse_gordon` 20%, `implied_erp_cape` 20%, `survey_consensus` 25%). The 7 available candidates span 3.57%–12.83% (9.27pp), described as **wide** dispersion.

## 2. The asset class

**US Large Cap** (equity), tracked by `SPY` against S&P 500 (paper uses Bloomberg SPTR Index).

- **Macro sensitivity:** Growth (+), Rates (-), Inflation (-), Dollar (+)
- **Primary valuation lens:** CAPE and the implied ERP; `market/fund_snapshot` supplies the ETF P/E
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 labels the regime an expansion, but a fragile, late-cycle-adjacent one with sticky above-history inflation. Its confidence is low (0.35) and recession probability is 20-30%. Exhibit 4 tilts late-cycle environments toward valuation and regime-adjusted methods. Here the regime-adjusted candidate (12.83%) is conditioned on the 'expansion' label. That label is the least certain input in the regime view, and its credibility weight (0.72) was set without knowing the label is borderline late-cycle. The forward-looking 3-year excess after expansion months (+8.98%) is barely above the unconditional +8.34%, so the label adds little information while carrying the full 1990-2026 sample's multiple expansion. I therefore cut regime_adjusted to 5% rather than raising it. I also tilt toward the valuation methods (40% combined), which is the late-cycle half of the Exhibit 4 rule. Financial conditions (+0.35) are the only clearly supportive dimension. That supports keeping a meaningful equilibrium and survey anchor rather than going fully to the valuation floor. Negative monetary-policy and inflation scores hurt this long-duration, tech-heavy sleeve, which sells off on rising real yields (consideration 3).

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 15.71% | 13.19% | 0.89 | 2.11 | -5.8% | -4.9% | 67% |
| 3y (36m) | 22.76% | 12.43% | 1.37 | 2.86 | -7.6% | -5.6% | 69% |
| 5y (60m) | 13.70% | 15.67% | 0.67 | 1.06 | -23.9% | -9.2% | 63% |
| 10y (120m) | 15.23% | 15.33% | 0.85 | 1.34 | -23.9% | -12.5% | 70% |
| since_1990 (441m) | 10.79% | 14.69% | 0.59 | 0.88 | -50.8% | -16.5% | 65% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| us_growth | +0.95 | cash | -0.01 |
| us_value | +0.91 | short_treasuries | +0.10 |
| us_small_cap | +0.86 | gold | +0.14 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| cape | +40.2609 | -0.784 | Shiller CAPE, inverted: expensive is bearish for forward return |

The judge's valuation assessment:

> CAPE at 40.3 is extreme even against the post-1990 median of 26.4. The real earnings yield is only 2.48%. So valuations are stretched, and Exhibit 4 directs weight toward implied_erp_cape and inverse_gordon. The Gordon build uses net payout, 0.93% dividends plus 1.28% net buybacks, which addresses consideration 4. A dividend-only yield would understate the income return by over a percentage point, so no further adjustment is needed. Its low headline (3.57%) comes from the -4.14%/yr valuation-reversion term, which assumes CAPE returns to 26.4 over 10 years. Mean reversion is real but slow, and the horizon here is 3 years, so I do not let this candidate dominate. I cap it at 20% rather than its 21% blend share, and balance it with the CAPE earnings-yield method (5.87%), which takes no reversion. The historical ERP (12.67%) embeds a 1990-2026 period of rising multiples. That is the very valuation expansion the CAPE signal says cannot repeat from here, so it is cut to 10%. Concentration (consideration 2) matters here. With the top ten names at about a third of the index, the aggregate CAPE is driven by a few mega-cap growth firms. Index returns therefore hinge on whether their earnings justify the multiples, which raises the downside tail.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.1579 | +0.171 | 11-month return skipping the last 1, vs. its own history |
| trend | +0.0658 | +0.143 | price against its 10-month moving average |
| mean_reversion | +0.6443 | -0.598 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.1579 | +0.333 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite signal is -0.25, and the bearish weight is valuation-driven. CAPE scores -0.78 and the 36-month mean-reversion signal scores -0.60 after a 22.8% annualised 3-year run. Short-horizon technicals are mildly positive: momentum +0.17, trend +0.14 and relative momentum +0.33. Regime fit is +0.23. So trend has not yet turned, but forward-return indicators point below history. This confirms leaning below the 8.24% auto-blend and well below the historical methods. The positive momentum and financial-conditions readings argue against going to the valuation floor (3.57-5.87%). Dollar exposure (consideration 5) is treated as an earnings headwind, not a return sign: the index's return can hold up on safe-haven dollar rallies, so I make no separate adjustment. No fund-flow or positioning view is used, because this pipeline cannot source one.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0051 | +0.231 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0574 | -0.003 | correlation with the growth score (-0.06) times its level today (+0.05) |
| inflation_alignment | +0.1040 | -0.028 | correlation with the inflation score (+0.10) times its level today (-0.27) |
| monetary_policy_alignment | +0.0666 | -0.014 | correlation with the monetary_policy score (+0.07) times its level today (-0.22) |
| financial_conditions_alignment | +0.3357 | +0.119 | correlation with the financial_conditions score (+0.34) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (14.76%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 12.67% | 0.50 | 10% | +8.64% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 12.83% | 0.40 | 5% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +8.98% a year (all months +8.34%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.26% | 0.40 | 20% | Equilibrium excess return +4.23% at a 48.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 3.57% | 0.60 | 20% | 0.93% dividends +1.28% net buybacks + 2.1% real growth + 2.3% inflation -4.14% valuation change + 1.09% variance add-back (net payout from WRDS 2025-12, rolled forward by SPY's price change; CAPE 40.3 reverting to 26.4 over 10y). |
| `implied_erp_cape` | 5.87% | 0.50 | 20% | 2.48% real earnings yield (1/CAPE, CAPE 40.3) + 2.3% expected inflation + 1.09% variance add-back. |
| `survey_consensus` | 8.09% | 0.50 | 25% | SPF median STOCK10 7.00% a year over 10 years + 1.09% variance add-back. |
| `yield_building_block` | — | — | — | unavailable: not applicable to equity |
| `auto_blend` | 8.24% | 0.49 | — | Confidence-weighted average of 6 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 14%, inverse_gordon 21%, implied_erp_cape 17%, survey_consensus 17%. |

## 10. The judgment

Selection: **custom blend** — `historical_erp` 10%, `regime_adjusted` 5%, `bl_equilibrium` 20%, `inverse_gordon` 20%, `implied_erp_cape` 20%, `survey_consensus` 25%. Final estimate 7.47%, inside the hard [3.57, 12.83] range Exhibit 4 requires.

> I set a custom blend at 7.47%, 0.77pp below the auto-blend. The blend weights the survey consensus at 25% (SPF STOCK10, a fresh independent outside view) and Black-Litterman equilibrium at 20%. The two valuation methods get 20% each, and the backward-looking historical ERP and regime methods only 10% and 5%. The auto-blend weights candidates by stated confidence and takes no view on whether their assumptions hold now. The historical and regime methods assume the 1990-2026 multiple expansion persists, which is implausible from a CAPE of 40. The Gordon method assumes a full 10-year reversion that a 3-year horizon will capture only partly. The result sits inside the [3.57, 12.83] range. It implies an excess return of about 3.4% over the 4.03% T-bill and a Sharpe of about 0.23 at 14.76% volatility, modest and consistent with stretched valuations. The S&P 500 is 60% of the IPS benchmark, so this number drives every tracking-error figure (consideration 1). For that reason I keep the departure from the blend moderate and well justified rather than taking the valuation floor. Concentration in a few tech and AI mega-caps and sensitivity to real yields widen the outcome distribution, so confidence is low given 9.3pp of dispersion and a low-confidence regime call. Governing policy is config/ips.yaml, whose status is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 3.57% | the most pessimistic available candidate is `inverse_gordon` at 3.57%, -3.90pp against the judged estimate. 0.93% dividends +1.28% net buybacks + 2.1% real growth + 2.3% inflation -4.14% valuation change + 1.09% variance add-back (net payout from WRDS 2025-12, rolled forward by SPY's price change; CAPE 40.3 reverting to 26.4 over 10y). |
| **base** | 7.47% | The judge's estimate, 7.47%, by custom blend across 7 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 12.83% | the most optimistic available candidate is `regime_adjusted` at 12.83%, +5.36pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged +8.98% a year (all months +8.34%); credibility weight 0.72, plus 4.03% T-bill. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **The S&P 500 is the benchmark.** Most investors compare everything against it, and it is 60% of the IPS benchmark, so an estimate here moves every tracking-error number in the pipeline.
2. **Concentration risk.** The top ten constituents have grown to roughly a third of index weight, so the index is far less diversified than its 500 names suggest and its return is increasingly a few companies' return.
3. **Technology and AI exposure.** Sector composition is heavily tilted toward technology and growth, which is why this sleeve behaves like a long-duration asset and sells off on rising real yields.
4. **Buyback yield is a real CMA component.** Net buybacks have run roughly 1-3% a year, so total shareholder yield materially exceeds the dividend yield. A Gordon-style build that uses dividends alone understates the return (decision 23 uses net payout for this reason).
5. **Dollar strength cuts multinational earnings.** Around 40% of revenue is earned abroad, so a strong dollar is a headwind to earnings even though the index's own return tends to hold up when the dollar rises on safe-haven flows. Do not read the return sign as an earnings sign.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `french:F-F_Research_Data_Factors[Mkt-RF + RF]` (academic_index): 1980-01-31 to 1980-01-31, 1 months
- `VFINX` (index_fund): 1980-02-29 to 1993-01-31, 156 months
- `SPY` (etf): 1993-02-28 to 2026-09-30, 404 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

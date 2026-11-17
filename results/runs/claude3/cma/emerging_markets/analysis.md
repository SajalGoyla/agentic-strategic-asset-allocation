# Emerging Markets — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 9.44%** over 3 years, nominal, against expected volatility of 22.13%. Judge confidence **medium**, selection by **custom blend** (`historical_erp` 15%, `regime_adjusted` 25%, `bl_equilibrium` 25%, `inverse_gordon` 20%, `implied_erp_cape` 15%). The 6 available candidates span 7.57%–11.76% (4.19pp), described as **moderate** dispersion.

## 2. The asset class

**Emerging Markets** (equity), tracked by `EEM` against MSCI Emerging Markets.

- **Macro sensitivity:** Growth (+), Rates (-), Inflation (-), Dollar (--)
- **Primary valuation lens:** CAPE, which is the cheapest in the universe and has been for years
- **Return history from** 1989-07-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls the regime a fragile, late-cycle-adjacent expansion with sticky inflation, and holds that view at low confidence (0.35). Recession probability is 20-30%. Under Exhibit 4, late-cycle conditions tilt weight toward regime-adjusted and valuation methods, while a plain expansion tilts toward the blend. The regime-adjusted candidate (7.57%) is the only one that conditions on what followed past expansion months. For EM, those 3-year-forward excess returns averaged just 2.59%, against 6.00% unconditionally. EM is the most dollar- and liquidity-sensitive equity in the universe, and late-expansion phases have often ended in dollar strength and tighter global funding. I therefore raised regime_adjusted's weight to 25%, above its 21% auto-blend weight. Because the regime call itself is low-confidence, I did not let it dominate. The candidate is already credibility-shrunk at 0.72, so I set no weight beyond a quarter. Only the macro view applies here: no survey consensus exists for EM, and I import no carry or local-rate reasoning from usd_em_debt, which is a different asset.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 27.52% | 21.39% | 1.07 | 1.94 | -9.3% | -9.3% | 67% |
| 3y (36m) | 23.64% | 15.23% | 1.19 | 2.20 | -9.3% | -9.3% | 72% |
| 5y (60m) | 8.32% | 17.68% | 0.33 | 0.53 | -31.3% | -11.5% | 57% |
| 10y (120m) | 8.30% | 17.22% | 0.41 | 0.63 | -36.5% | -15.8% | 57% |
| since_1990 (441m) | 8.04% | 21.76% | 0.34 | 0.50 | -60.4% | -26.1% | 56% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| intl_developed | +0.80 | cash | +0.04 |
| usd_em_debt | +0.74 | short_treasuries | +0.21 |
| intl_corporates | +0.72 | intermediate_treasuries | +0.24 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> EM is the cheapest equity in the universe on earnings yield (7.01% trailing on EEM). Taken at face value, that drives the top candidate, implied_erp_cape, to 11.76%. I treat that figure as overstated, for the reasons in Key consideration 4. A sustained discount reflects governance, state ownership, capital-controls and concentration risk, so it is largely compensation rather than mispricing. In addition, EM firms persistently dilute shareholders through net issuance, so headline earnings yield translates poorly into per-share returns. The same dilution means the Gordon candidate's net buyback term of 0.00% (no buyback data for international) is generous, since true net issuance is negative. I see no specific catalyst to close the discount within 3 years: the weight is roughly 60% China, Taiwan and Korea, which makes this a China-policy and semiconductor-cycle bet. Accordingly I cut implied_erp_cape to 15% from 18%, and held inverse_gordon (9.04%) at 20% as a cash-flow anchor. That only modestly lowers the estimate, which is consistent with the paper's judge marking EM down just -0.2% rather than rejecting the cheapness case.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.2700 | +0.434 | 11-month return skipping the last 1, vs. its own history |
| trend | +0.0694 | +0.178 | price against its 10-month moving average |
| mean_reversion | +0.6776 | -0.642 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.2700 | +0.889 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite is mildly positive at +0.21, but the components conflict. Relative momentum (+0.89) and 12-1 momentum (+0.43) are strong after a 27.5% one-year and 23.6% three-year annualised run, much of it semiconductor-driven in Taiwan and Korea. The 36-month mean-reversion signal (-0.64) flags that run as stretched over a 3-year horizon, which is the relevant one here. The measured macro alignments are near zero. Financial conditions (+0.10) are the only meaningful support, which fits EM's liquidity sensitivity, and that support would reverse if the dollar strengthens. On net, the signals do not justify leaning toward the historical or CAPE end of the range. Momentum argues against a deep cut, so I hedge toward the middle of the range rather than the bottom.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0029 | +0.091 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.1070 | -0.006 | correlation with the growth score (-0.11) times its level today (+0.05) |
| inflation_alignment | +0.1925 | -0.052 | correlation with the inflation score (+0.19) times its level today (-0.27) |
| monetary_policy_alignment | +0.0821 | -0.018 | correlation with the monetary_policy score (+0.08) times its level today (-0.22) |
| financial_conditions_alignment | +0.2866 | +0.101 | correlation with the financial_conditions score (+0.29) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (22.13%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 11.45% | 0.50 | 15% | +7.42% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 7.57% | 0.40 | 25% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +2.59% a year (all months +6.00%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 9.02% | 0.40 | 25% | Equilibrium excess return +4.99% at a 1.9% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 9.04% | 0.29 | 20% | 2.19% dividends +0.00% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 2.45% variance add-back (dividends from WRDS 2026-09; no buyback data; no long valuation history, drift 0). |
| `implied_erp_cape` | 11.76% | 0.35 | 15% | 7.01% real earnings yield (EEM trailing earnings yield) + 2.3% expected inflation + 2.45% variance add-back. |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | — | — | — | unavailable: not applicable to equity |
| `auto_blend` | 9.84% | 0.40 | — | Confidence-weighted average of 5 methods: historical_erp 26%, regime_adjusted 21%, bl_equilibrium 21%, inverse_gordon 15%, implied_erp_cape 18%. |

## 10. The judgment

Selection: **custom blend** — `historical_erp` 15%, `regime_adjusted` 25%, `bl_equilibrium` 25%, `inverse_gordon` 20%, `implied_erp_cape` 15%. Final estimate 9.44%, inside the hard [7.57, 11.76] range Exhibit 4 requires.

> I use a custom blend: historical 15%, regime-adjusted 25%, Black-Litterman 25%, Gordon 20%, CAPE 15%. That gives 9.44%, about 0.4pp below the 9.84% auto-blend and well inside the [7.57, 11.76] range. Dispersion is moderate at 4.19pp. Compared with the confidence-weighted blend, I made three moves. First, I trimmed historical_erp (11.45%, down to 15% from 26%), because it adds a full 7.4% excess premium to today's 4.03% T-bill, above the 8.0% compound and roughly 10.4% arithmetic realised since 1990. Second, I trimmed implied_erp_cape for the dilution and persistent-discount reasons above. Third, I raised the late-cycle regime-adjusted and equilibrium anchors; BL's 9.02% reflects EM's beta to the ETF market portfolio. The adjustment is deliberately small, because return estimates are the weakest input. At 22.1% volatility, the highest in the universe (Key consideration 1), 9.44% implies a Sharpe of about 0.24 and a geometric return near 7%. That is lower than US large cap on a risk-adjusted basis, so risk-based portfolio-construction methods will rightly keep EM's weight small. Confidence is medium, not high, given the low-confidence regime call, the dollar sensitivity and the China/semiconductor concentration. The governing IPS (config/ips.yaml) is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 7.57% | the most pessimistic available candidate is `regime_adjusted` at 7.57%, -1.87pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged +2.59% a year (all months +6.00%); credibility weight 0.72, plus 4.03% T-bill. |
| **base** | 9.44% | The judge's estimate, 9.44%, by custom blend across 6 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 11.76% | the most optimistic available candidate is `implied_erp_cape` at 11.76%, +2.32pp against the judged estimate. 7.01% real earnings yield (EEM trailing earnings yield) + 2.3% expected inflation + 2.45% variance add-back. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **The highest-volatility asset in the universe.** Around 22% annualised on our covariance matrix, against roughly 15% for US large cap. Any expected return has to be judged against that, and a risk-based PC method will give it a small weight however attractive the CMA.
2. **Three countries are most of the index.** China, Taiwan and Korea together run near 60% of weight, and Taiwan and Korea are concentrated in semiconductors. This is substantially a China policy position plus a semiconductor cycle position.
3. **The dollar and global liquidity dominate the short run.** EM equity is one of the most dollar-sensitive assets here: a strong dollar tightens local funding conditions and compresses multiples at the same time.
4. **Cheap for reasons that may not close.** Exhibit 8 puts EM at CAPE around 13, the cheapest in the universe, and yet the paper's judge marked it down only -0.2% - treating most of the discount as compensation for governance, state ownership and capital-controls risk rather than as mispricing. Reaching a very different conclusion needs an argument about why the discount should close.
5. **This is unhedged equity, not local-currency debt.** Do not import carry or local-rate reasoning from `usd_em_debt`; the two have different risk drivers despite the shared label.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `french:Emerging_5_Factors[Mkt-RF + RF]` (academic_index): 1989-07-31 to 1994-05-31, 59 months
- `VEIEX` (index_fund): 1994-06-30 to 2003-04-30, 107 months
- `EEM` (etf): 2003-05-31 to 2026-09-30, 281 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

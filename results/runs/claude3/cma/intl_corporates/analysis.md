# International Corporates — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 5.16%** over 3 years, nominal, against expected volatility of 9.18%. Judge confidence **medium**, selection by **custom blend** (`yield_building_block` 65%, `bl_equilibrium` 25%, `regime_adjusted` 10%). The 5 available candidates span 4.44%–6.14% (1.70pp), described as **tight** dispersion.

## 2. The asset class

**International Corporates** (fixed income), tracked by `PICB` against S&P International Corporate Bond.

- **Macro sensitivity:** Growth (+), Rates (-), Inflation (-), Dollar (--)
- **Primary valuation lens:** local long yields (German, UK) plus a credit spread proxied from US IG
- **Return history from** 1986-10-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls a fragile, late-cycle-adjacent expansion with sticky inflation, at low confidence (0.35) and a 20-30% recession probability. For an unhedged euro-heavy corporate bond index, late-cycle logic favours the starting-yield anchor over backward-looking premia. The regime-adjusted candidate (4.44%) shows that past expansion months were followed by near-zero excess returns (+0.04%). That fits an asset whose credit leg widens as cycles mature and whose currency leg suffers in dollar-strength episodes. Because the regime call is low-confidence and the method already shrinks toward the unconditional premium, I give it a modest 10% as a late-cycle haircut rather than a driving weight. The recession tail argues against the historical ERP, not for a larger adjustment.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | -3.47% | 7.35% | -0.95 | -1.02 | -6.7% | -4.7% | 58% |
| 3y (36m) | 5.53% | 8.90% | 0.16 | 0.23 | -7.1% | -4.7% | 64% |
| 5y (60m) | -2.03% | 11.68% | -0.44 | -0.55 | -31.0% | -8.2% | 57% |
| 10y (120m) | 0.25% | 10.28% | -0.16 | -0.21 | -34.9% | -8.6% | 56% |
| since_1990 (441m) | 4.51% | 9.24% | 0.23 | 0.33 | -34.9% | -8.6% | 58% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| intl_sovereigns | +0.92 | cash | +0.08 |
| usd_em_debt | +0.84 | commodities | +0.18 |
| ig_corporates | +0.83 | long_treasuries | +0.50 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| yield_level | +3.0704 | +0.449 | IRLTLT01DEM156N: starting yield against its own history: the dominant predictor of bond return |

The judge's valuation assessment:

> The valuation lens is local long yields (mean of German and UK 10-year, 4.00%) plus a credit spread. That spread is proxied from the US IG OAS (BAMLC0A0CM, 0.84%), because no non-US series has the history. European credit cycles correlate with US ones but are not identical, and the estimate inherits that approximation. The yield-level signal (+0.45) says starting local yields are high against their own history, the strongest predictor of bond returns over a horizon near duration. The 0.10% expected credit loss is already netted once in the building block; I did not subtract it again. The building block is a local-currency yield on an unhedged USD holding, so it says nothing about EUR/GBP versus USD. Currency is the first driver of this asset's return and the credit spread only the second. With German/UK average yields roughly level with the 4.03% US T-bill, carry gives no strong reason to tilt the estimate either way, so FX enters as volatility rather than as an expected-return adjustment.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.0041 | -0.130 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0385 | -0.482 | price against its 10-month moving average |
| mean_reversion | +0.1733 | -0.331 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.0041 | -0.444 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite is roughly neutral (+0.06), with a split underneath. Valuation is constructive (yield_level +0.45), while every technical signal is negative: trend -0.48, relative momentum -0.44, mean reversion -0.33, 12-1 momentum -0.13. This matches a 1-year return of -3.47%, likely driven by currency and rate moves rather than credit. Macro alignments are all near zero. Technicals matter little over a 3-year horizon for a bond whose return is mostly carry, so they do not justify moving below the yield anchor. They do argue against leaning toward the upper end of the range (historical ERP 6.14%). The final figure therefore sits slightly below the auto-blend.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | -0.0005 | -0.034 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.1127 | -0.006 | correlation with the growth score (-0.11) times its level today (+0.05) |
| inflation_alignment | +0.2128 | -0.058 | correlation with the inflation score (+0.21) times its level today (-0.27) |
| monetary_policy_alignment | +0.0155 | -0.003 | correlation with the monetary_policy score (+0.02) times its level today (-0.22) |
| financial_conditions_alignment | +0.2329 | +0.082 | correlation with the financial_conditions score (+0.23) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (9.18%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 6.14% | 0.30 | — | +2.11% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 4.44% | 0.25 | 10% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +0.04% a year (all months +1.37%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.45% | 0.40 | 25% | Equilibrium excess return +1.42% at a 0.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to fixed_income |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 5.16% | 0.48 | 65% | 4.00% starting yield + 0.84% spread - 0.10% expected credit loss + 0.42% variance add-back (mean of IRLTLT01DEM156N, IRLTLT01GBM156N; + BAMLC0A0CM spread; local-currency yield on an unhedged USD holding). |
| `auto_blend` | 5.32% | 0.38 | — | Confidence-weighted average of 4 methods: historical_erp 21%, regime_adjusted 17%, bl_equilibrium 28%, yield_building_block 34%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 65%, `bl_equilibrium` 25%, `regime_adjusted` 10%. Final estimate 5.16%, inside the hard [4.44, 6.14] range Exhibit 4 requires.

> Under the ratified IPS, I anchor on yield_building_block (65%), the strongest fixed-income candidate at a horizon near duration. I add Black-Litterman (25%) as a cross-check, since its 5.45% equilibrium figure sits close to the yield anchor. Regime_adjusted (10%) adds a modest late-cycle haircut. I give historical_erp zero weight: its 6.14% embeds the 1990-2026 secular fall in European yields and cannot repeat from today's starting point. BL's 0.02% market weight shows how thinly held PICB is, the thinnest index in the fixed-income sleeve, so I hold it below the yield anchor. The result, 5.16%, is about 1.1pp over T-bills, a Sharpe near 0.13 at 9.18% volatility. That is deliberately modest. This is largely a euro position with a proxied European IG credit leg attached, and it duplicates intl_sovereigns (currency) and ig_corporates (credit). The estimate should not make it look clearly preferable to holding those two separately. Confidence is medium rather than high for three reasons: currency risk sits outside the forecast, the spread is a US proxy, and the index history is noisy.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 4.44% | the most pessimistic available candidate is `regime_adjusted` at 4.44%, -0.72pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged +0.04% a year (all months +1.37%); credibility weight 0.72, plus 4.03% T-bill. |
| **base** | 5.16% | The judge's estimate, 5.16%, by custom blend across 5 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 6.14% | the most optimistic available candidate is `historical_erp` at 6.14%, +0.98pp against the judged estimate. +2.11% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Currency dominates, then credit.** Unhedged like `intl_sovereigns`, so the dollar is the first driver and the credit spread is the second. Two sources of risk, neither of them the one a reader expects from the name.
2. **Our credit input is a proxy and you should say so.** `config/signals.yaml` uses the US IG spread (`BAMLC0A0CM`) for this asset because no comparable non-US series has the history. European credit cycles are correlated with but not identical to US ones, and the estimate inherits that approximation.
3. **Mostly EUR-denominated issuance,** so this is largely a euro position with European corporate credit attached, not a globally diversified one.
4. **The thinnest index in the fixed-income sleeve.** Less liquid and more narrowly held than LQD, which makes the index history noisier and the tracking of any real portfolio looser.
5. **Marginal value over holding `intl_sovereigns` and `ig_corporates` separately is small.** Its currency leg duplicates the first and its credit leg duplicates the second. If your estimate implies it is clearly preferable to both, explain what it adds that they do not.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `RPIBX` (active_fund): 1986-10-31 to 2010-06-30, 285 months
- `PICB` (etf): 2010-07-31 to 2026-09-30, 195 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

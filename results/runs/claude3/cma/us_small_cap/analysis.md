# US Small Cap — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 9.34%** over 3 years, nominal, against expected volatility of 19.48%. Judge confidence **low**, selection by **custom blend** (`historical_erp` 15%, `regime_adjusted` 10%, `bl_equilibrium` 30%, `inverse_gordon` 25%, `implied_erp_cape` 20%). The 6 available candidates span 6.65%–12.38% (5.73pp), described as **moderate** dispersion.

## 2. The asset class

**US Small Cap** (equity), tracked by `IWM` against Russell 2000.

- **Macro sensitivity:** Growth (++), Rates (--), Inflation (-), Dollar (+)
- **Primary valuation lens:** relative valuation against large cap; price/book and EV/sales are more usable than P/E
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls an expansion, but a fragile, late-cycle-adjacent one. Confidence is low (0.35), inflation is sticky and policy is restrictive, with a 20-30% recession probability. For small caps this matters more than for any other equity sleeve (consideration 3). Russell 2000 balance sheets carry more floating-rate and short-maturity debt, so a 4% T-bill and restrictive policy press directly on interest coverage, not just on the discount rate. Exhibit 4 tilts late-cycle environments toward valuation and regime-adjusted methods, and the low regime confidence argues against leaning on any regime-conditional figure. The regime_adjusted candidate (11.78%) rests on 155 'expansion' months that were mostly not this fragile, high-rate variety, and its credibility weight of 0.72 does not fix the label risk. I cut it to 10%. The weight goes to equilibrium (BL) and to cash-flow and earnings-based anchors, which do not depend on the regime label being right.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 16.02% | 16.69% | 0.75 | 1.49 | -7.3% | -5.2% | 67% |
| 3y (36m) | 17.58% | 19.60% | 0.70 | 1.23 | -19.0% | -8.4% | 61% |
| 5y (60m) | 6.21% | 20.90% | 0.21 | 0.33 | -26.8% | -9.9% | 55% |
| 10y (120m) | 9.75% | 20.92% | 0.44 | 0.66 | -32.3% | -21.5% | 63% |
| since_1990 (441m) | 9.58% | 19.42% | 0.43 | 0.63 | -52.5% | -21.5% | 62% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| us_value | +0.90 | cash | -0.06 |
| us_large_cap | +0.86 | gold | +0.02 |
| us_growth | +0.76 | short_treasuries | +0.03 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> Consideration 2 rules out treating index-level P/E or CAPE as reliable here: roughly 40% of Russell 2000 constituents lose money. The implied_erp_cape candidate uses IWM's vendor trailing earnings yield (5.78%), not the WRDS aggregate. Vendor P/E effectively excludes loss-makers, so this is closer to the profitable-subset earnings yield the asset file prefers. That makes it usable, but it overstates the earnings power of the whole index. I therefore kept it at 20%, slightly above its auto-blend share but below what a clean earnings yield would earn. The inverse_gordon candidate (6.65%) is the most conservative input. Net buybacks are -0.86%, meaning net issuance and dilution, a real and persistent drag for small caps that large caps do not have. It also applies aggregate GDP growth with zero valuation drift, since there is no long valuation history to anchor a reversion. I gave it 25% because dilution is a genuine reduction in holder return, not a data artefact. The preferred relative lens, price/book or EV/sales against large cap, is not among the computed inputs. I cannot cite a quantified small-versus-large discount and have not assumed one. On the relative cases §3.3 asks for: US Large Cap's blend sits near 8.3% at about 15% volatility. A small-cap figure around 9.3% at 19.5% volatility gives a modest size premium with a lower Sharpe ratio (about 0.27), which is consistent with the dilution and rate headwinds. Against high yield, a profitable-subset real earnings yield near 5.8% plus about 2.3% inflation is broadly comparable to typical HY yields after credit losses. That makes the equity case roughly at parity, not compelling, which supports a mid-range estimate.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.2141 | +0.327 | 11-month return skipping the last 1, vs. its own history |
| trend | +0.0239 | -0.077 | price against its 10-month moving average |
| mean_reversion | +0.5450 | -0.513 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.2141 | +0.667 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite is mildly bullish (+0.14), but the parts conflict. Relative momentum (+0.67) and 12-1 momentum (+0.33) reflect a strong recent run: 16% over 1 year and 17.6% a year over 3 years. Mean reversion (-0.51) says that 36-month stretch tends to give back. Trend is slightly negative (-0.08). The macro alignment signals are near zero, apart from supportive financial conditions (+0.10). The signals neither confirm the high backward-looking candidates nor justify sitting at the Gordon floor. The mean-reversion reading over a 3-year horizon is a reason not to extrapolate the recent run, and so not to weight historical_erp heavily. I hedged by staying near the middle of the range, slightly below the auto-blend.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0030 | +0.103 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0601 | -0.003 | correlation with the growth score (-0.06) times its level today (+0.05) |
| inflation_alignment | +0.1548 | -0.042 | correlation with the inflation score (+0.15) times its level today (-0.27) |
| monetary_policy_alignment | +0.0889 | -0.019 | correlation with the monetary_policy score (+0.09) times its level today (-0.22) |
| financial_conditions_alignment | +0.2762 | +0.098 | correlation with the financial_conditions score (+0.28) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (19.48%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 12.38% | 0.50 | 15% | +8.35% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 11.78% | 0.40 | 10% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +7.65% a year (all months +8.00%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.82% | 0.40 | 30% | Equilibrium excess return +4.79% at a 4.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 6.65% | 0.42 | 25% | 1.21% dividends -0.86% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.90% variance add-back (net payout from WRDS 2025-12, rolled forward by IWM's price change; no long valuation history, drift 0). |
| `implied_erp_cape` | 9.98% | 0.35 | 20% | 5.78% real earnings yield (IWM trailing earnings yield) + 2.3% expected inflation + 1.90% variance add-back. |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | — | — | — | unavailable: not applicable to equity |
| `auto_blend` | 10.01% | 0.42 | — | Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%. |

## 10. The judgment

Selection: **custom blend** — `historical_erp` 15%, `regime_adjusted` 10%, `bl_equilibrium` 30%, `inverse_gordon` 25%, `implied_erp_cape` 20%. Final estimate 9.34%, inside the hard [6.65, 12.38] range Exhibit 4 requires.

> The final estimate is 9.34%, a custom blend: BL equilibrium 30%, inverse Gordon 25%, implied earnings yield 20%, historical ERP 15% and regime-adjusted 10%. This sits about 0.7pp below the auto-blend (10.01%), well inside [6.65, 12.38].

The main departure from the confidence weights is shifting about 0.18 of weight from the two backward-looking methods to BL equilibrium.
- Historical_erp (8.35% excess over T-bills since 1990) is a full-sample average that sits well above the asset's realised 9.58% total return since 1990. It embeds a period of falling rates that small caps, the most rate-sensitive equity sleeve, will not repeat with T-bills at 4%.
- Regime_adjusted depends on a low-confidence regime label.
- BL is the cleanest forward anchor. Its 4.8% market weight is ETF AUM, a proxy for the asset's size, but it is not biased by the sample's strong returns.

On the key considerations:
- I treated the earnings-yield method as a profitable-subset read and did not up-weight it (consideration 2).
- I kept the Gordon dilution term rather than dismissing it.
- I weighed the floating-rate exposure against the restrictive policy backdrop (consideration 3).
- The domestic-revenue profile (consideration 4) makes this a clean read on a fragile US cycle, which supports caution.
- I accepted the index total-return series behind the historical methods (consideration 5).

No survey consensus exists for this asset. No fund-flow or positioning view is claimed, since none can be sourced. Confidence is low: the regime call is low-confidence, the preferred P/B and EV/sales lens is absent, and small-cap return estimates at about 19.5% volatility are imprecise over 3 years. Governing IPS status is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 6.65% | the most pessimistic available candidate is `inverse_gordon` at 6.65%, -2.69pp against the judged estimate. 1.21% dividends -0.86% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.90% variance add-back (net payout from WRDS 2025-12, rolled forward by IWM's price change; no long valuation history, drift 0). |
| **base** | 9.34% | The judge's estimate, 9.34%, by custom blend across 6 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 12.38% | the most optimistic available candidate is `historical_erp` at 12.38%, +3.04pp against the judged estimate. +8.35% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Judge it against large cap and against corporate debt, not in isolation.** §3.3 names this explicitly for this agent. The small-cap case is almost always a relative-value case: the discount to large cap, and whether small-cap earnings yields beat high-yield debt.
2. **A large minority of the index does not earn money.** The share of Russell 2000 constituents with negative trailing earnings is commonly cited near 40%, which makes index-level P/E and CAPE unstable or meaningless. Prefer price/book, EV/sales or the earnings yield of the profitable subset, and say which you used.
3. **The most rate-sensitive equity sleeve.** Small caps carry more floating-rate and shorter-maturity debt than large caps, so a rise in short rates hits interest coverage directly rather than only through the discount rate.
4. **Mostly domestic revenue.** Less direct dollar translation exposure than large cap, which makes it a cleaner read on the US cycle and a poor hedge against a weak dollar.
5. **June reconstitution.** The annual Russell rebalance moves names in and out mechanically, so a long price history embeds turnover effects that are not a holding return. It is a reason to trust the index total-return series over any reconstructed one.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `french:6_Portfolios_2x3[mean(SMALL LoBM, ME1 BM2, SMALL HiBM)]` (academic_index): 1980-01-31 to 1980-01-31, 1 months
- `NAESX` (index_fund): 1980-02-29 to 2000-05-31, 244 months
- `IWM` (etf): 2000-06-30 to 2026-09-30, 316 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

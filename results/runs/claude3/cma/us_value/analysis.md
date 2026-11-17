# US Value — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 9.51%** over 3 years, nominal, against expected volatility of 14.84%. Judge confidence **medium**, selection by **custom blend** (`inverse_gordon` 35%, `bl_equilibrium` 20%, `regime_adjusted` 20%, `implied_erp_cape` 15%, `historical_erp` 10%). The 6 available candidates span 8.00%–11.99% (3.99pp), described as **moderate** dispersion.

## 2. The asset class

**US Value** (equity), tracked by `IWD` against Russell 1000 Value.

- **Macro sensitivity:** Growth (+), Rates (+), Inflation (+), Dollar (0)
- **Primary valuation lens:** the value-growth spread; dividend yield carries more of the total return
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls a fragile, late-cycle-adjacent expansion with sticky inflation, but only at low confidence (0.35) and with a 20-30% recession probability. Exhibit 4 tilts late-cycle environments toward valuation and regime-adjusted methods, so the cash-flow build carries the most weight. regime_adjusted keeps a moderate 20%: its 7.77% forward excess return after expansion months rests on 155 months and shrinks toward the unconditional premium (credibility 0.72), but the expansion label is uncertain. That uncertainty is also why I did not give it more. For value specifically, the regime mix is less hostile than for long-duration equity. Monetary policy is restrictive (-0.22) and inflation sticky, and value is the short-duration sleeve with a positive Rates sensitivity. Financials benefit from net interest margins and energy from inflation-linked commodity prices (considerations 1 and 2). That supports holding the estimate near the middle of the range rather than at the equilibrium floor. Nothing in the blend implies a negative rate sensitivity for this sleeve, which consideration 1 would treat as suspect.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 23.67% | 11.82% | 1.56 | 2.95 | -4.9% | -4.9% | 83% |
| 3y (36m) | 19.87% | 12.38% | 1.18 | 2.03 | -7.9% | -6.9% | 75% |
| 5y (60m) | 11.73% | 14.98% | 0.57 | 0.89 | -17.8% | -8.8% | 63% |
| 10y (120m) | 11.24% | 15.56% | 0.61 | 0.91 | -26.7% | -17.4% | 65% |
| since_1990 (441m) | 10.03% | 14.79% | 0.54 | 0.78 | -55.4% | -17.4% | 64% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| us_large_cap | +0.91 | cash | -0.04 |
| us_small_cap | +0.90 | short_treasuries | +0.05 |
| intl_developed | +0.86 | long_treasuries | +0.09 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> Consideration 4 says dividends are a larger share of value's return, so inverse_gordon gets the largest weight (35%). Its components are clean: 1.78% dividends, 1.72% net buybacks from WRDS (rolled forward by IWD's price change), nominal GDP growth and the variance add-back, with zero valuation drift. That zero drift is a limitation, since there is no long valuation history for this index. implied_erp_cape (8.11%) uses IWD's trailing earnings yield, a proxy rather than a true cyclically adjusted figure. Trailing earnings for an energy- and financials-heavy index are cyclical, so it gets 15%. On consideration 3, I take the reading that a wide book-based value-growth spread partly reflects intangible capital that book value cannot measure. I therefore add no spread-reversion premium. None of the candidates is book-based, so the artefact does not enter the arithmetic; I simply decline to lean toward the top of the range on 'value is cheap' grounds. After a 23.7% one-year and 19.9% three-year run, starting yields have compressed. That argues against the backward-looking historical_erp (11.99%), which is held to 10%. The rally embedded in the 1990-2026 sample is exactly what the valuation methods correct for.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.2523 | +0.493 | 11-month return skipping the last 1, vs. its own history |
| trend | +0.0706 | +0.219 | price against its 10-month moving average |
| mean_reversion | +0.5715 | -0.579 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.2523 | +0.778 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite signal is mildly bullish (+0.24) but internally split. Relative momentum (+0.78) and 12-1 momentum (+0.49) are strong, while the 36-month mean-reversion signal is clearly negative (-0.58). Over a 3-year horizon, the mean-reversion reading is the more relevant one: momentum decays within about a year, while a stretched 36-month run tends to give back part of its gains over the next few years. The macro alignment signals are near zero, apart from financial conditions (+0.13) and regime fit (+0.17), both modestly supportive. The net picture confirms neither the 12% historical tail nor the 8% equilibrium floor. It supports a mid-range estimate a little below the auto-blend, which is where the blend lands.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0036 | +0.166 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0343 | -0.002 | correlation with the growth score (-0.03) times its level today (+0.05) |
| inflation_alignment | +0.0670 | -0.018 | correlation with the inflation score (+0.07) times its level today (-0.27) |
| monetary_policy_alignment | +0.0670 | -0.015 | correlation with the monetary_policy score (+0.07) times its level today (-0.22) |
| financial_conditions_alignment | +0.3605 | +0.127 | correlation with the financial_conditions score (+0.36) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (14.84%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 11.99% | 0.50 | 10% | +7.96% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 11.71% | 0.40 | 20% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +7.77% a year (all months +7.43%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.00% | 0.40 | 20% | Equilibrium excess return +3.97% at a 5.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 9.00% | 0.42 | 35% | 1.78% dividends +1.72% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.10% variance add-back (net payout from WRDS 2025-12, rolled forward by IWD's price change; no long valuation history, drift 0). |
| `implied_erp_cape` | 8.11% | 0.35 | 15% | 4.71% real earnings yield (IWD trailing earnings yield) + 2.3% expected inflation + 1.10% variance add-back. |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | — | — | — | unavailable: not applicable to equity |
| `auto_blend` | 9.90% | 0.42 | — | Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%. |

## 10. The judgment

Selection: **custom blend** — `inverse_gordon` 35%, `bl_equilibrium` 20%, `regime_adjusted` 20%, `implied_erp_cape` 15%, `historical_erp` 10%. Final estimate 9.51%, inside the hard [8.00, 11.99] range Exhibit 4 requires.

> The final estimate is a custom blend of 9.51%, inside the 8.00-11.99% range and 0.39pp below the confidence-weighted auto-blend (9.90%). The adjustment is deliberately small; return forecasts are the least reliable input in the chain. The blend makes three departures from the auto-blend. First, it moves weight onto inverse_gordon (35%), because consideration 4 makes the payout build more reliable for value than for other sleeves. Second, it cuts historical_erp from 24% to 10%. That method extrapolates a 1990-2026 premium after a strong recent run that the mean-reversion signal flags as stretched, and it takes no account of starting valuations. Third, it keeps bl_equilibrium (8.00%) at 20% as an anchor. Its 5% ETF-AUM weight is only a proxy for market size, and the Russell style split means part of that weight double-counts names also held in us_growth (consideration 5). The BL figure also takes no view on the rate and commodity exposures, so it is not given more weight. The sector composition (consideration 2) makes this partly a view on bank margins and oil. Under sticky inflation and restrictive policy, that composition is a modest support, and it is reflected in the 20% regime_adjusted weight. No candidate is book-based, so the intangibles caveat (consideration 3) is handled by adding no value-spread reversion premium on top. Confidence is medium: dispersion is moderate at 3.99pp, the macro regime is held at low confidence, and the two highest-weighted valuation methods rely on a rolled-forward payout yield and a trailing earnings-yield proxy. Governing policy is config/ips.yaml, whose header status is ratified for this run.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 8.00% | the most pessimistic available candidate is `bl_equilibrium` at 8.00%, -1.51pp against the judged estimate. Equilibrium excess return +3.97% at a 5.0% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| **base** | 9.51% | The judge's estimate, 9.51%, by custom blend across 6 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 11.99% | the most optimistic available candidate is `historical_erp` at 11.99%, +2.48pp against the judged estimate. +7.96% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Short-duration equity.** Value's cash flows arrive sooner than growth's, so it is the one equity sleeve that can benefit from higher rates. Expect its sign on Rates to be the opposite of US Growth's, and treat an estimate that implies otherwise as suspect.
2. **Sector composition is the exposure.** Financials, energy and industrials dominate, so this is partly a bet on bank net interest margins and on the oil price rather than on a style premium in the abstract.
3. **Book value measures less than it used to.** Value screens built on book value penalise firms whose capital is intangible, and intangible investment has grown as a share of the economy. A wide book-based value spread may be a measurement artefact rather than an opportunity. Say which reading you take.
4. **Dividend yield is a larger share of expected return** than for the other equity sleeves, which makes the inverse-Gordon build more reliable here than it is for growth.
5. **Style indices overlap.** Russell splits some companies across both the Value and Growth indices, so this sleeve and `us_growth` are not mutually exclusive holdings and their combined weight double-counts those names.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `french:6_Portfolios_2x3[BIG HiBM]` (academic_index): 1980-01-31 to 1992-10-31, 154 months
- `VIVAX` (index_fund): 1992-11-30 to 2000-05-31, 91 months
- `IWD` (etf): 2000-06-30 to 2026-09-30, 316 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

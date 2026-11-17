# Commodities — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 5.61%** over 3 years, nominal, against expected volatility of 19.10%. Judge confidence **low**, selection by **custom blend** (`historical_erp` 30%, `regime_adjusted` 35%, `bl_equilibrium` 35%). The 4 available candidates span 4.56%–6.54% (1.98pp), described as **tight** dispersion.

## 2. The asset class

**Commodities** (real assets), tracked by `DBC` against DBIQ Optimum Yield Diversified Commodity.

- **Macro sensitivity:** Growth (+), Rates (0), Inflation (++), Dollar (-)
- **Primary valuation lens:** no cash flow: spot prices (`DCOILWTICO`, `DCOILBRENTEU`, `PCOPPUSDM`) plus the collateral rate (`DTB3`)
- **Return history from** 1984-02-29 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls a fragile, late-cycle-adjacent expansion with sticky above-history inflation, but only at 0.35 confidence and with a 20-30% recession probability. For commodities that mix cuts both ways. Sticky inflation is the environment where this asset earns its place: it has the highest inflation sensitivity in the universe. But commodities, being largely an oil position, are also the asset hit hardest when a late-cycle expansion tips into demand destruction. The regime-adjusted candidate captures this. Excess returns over the three years after past expansion months averaged -0.49%, against +3.17% unconditionally, because forward windows from mature expansions often ran into the 2008 and 2014-15 commodity busts. With the regime tilting late-cycle, Exhibit 4 step 2 points toward the regime-adjusted method. I raise its weight from the blend's 31% to 35%, but not further, because the regime label itself is low-confidence.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 48.28% | 23.68% | 1.64 | 3.44 | -14.3% | -9.6% | 83% |
| 3y (36m) | 13.94% | 16.58% | 0.60 | 1.07 | -14.3% | -9.6% | 64% |
| 5y (60m) | 12.98% | 17.28% | 0.57 | 0.96 | -23.0% | -9.6% | 60% |
| 10y (120m) | 9.80% | 17.01% | 0.49 | 0.75 | -37.8% | -17.3% | 58% |
| since_1990 (441m) | 3.48% | 19.06% | 0.13 | 0.19 | -74.6% | -25.1% | 53% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| us_value | +0.46 | long_treasuries | -0.31 |
| intl_developed | +0.38 | intermediate_treasuries | -0.31 |
| us_small_cap | +0.36 | short_treasuries | -0.29 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> Key consideration 5 applies directly: there is no yield and no earnings, so nothing makes commodities cheap or expensive. That is why inverse_gordon, implied_erp_cape and yield_building_block are correctly unavailable, and I do not try to substitute a pseudo-valuation for them. The closest substitutes are curve shape, inventories and marginal cost. None of these is in our inputs, so I cannot claim a backwardation or contango view. Key consideration 1 says the roll decides total return. Consideration 2 warns that spot appreciation overstates it. Both are respected because historical_erp is built from the fund's return series since 1990, which embeds the actual roll and collateral, not from the oil or copper spot series. Even that candidate is generous: its 2.51% excess return includes the 2000s supercycle, while the full-history fund Sharpe is only 0.07. A 48% one-year gain also leaves prices extended against their own history. With no anchor to revert to, I treat that as a reason to lean away from the most optimistic candidate, not as a valuation signal.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.3935 | +0.672 | 11-month return skipping the last 1, vs. its own history |
| trend | +0.1598 | +0.560 | price against its 10-month moving average |
| mean_reversion | +0.4333 | -0.421 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.3935 | +1.000 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The signals split along time horizons. Momentum (+0.67), trend (+0.56) and relative momentum (+1.00, top of the 18 assets) are strongly bullish. That is consistent with commodity trend persistence over months, but a 3-year horizon outlasts most of that persistence. The 36-month mean-reversion signal is -0.42, which matches the regime-adjusted method's weak forward excess return after extended runs. The macro alignment signals are all close to zero, inflation alignment included at +0.01. So the measured link to today's inflation score gives no independent support for a higher number. I do not let the +0.34 composite, which is dominated by short-horizon technicals, pull the estimate toward historical_erp. Nor do I override it to the floor, since trend strength argues against a sharp near-term reversal. No flow or positioning view is available (decision 26), and I claim none.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0007 | +0.024 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | +0.1943 | +0.010 | correlation with the growth score (+0.19) times its level today (+0.05) |
| inflation_alignment | -0.0478 | +0.013 | correlation with the inflation score (-0.05) times its level today (-0.27) |
| monetary_policy_alignment | +0.1890 | -0.041 | correlation with the monetary_policy score (+0.19) times its level today (-0.22) |
| financial_conditions_alignment | +0.2912 | +0.103 | correlation with the financial_conditions score (+0.29) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (19.10%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 6.54% | 0.50 | 30% | +2.51% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 4.56% | 0.40 | 35% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged -0.49% a year (all months +3.17%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 5.87% | 0.40 | 35% | Equilibrium excess return +1.84% at a 0.1% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to real_assets |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to real_assets |
| `survey_consensus` | — | — | — | unavailable: not applicable to real_assets |
| `yield_building_block` | — | — | — | unavailable: not applicable to real_assets |
| `auto_blend` | 5.72% | 0.44 | — | Confidence-weighted average of 3 methods: historical_erp 38%, regime_adjusted 31%, bl_equilibrium 31%. |

## 10. The judgment

Selection: **custom blend** — `historical_erp` 30%, `regime_adjusted` 35%, `bl_equilibrium` 35%. Final estimate 5.61%, inside the hard [4.56, 6.54] range Exhibit 4 requires.

> Dispersion is tight at 1.98pp, so method choice moves the answer only modestly. Per the asset-class guidance for commodities, confidence stays low. I use a custom blend of 30% historical_erp, 35% regime_adjusted and 35% bl_equilibrium, giving 5.61%. That is slightly below the 5.72% auto-blend and well inside [4.56, 6.54]. I trim historical_erp from 38% to 30% for two reasons: its since-1990 premium is flattered by the 2000s supercycle, and the trailing 48% run plus late-cycle positioning make the long-run average a weaker guide now. I hold BL at 35%. Its 0.1% ETF-AUM weight is a thin proxy for the asset's true size, but its +1.84% excess (Sharpe about 0.10) matches the near-0.09 ex-ante Sharpe noted in key consideration 3. I lift regime_adjusted to 35% because it is the only candidate that conditions on the current cycle. The result is about 1.6pp over the 4.03% T-bill, an implied Sharpe near 0.08 at 19.1% volatility. Per key consideration 3, the allocation case for commodities should rest on inflation hedging and diversification, not on this return. Per consideration 4, the estimate is largely a crude-oil view with metals and agriculture attached. The governing IPS (config/ips.yaml) is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 4.56% | the most pessimistic available candidate is `regime_adjusted` at 4.56%, -1.05pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged -0.49% a year (all months +3.17%); credibility weight 0.72, plus 4.03% T-bill. |
| **base** | 5.61% | The judge's estimate, 5.61%, by custom blend across 4 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 6.54% | the most optimistic available candidate is `historical_erp` at 6.54%, +0.93pp against the judged estimate. +2.51% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Total return is spot plus roll plus collateral, and the roll is what decides it.** A futures-based index earns the T-bill rate on its collateral, the change in spot, and a roll yield that is negative in contango and positive in backwardation. Over long stretches the roll has dominated. DBC's 'optimum yield' rule exists specifically to choose the contract that minimises contango drag.
2. **A spot price history is not this asset's return history.** This is the most important trap on this asset: using oil or copper price appreciation as a proxy for commodity returns ignores the roll and overstates the result, often by several points a year. Our `cma_series` carries spot series for the signal layer; the return history comes from the fund, not from them.
3. **The best inflation hedge here and the worst risk-adjusted return.** Highest Inflation sensitivity in the universe and an ex-ante Sharpe near 0.09 on our inputs. Its case is a hedging case, and it should be argued as one rather than as a return case.
4. **Energy-weighted, so largely an oil position.** The diversified label understates how much of the variance comes from crude. Judge it partly as an oil exposure with industrial metals and agriculture attached.
5. **No yield and no earnings, so no valuation anchor exists.** There is nothing to be cheap or expensive relative to. Inventory levels, the curve shape and marginal production cost are the closest available substitutes for a valuation signal.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `^SPGSCI` (index): 1984-02-29 to 2006-02-28, 265 months
- `DBC` (etf): 2006-03-31 to 2026-09-30, 247 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

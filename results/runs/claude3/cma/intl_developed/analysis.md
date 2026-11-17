# International Developed — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 8.18%** over 3 years, nominal, against expected volatility of 16.00%. Judge confidence **medium**, selection by **custom blend** (`historical_erp` 25%, `regime_adjusted` 25%, `bl_equilibrium` 25%, `inverse_gordon` 10%, `implied_erp_cape` 15%). The 6 available candidates span 7.67%–8.94% (1.28pp), described as **tight** dispersion.

## 2. The asset class

**International Developed** (equity), tracked by `EFA` against MSCI EAFE.

- **Macro sensitivity:** Growth (+), Rates (-), Inflation (-), Dollar (--)
- **Primary valuation lens:** CAPE against the US; local long yields (German, Japanese, UK) as the discount rate
- **Return history from** 1983-02-28 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> The stage-1 call is an expansion, but a fragile, late-cycle-adjacent one. It is held at low confidence (0.35), inflation is sticky, policy is restrictive and recession odds are 20-30%. Exhibit 4 says late-cycle should tilt toward regime-adjusted and valuation methods. Here the only real valuation input is a structurally cheap EAFE earnings yield (see valuation_context), so I put the late-cycle tilt into regime_adjusted rather than the valuation methods. I give regime_adjusted equal weight with historical_erp, above its confidence-based share. Its forward-looking construction is informative here: excess returns in the three years after past expansion months were +3.34%, against +4.41% unconditionally, which fits a late-cycle starting point. I do not weight it more heavily for two reasons. The regime label itself is low-confidence, and the 155-month sample mixes two different cycles. Europe is about 60% of the index, exposed to energy costs and ECB policy. Japan is about a fifth, where the governance-reform story has its own momentum. One US-centred regime label fits neither cycle cleanly.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 15.08% | 12.75% | 0.88 | 1.26 | -7.8% | -7.8% | 83% |
| 3y (36m) | 18.31% | 11.89% | 1.11 | 1.82 | -8.4% | -7.8% | 72% |
| 5y (60m) | 9.29% | 15.56% | 0.41 | 0.62 | -27.5% | -9.2% | 63% |
| 10y (120m) | 8.96% | 14.95% | 0.49 | 0.73 | -27.6% | -14.1% | 64% |
| since_1990 (441m) | 5.86% | 16.00% | 0.27 | 0.38 | -57.4% | -20.8% | 59% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| us_value | +0.86 | cash | +0.02 |
| us_large_cap | +0.83 | long_treasuries | +0.25 |
| intl_corporates | +0.82 | short_treasuries | +0.25 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> EAFE screens cheap. The trailing earnings yield is 5.37%, which drives implied_erp_cape to the top of the range at 8.94%. Key consideration 4 warns that this asset will always look cheap on CAPE against the US. Much of the discount reflects a structurally different sector mix: less technology, and more financials, industrials and staples. Lower long-run growth and governance differences explain more of it. Those parts are not mean-reverting over a 3-year horizon. I therefore cut implied_erp_cape slightly to 15% weight, and I do not credit any valuation re-rating. I also discount inverse_gordon to 10%, for reasons specific to its inputs:
- its yield is dividends only, with zero buybacks (Compustat Global has none);
- its growth term is US SPF real GDP and CPI applied to Europe and Japan;
- its valuation drift is set to zero for lack of history.
With those adjustments, the valuation methods still sit above the backward-looking ones, so valuation adds a modest upward lean rather than a large one. On key consideration 5: the historical, regime and BL candidates are built on the 4.03% US T-bill, not on Bund, JGB or Gilt yields. Local yields are lower than US bills, so a build-up anchored to local rates would come out somewhat lower in local terms. The gap would be offset in USD terms by expected currency carry. I treat the two effects as netting and do not adjust for them.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.1821 | +0.331 | 11-month return skipping the last 1, vs. its own history |
| trend | +0.0240 | -0.007 | price against its 10-month moving average |
| mean_reversion | +0.5299 | -0.642 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.1821 | +0.556 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite signal is mildly positive (+0.14), but its components conflict. Momentum is positive (12-1 at +0.33; relative momentum at +0.56, the strongest cross-asset rank). Mean reversion is firmly negative at -0.64, after a 3-year annualised return of 18.3% that is well above the long-run 5.9% since 1990. Trend is flat. Part of that 3-year run is dollar weakness: the USD share class is unhedged, so currency drives both return and volatility. Mean reversion therefore partly implies a risk that the dollar recovers. The macro alignments are close to zero, apart from a small positive from easy financial conditions. Overall, the signals do not justify moving away from the centre of a tight range in either direction. They are consistent with a marginal trim below the auto-blend, not with a call above it. The short-term momentum is real, but a 3-year horizon is long enough for the mean-reversion signal to matter.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0038 | +0.162 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0566 | -0.003 | correlation with the growth score (-0.06) times its level today (+0.05) |
| inflation_alignment | +0.1031 | -0.028 | correlation with the inflation score (+0.10) times its level today (-0.27) |
| monetary_policy_alignment | +0.0324 | -0.007 | correlation with the monetary_policy score (+0.03) times its level today (-0.22) |
| financial_conditions_alignment | +0.3352 | +0.118 | correlation with the financial_conditions score (+0.34) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (16.00%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 8.29% | 0.50 | 25% | +4.26% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 7.67% | 0.40 | 25% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +3.34% a year (all months +4.41%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.02% | 0.40 | 25% | Equilibrium excess return +3.99% at a 4.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 8.48% | 0.29 | 10% | 2.80% dividends +0.00% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.28% variance add-back (dividends from WRDS 2026-09; no buyback data; no long valuation history, drift 0). |
| `implied_erp_cape` | 8.94% | 0.35 | 15% | 5.37% real earnings yield (EFA trailing earnings yield) + 2.3% expected inflation + 1.28% variance add-back. |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | — | — | — | unavailable: not applicable to equity |
| `auto_blend` | 8.25% | 0.40 | — | Confidence-weighted average of 5 methods: historical_erp 26%, regime_adjusted 21%, bl_equilibrium 21%, inverse_gordon 15%, implied_erp_cape 18%. |

## 10. The judgment

Selection: **custom blend** — `historical_erp` 25%, `regime_adjusted` 25%, `bl_equilibrium` 25%, `inverse_gordon` 10%, `implied_erp_cape` 15%. Final estimate 8.18%, inside the hard [7.67, 8.94] range Exhibit 4 requires.

> Dispersion is tight: 7.67-8.94%, a 1.28pp spread. The decision is therefore about modest tilts, not method selection. I use a custom blend that cuts the two valuation-based methods relative to the auto-blend and lifts regime_adjusted and bl_equilibrium. The weights are 25% each for historical_erp, regime_adjusted and bl_equilibrium, 10% for inverse_gordon and 15% for implied_erp_cape. The result is 8.18%, 0.07pp below the auto-blend's 8.25%.

The reasons for the tilts:
- Per key consideration 4, EAFE's persistent CAPE and earnings-yield discount is mostly sector mix and structure, not mean-reverting sentiment. I do not let the cheapness signal pull the estimate up.
- The Gordon candidate uses dividends-only inputs and US-based growth, so it gets less weight than its confidence implies.
- The late-cycle-adjacent regime supports the lower regime-conditioned premium.

The markdown is small and close to the paper's -0.3pp. That is deliberate, because return estimates are the least reliable input in the chain.

On currency (key consideration 1), the estimate assumes no expected contribution from the dollar in either direction. The candidates are USD-denominated, but none forecasts FX. Dollar moves enter through the 16% volatility, not the mean. The recent 3-year outperformance was partly dollar weakness, and I do not extrapolate it.

Confidence is medium. The candidates agree closely, but the regime call is weak, the index combines distinct European and Japanese cycles, and currency adds variance that none of the methods forecasts.

The governing IPS (config/ips.yaml) is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 7.67% | the most pessimistic available candidate is `regime_adjusted` at 7.67%, -0.51pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged +3.34% a year (all months +4.41%); credibility weight 0.72, plus 4.03% T-bill. |
| **base** | 8.18% | The judge's estimate, 8.18%, by custom blend across 6 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 8.94% | the most optimistic available candidate is `implied_erp_cape` at 8.94%, +0.76pp against the judged estimate. 5.37% real earnings yield (EFA trailing earnings yield) + 2.3% expected inflation + 1.28% variance add-back. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Unhedged, so currency is part of the asset.** The USD share class means the dollar is a first-order driver of both return and volatility. A large part of any historical outperformance or underperformance against the US is currency, not equity. State whether your estimate assumes a currency contribution and of what sign.
2. **Japan and Europe are the index.** Europe is roughly 60% and Japan roughly a fifth, so this is a bet on two quite different cycles aggregated into one number, with Japanese corporate governance reform and European energy costs pulling in different directions.
3. **A structurally different sector mix.** Much less technology and much more financials, industrials and staples than the S&P 500. That alone explains a large part of the persistent valuation discount, so the discount is not automatically an opportunity.
4. **It will always look cheap on CAPE.** EAFE has traded below the US on CAPE for most of the past two decades. A valuation-tilted method will therefore always favour it. The judgement you have to make is how much of the gap is sector mix and governance (structural, not closing) versus sentiment (mean-reverting). The paper's judge marked it down only -0.3%.
5. **The CMA uses local long yields.** `IRLTLT01DEM156N`, `IRLTLT01JPM156N` and `IRLTLT01GBM156N` stand in for the local risk-free rates, so a build-up method here is anchored to Bund, JGB and Gilt yields rather than to Treasuries.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `crsp_fund:RINSX` (active_fund): 1983-02-28 to 2001-08-31, 223 months
- `EFA` (etf): 2001-09-30 to 2026-09-30, 301 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

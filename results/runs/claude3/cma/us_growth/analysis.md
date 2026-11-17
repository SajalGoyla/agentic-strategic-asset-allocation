# US Growth — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 8.28%** over 3 years, nominal, against expected volatility of 16.91%. Judge confidence **low**, selection by **custom blend** (`historical_erp` 5%, `regime_adjusted` 5%, `bl_equilibrium` 25%, `inverse_gordon` 32%, `implied_erp_cape` 33%). The 6 available candidates span 7.12%–13.69% (6.57pp), described as **wide** dispersion.

## 2. The asset class

**US Growth** (equity), tracked by `IWF` against Russell 1000 Growth.

- **Macro sensitivity:** Growth (+), Rates (--), Inflation (-), Dollar (+)
- **Primary valuation lens:** CAPE and the implied ERP; both will read expensive, and the question is how much to mark down
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls an expansion, but a fragile, late-cycle-adjacent one, at low confidence (0.35), with sticky above-history inflation, a restrictive monetary-policy score (-0.22) and a 20-30% recession probability. Exhibit 4 tilts late-cycle conditions toward valuation and regime-adjusted methods. Here, though, the regime-adjusted candidate (13.69%) is simply the 'expansion' label applied at full credibility (0.72). It is not conditioned on the late-cycle or inflation features that matter most for the longest-duration equity sleeve, which loses on the discount-rate channel if inflation stays sticky and rates stay high. Given how weak the regime call is, I treat the regime candidate as a cousin of the historical ERP, not as independent evidence. I give it 5%, below its 19% auto-blend weight.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 7.36% | 17.90% | 0.27 | 0.52 | -12.0% | -5.2% | 42% |
| 3y (36m) | 24.06% | 16.27% | 1.15 | 2.23 | -12.0% | -8.4% | 64% |
| 5y (60m) | 13.48% | 19.27% | 0.56 | 0.88 | -30.7% | -12.2% | 60% |
| 10y (120m) | 17.95% | 17.80% | 0.89 | 1.45 | -30.7% | -12.2% | 67% |
| since_1990 (441m) | 11.28% | 16.84% | 0.56 | 0.84 | -61.9% | -17.8% | 61% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| us_large_cap | +0.95 | cash | +0.01 |
| us_small_cap | +0.76 | gold | +0.12 |
| us_value | +0.74 | short_treasuries | +0.12 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> This is the most expensive sleeve in the universe. IWF's trailing earnings yield is 3.39%, below the 4.03% T-bill, so the real earnings-yield build gives only about 3.1pp over cash once inflation and the variance add-back are included. The net payout yield is 1.77%, which needs 4.4% nominal growth just to reach the Gordon figure. Neither valuation candidate includes a multiple-compression term: Gordon's valuation change is set to 0 because there is no long valuation history outside US Large Cap. Both are therefore, if anything, generous for a sleeve whose 10-year return of 17.95% was flattered by re-rating. The historical ERP (13.46%) comes from a 1990-2026 sample dominated by growth and technology multiple expansion, and it is the method least suited to valuations at an extreme. Valuation and history disagree by about 6pp, which is information about where multiples stand, not noise. Mean reversion is slow and 3 years is short, so I do not go to the floor. I put 65% on the two valuation methods, above the paper's 60%.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.0636 | -0.189 | 11-month return skipping the last 1, vs. its own history |
| trend | +0.0590 | +0.044 | price against its 10-month moving average |
| mean_reversion | +0.6925 | -0.554 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.0636 | +0.111 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite is flat (0.00), but its parts point the same way as the markdown. Mean reversion is strongly negative (-0.55) after a 24% annualised 3-year run, and 12-1 momentum is negative (-0.19). Trend (+0.04) and relative momentum (+0.11) are only marginally positive. Regime fit (+0.26) is the one constructive signal, and it rests on the same low-confidence expansion label I have already discounted. The macro alignments are near zero; the small inflation drag (-0.04) is consistent with the asset's inflation and rate sensitivities. Nothing in the signals argues for leaning back toward the historical candidates, so they confirm a below-blend estimate rather than hedge against it.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0066 | +0.260 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0744 | -0.004 | correlation with the growth score (-0.07) times its level today (+0.05) |
| inflation_alignment | +0.1430 | -0.039 | correlation with the inflation score (+0.14) times its level today (-0.27) |
| monetary_policy_alignment | +0.0617 | -0.013 | correlation with the monetary_policy score (+0.06) times its level today (-0.22) |
| financial_conditions_alignment | +0.2752 | +0.097 | correlation with the financial_conditions score (+0.28) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (16.91%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 13.46% | 0.50 | 5% | +9.43% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 13.69% | 0.40 | 5% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +9.86% a year (all months +9.12%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 8.54% | 0.40 | 25% | Equilibrium excess return +4.51% at a 7.5% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 7.61% | 0.42 | 32% | 0.65% dividends +1.12% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.43% variance add-back (net payout from WRDS 2025-12, rolled forward by IWF's price change; no long valuation history, drift 0). |
| `implied_erp_cape` | 7.12% | 0.35 | 33% | 3.39% real earnings yield (IWF trailing earnings yield) + 2.3% expected inflation + 1.43% variance add-back. |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | — | — | — | unavailable: not applicable to equity |
| `auto_blend` | 10.29% | 0.42 | — | Confidence-weighted average of 5 methods: historical_erp 24%, regime_adjusted 19%, bl_equilibrium 19%, inverse_gordon 20%, implied_erp_cape 17%. |

## 10. The judgment

Selection: **custom blend** — `historical_erp` 5%, `regime_adjusted` 5%, `bl_equilibrium` 25%, `inverse_gordon` 32%, `implied_erp_cape` 33%. Final estimate 8.28%, inside the hard [7.12, 13.69] range Exhibit 4 requires.

> Final estimate 8.28%: about 2.0pp below the 10.29% auto-blend, matching the paper's Exhibit 8 markdown for US Growth, its largest in the universe. The weights are 65% on the valuation methods (implied ERP 33%, inverse Gordon 32%), 25% on Black-Litterman equilibrium, and 5% each on the historical ERP and regime-adjusted methods.

Why the historical candidates are cut: they are near-identical backward-looking views from a sample of secular multiple expansion. Taking them together at a combined 43% of the auto-blend would let one hindsight-heavy view drive the result.

Why the valuation candidates are not pushed further: I do not let them pull the estimate to the 7.12% floor, because neither carries an explicit valuation-drift term and a 3-year horizon is short for reversion. That leaves the estimate above the floor but within the bottom quarter of the range.

Black-Litterman (8.54%) gets a meaningful weight as a neutral anchor. It sits close to the valuation cluster, which is independent support for an estimate in the low 8s.

The markdown is meant to be the largest among the equity sleeves; this is the most expensive, most concentrated and longest-duration one. If another sleeve's judge marks down more, the PC stage should revisit the comparison.

Other points for the PC stage:
- **Concentration:** the top ten names can exceed half the index, so effective breadth is low. That is a further reason for a modest return expectation, not a diversification argument.
- **Overlap with US Large Cap:** correlation is above 0.9. US Growth should be read as a tilt on US Large Cap, not a separate holding, and holding both concentrates the portfolio in a handful of mega-cap technology names.
- **Implied Sharpe:** the estimate is about 4.25pp over cash at 16.9% volatility, roughly 0.25, which is deliberately low.
- **Sentiment:** no fund-flow or positioning view is claimed, because none is sourced, and the survey consensus is unavailable for this asset.

The governing IPS is reported as ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 7.12% | the most pessimistic available candidate is `implied_erp_cape` at 7.12%, -1.16pp against the judged estimate. 3.39% real earnings yield (IWF trailing earnings yield) + 2.3% expected inflation + 1.43% variance add-back. |
| **base** | 8.28% | The judge's estimate, 8.28%, by custom blend across 6 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 13.69% | the most optimistic available candidate is `regime_adjusted` at 13.69%, +5.41pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged +9.86% a year (all months +9.12%); credibility weight 0.72, plus 4.03% T-bill. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **The most expensive sleeve, and the paper's largest markdown.** Exhibit 8 gives US Growth a -2.0% adjustment to the auto-blend, the largest in the universe, with the judge putting 60% weight on valuation methods and 5% on the historical ERP. If your markdown here is not the largest of the equity sleeves, justify why.
2. **Longest-duration equity in the universe.** The most rate-sensitive equity sleeve on the discount-rate channel, as distinct from US Small Cap's coverage-ratio channel.
3. **Extreme concentration.** The top ten names can exceed half the index, so this is a concentrated position in a handful of mega-cap technology companies, not a diversified growth exposure. Effective breadth is far below the nominal constituent count.
4. **Valuation methods can produce very low or negative estimates.** When the earnings yield sits near or below the risk-free rate, the implied-ERP and inverse-Gordon builds return an equity premium near zero. That is information, not an error, but it is also why the candidate range for this asset is the widest in the universe. Do not let one extreme candidate drag the blend without saying so.
5. **It overlaps US Large Cap almost completely.** The two correlate above 0.9, so growth is a tilt on top of large cap rather than a separate holding. A portfolio holding both is concentrating, and the PC agents will not see that unless the CMAs make the overlap clear.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `french:6_Portfolios_2x3[BIG LoBM]` (academic_index): 1980-01-31 to 1992-10-31, 154 months
- `VIGRX` (index_fund): 1992-11-30 to 2000-05-31, 91 months
- `IWF` (etf): 2000-06-30 to 2026-09-30, 316 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

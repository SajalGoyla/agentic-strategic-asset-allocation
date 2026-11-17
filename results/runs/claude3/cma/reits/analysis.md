# REITs — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 9.09%** over 3 years, nominal, against expected volatility of 18.99%. Judge confidence **low**, selection by **custom blend** (`inverse_gordon` 40%, `bl_equilibrium` 25%, `regime_adjusted` 20%, `historical_erp` 15%). The 6 available candidates span 7.42%–11.94% (4.53pp), described as **moderate** dispersion.

## 2. The asset class

**REITs** (real assets), tracked by `VNQ` against MSCI US IMI Real Estate 25/50.

- **Macro sensitivity:** Growth (+), Rates (--), Inflation (+), Dollar (0)
- **Primary valuation lens:** the dividend yield plus NOI growth; cap rates against the real 10-year yield (`DFII10`)
- **Return history from** 1986-12-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 calls this a fragile, late-cycle-adjacent expansion with sticky above-history inflation, at low confidence (0.35) and a 20-30% recession probability. REITs are rate-sensitive levered equities: Growth (+), Rates (--). A restrictive monetary score (-0.22) together with sticky inflation argues against assuming policy easing that would compress cap rates. The regime-adjusted candidate (11.40%) uses forward three-year returns after expansion months. Its regime premium (+7.01%) sits below the unconditional premium (+8.28%), so even the regime view trims the historical figure. However, those expansion months fall mostly in a 1990-2021 sample of falling real yields, which flattered REIT returns. Under Exhibit 4, late-cycle tilts toward valuation and regime methods. I keep a meaningful regime_adjusted weight (0.20) but do not let it dominate, because the regime call itself is low-confidence and the sample's rate tailwind is unlikely to repeat.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 1.75% | 15.54% | -0.05 | -0.08 | -8.6% | -6.3% | 50% |
| 3y (36m) | 10.05% | 16.61% | 0.40 | 0.62 | -9.1% | -8.4% | 64% |
| 5y (60m) | 1.36% | 19.19% | -0.03 | -0.04 | -32.8% | -12.9% | 55% |
| 10y (120m) | 4.40% | 17.70% | 0.20 | 0.28 | -32.8% | -19.4% | 60% |
| since_1990 (441m) | 9.26% | 18.54% | 0.43 | 0.62 | -68.3% | -31.7% | 61% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| us_value | +0.82 | cash | -0.03 |
| us_large_cap | +0.77 | gold | +0.21 |
| hy_corporates | +0.77 | short_treasuries | +0.24 |

## 6. Valuation and fundamentals

_No valuation signal was emitted for this asset._

The judge's valuation assessment:

> Following key consideration 2, the build is dividend yield plus NOI growth, not GAAP earnings. I therefore give implied_erp_cape (7.42%) zero weight. It capitalises VNQ's GAAP earnings yield, which is net of depreciation on long-lived property, so it is structurally inapplicable rather than merely low-confidence. Its own rationale flags the understatement. The inverse_gordon candidate (7.68%) is the closest match to this asset's lens, so it carries the largest weight (0.40). It is built from a 3.75% dividend yield, -2.27% net issuance, 4.4% nominal growth, zero valuation drift and a 1.80% variance add-back. The negative buyback term is real per-share dilution, because the distribution requirement forces REITs to fund growth by issuing equity. Pairing net payout with aggregate GDP growth is therefore consistent and is not double-counting. The zero valuation-change term reflects the absence of a reliable long valuation anchor for REITs. I did not have current cap-rate or DFII10 levels in the inputs, so I take no explicit cap-rate-spread or NAV-discount view (considerations 3 and 5). Real yields well above their 2010s levels are a reason not to assume multiple expansion. Black-Litterman (7.77%) independently lands near Gordon, which supports this valuation-based anchor. The historical_erp (11.94%) reflects a different property mix: more office and regional retail, versus today's industrial, data centre and tower weight (consideration 4). It also reflects a secular fall in rates. I hold it at 0.15.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.0909 | +0.032 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0229 | -0.258 | price against its 10-month moving average |
| mean_reversion | +0.3283 | -0.096 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.0909 | +0.222 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite signal is essentially neutral (+0.02) and gives no reason to move away from the valuation anchor in either direction. Price sits below its 10-month moving average (trend -0.26), and the mean-reversion score is mildly negative (-0.10). These modestly undercut the high historical and regime candidates. Relative momentum against the other 17 classes is positive (+0.22), and financial conditions are supportive (+0.12), so I do not push the estimate to the bottom of the range. The 5-year (1.36%) and 10-year (4.40%) realised returns are far below the since-1990 9.26%. This confirms that the backward-looking candidates rest on an earlier, more favourable rate and sector environment. Macro alignment scores are near zero, consistent with the low-confidence regime. No fund-flow or positioning view is claimed, because none is sourced in this pipeline.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0031 | +0.110 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | +0.0952 | +0.005 | correlation with the growth score (+0.10) times its level today (+0.05) |
| inflation_alignment | +0.0374 | -0.010 | correlation with the inflation score (+0.04) times its level today (-0.27) |
| monetary_policy_alignment | +0.0540 | -0.012 | correlation with the monetary_policy score (+0.05) times its level today (-0.22) |
| financial_conditions_alignment | +0.3320 | +0.117 | correlation with the financial_conditions score (+0.33) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (18.99%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 11.94% | 0.50 | 15% | +7.91% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 11.40% | 0.40 | 20% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +7.02% a year (all months +8.28%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 7.77% | 0.40 | 25% | Equilibrium excess return +3.74% at a 4.3% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | 7.68% | 0.42 | 40% | 3.75% dividends -2.27% net buybacks + 2.1% real growth + 2.3% inflation +0.00% valuation change + 1.80% variance add-back (net payout from WRDS 2025-12, rolled forward by VNQ's price change; no long valuation history, drift 0). |
| `implied_erp_cape` | 7.42% | 0.21 | — | 3.31% real earnings yield (VNQ trailing earnings yield; REIT earnings are net of depreciation, so this understates) + 2.3% expected inflation + 1.80% variance add-back. |
| `survey_consensus` | — | — | — | unavailable: not applicable to real_assets |
| `yield_building_block` | — | — | — | unavailable: not applicable to real_assets |
| `auto_blend` | 9.54% | 0.41 | — | Confidence-weighted average of 5 methods: historical_erp 26%, regime_adjusted 21%, bl_equilibrium 21%, inverse_gordon 22%, implied_erp_cape 11%. |

## 10. The judgment

Selection: **custom blend** — `inverse_gordon` 40%, `bl_equilibrium` 25%, `regime_adjusted` 20%, `historical_erp` 15%. Final estimate 9.09%, inside the hard [7.42, 11.94] range Exhibit 4 requires.

> Final estimate: 9.09%, a custom blend of inverse_gordon 0.40, bl_equilibrium 0.25, regime_adjusted 0.20 and historical_erp 0.15. It sits inside the [7.42, 11.94] range and 0.45pp below the 9.54% auto-blend, between the paper's -0.2pp markdown and our prior -0.68pp. The main changes from the auto-blend are:
- I dropped implied_erp_cape entirely, because GAAP earnings are not a usable REIT valuation input (key consideration 2). Dropping it removes a low number, which raises the blend.
- I reweighted toward the dividend-plus-growth Gordon build, which is this asset's primary lens, and toward the equilibrium estimate that corroborates it.
- I cut historical_erp, whose 1990-2026 sample reflects falling rates and a superseded office and retail-heavy property mix (key consideration 4).

The estimate implies a Sharpe ratio of about 0.27 at 18.99% volatility. That is consistent with treating REITs as a levered real-asset equity with a 0.65 correlation to US large cap, not a bond substitute (key consideration 1). It sits sensibly below a broad-equity premium, given REITs' heavy rate sensitivity in a restrictive, sticky-inflation backdrop. Confidence is low. The regime call is low-confidence, the candidates differ by 4.5pp, and no direct cap-rate versus real-yield spread or NAV-discount input was available. Governing policy is config/ips.yaml, which is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 7.42% | the most pessimistic available candidate is `implied_erp_cape` at 7.42%, -1.67pp against the judged estimate. 3.31% real earnings yield (VNQ trailing earnings yield; REIT earnings are net of depreciation, so this understates) + 2.3% expected inflation + 1.80% variance add-back. |
| **base** | 9.09% | The judge's estimate, 9.09%, by custom blend across 6 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 11.94% | the most optimistic available candidate is `historical_erp` at 11.94%, +2.85pp against the judged estimate. +7.91% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **A levered real-asset equity, not a bond substitute.** Correlation of 0.65 with US large cap on our matrix. REITs are equities whose underlying assets happen to be buildings, and balance-sheet leverage amplifies both the rate sensitivity and the equity beta.
2. **Use FFO or AFFO, not GAAP earnings.** Depreciation on long-lived property makes reported earnings and therefore P/E and CAPE close to meaningless for this sector. Dividend yield plus net-operating-income growth is the right build, and the payout is constrained by the REIT distribution requirement.
3. **Cap rates trade against real yields,** which is why `DFII10` is in this asset's `cma_series`. The valuation question is the spread between property cap rates and the real 10-year yield, not the nominal level of rates.
4. **The property mix has changed fundamentally.** Weight has moved away from office and regional retail toward industrial, data centres and communication towers, so sector betas and yields estimated on the long history describe a different asset class from today's index. The paper's judge marked REITs down only -0.2%; ours marked them -0.68%.
5. **Public and private valuations diverge for long stretches.** Listed REITs reprice daily and can trade at a sustained discount or premium to appraised NAV. A discount is information about the forward return, and it is also a reason the listed series is more volatile than the underlying property.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `FRESX` (active_fund): 1986-12-31 to 1996-05-31, 114 months
- `VGSIX` (index_fund): 1996-06-30 to 2004-09-30, 100 months
- `VNQ` (etf): 2004-10-31 to 2026-09-30, 264 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

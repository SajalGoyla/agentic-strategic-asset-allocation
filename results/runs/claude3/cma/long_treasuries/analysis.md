# Long-Term Treasuries — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 5.98%** over 3 years, nominal, against expected volatility of 12.43%. Judge confidence **medium**, selection by **custom blend** (`yield_building_block` 80%, `bl_equilibrium` 20%). The 5 available candidates span 4.19%–8.23% (4.05pp), described as **moderate** dispersion.

## 2. The asset class

**Long-Term Treasuries** (fixed income), tracked by `TLT` against ICE US Treasury 20+ Year.

- **Macro sensitivity:** Growth (-), Rates (---), Inflation (---), Dollar (0)
- **Primary valuation lens:** the yield level (`DGS20`, `DGS30`) and the term premium
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> The stage-1 call is a fragile, late-cycle-adjacent expansion with sticky above-history inflation, held at low confidence (0.35) and with a 20-30% recession probability. For the longest-duration nominal asset in the universe the regime label matters less than which macro surprise arrives over three years. A deflationary growth shock would drive a large, convexity-boosted gain. A renewed inflation surprise, which the -0.27 inflation score warns of, would drive a large loss, since roughly 16-17 years of duration turns 100bp into about 16% of price. These two tails roughly offset, so the regime gives no clean directional tilt. I therefore do not lean on regime_adjusted. Its 8.23% comes from the three years after past expansion months, and those were overwhelmingly drawn from the 1990-2020 secular fall in yields, so it measures a tailwind that started from much higher yields and cannot repeat in the same form. Exhibit 4's late-cycle guidance points toward valuation-anchored methods, and for a bond that means the starting yield.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | -8.98% | 10.11% | -1.24 | -1.35 | -12.1% | -5.4% | 50% |
| 3y (36m) | -0.14% | 13.50% | -0.27 | -0.38 | -13.4% | -6.5% | 56% |
| 5y (60m) | -8.46% | 14.61% | -0.79 | -0.97 | -42.0% | -9.4% | 47% |
| 10y (120m) | -2.81% | 13.63% | -0.32 | -0.43 | -47.6% | -9.4% | 50% |
| since_1990 (441m) | 5.08% | 12.12% | 0.24 | 0.37 | -47.6% | -13.1% | 57% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| intermediate_treasuries | +0.93 | commodities | -0.31 |
| ig_corporates | +0.77 | cash | +0.08 |
| short_treasuries | +0.69 | us_value | +0.09 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| yield_level | +5.6400 | +0.794 | DGS30: starting yield against its own history: the dominant predictor of bond return |

The judge's valuation assessment:

> Valuation is the strongest input here. The 20-30 year yield averages 5.66%, and the DGS30 yield-level signal is +0.79 against its own history, which makes long Treasuries cheap by their own standards. The term-structure split is the key judgment (consideration 4). The starting yield sits about 1.6pp above the 4.03% T-bill. If the expected average short rate over the bonds' life is roughly 3.5-4%, the implied term premium is about +1.5-2%. That is high relative to the near-zero or negative estimates of the past decade, and it is what separates this sleeve from intermediate Treasuries. I assume only part of that premium is earned over the next three years. The 3-year horizon is far shorter than the bonds' duration, so the starting yield is a noisy predictor here: a modest further rise in yields from sticky inflation could absorb a year or more of carry. That is why I shade below the 6.43% building block rather than taking it whole. Credit loss is correctly zero, and the 0.77pp variance add-back converts the yield to the arithmetic convention. Cheap valuation also argues against the low end of the range: bl_equilibrium's +0.16% excess return is a CAPM artifact, because Treasuries hedge the equity-heavy ETF market portfolio. It is not a valuation view.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | -0.0352 | -0.277 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0711 | -0.562 | price against its 10-month moving average |
| mean_reversion | +0.0219 | +0.231 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | -0.0352 | -0.889 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The signals split cleanly by category. Valuation (yield_level +0.79) and mean reversion (+0.23, after a deeply negative 36-month run) support the yield-based estimate. Trend (-0.56), 12-1 momentum (-0.28) and relative momentum (-0.89, near the bottom of the 18 assets) say yields are still rising and the sleeve is losing ground. The macro alignment signals are essentially zero; the measured correlations with the dimension scores are tiny. The composite is +0.18, mildly bullish. I read this as confirming the direction of the building block, a positive expected excess return from a high starting yield. The adverse momentum justifies hedging the magnitude, which is why 20% goes to the lower equilibrium anchor. I do not set the estimate at the bottom of the range. No fund-flow or positioning view is claimed, because this pipeline does not source one.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0019 | +0.106 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.0160 | -0.001 | correlation with the growth score (-0.02) times its level today (+0.05) |
| inflation_alignment | +0.1346 | -0.036 | correlation with the inflation score (+0.13) times its level today (-0.27) |
| monetary_policy_alignment | +0.0179 | -0.004 | correlation with the monetary_policy score (+0.02) times its level today (-0.22) |
| financial_conditions_alignment | +0.0334 | +0.012 | correlation with the financial_conditions score (+0.03) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (12.43%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 6.98% | 0.30 | — | +2.95% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 8.23% | 0.25 | — | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +4.58% a year (all months +3.23%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 4.19% | 0.40 | 20% | Equilibrium excess return +0.16% at a 2.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to fixed_income |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 6.43% | 0.80 | 80% | 5.66% starting yield - 0.00% expected credit loss + 0.77% variance add-back (mean of DGS20, DGS30). |
| `auto_blend` | 6.27% | 0.54 | — | Confidence-weighted average of 4 methods: historical_erp 17%, regime_adjusted 14%, bl_equilibrium 23%, yield_building_block 46%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 80%, `bl_equilibrium` 20%. Final estimate 5.98%, inside the hard [4.19, 8.23] range Exhibit 4 requires.

> For a default-free bond, the starting yield is the strongest single predictor, so yield_building_block (6.43%, confidence 0.80) carries 80% of the weight. The other 20% goes to bl_equilibrium (4.19%). This is not because equilibrium is a good forecast for a hedge asset. It is a deliberate haircut for horizon mismatch: three years against roughly 16-17 years of duration leaves substantial mark-to-market risk if sticky inflation pushes yields higher, and price trend and momentum still point that way. The result is 0.8 x 6.43 + 0.2 x 4.19 = 5.98%. That is about 1.95pp over the 4.03% T-bill, which implies about a 1.5pp term premium earned, a Sharpe of about 0.16 at 12.43% volatility, and a value comfortably inside [4.19, 8.23]. I gave zero weight to historical_erp (6.98%) and regime_adjusted (8.23%). Both are built on 1990-2026 returns dominated by the secular decline in yields, and the 5- and 10-year windows of -8.5% and -2.8% a year show how regime-specific that history was. Auto_blend is excluded to avoid double-counting its components and to keep those history-based methods out. Two risks fall outside the point estimate. First, this 'safe' sleeve has suffered drawdowns near -48% (consideration 2), well beyond the -25% IPS limit, so position sizing must respect that. Second, convexity's asymmetric payoff in a deflationary shock (consideration 3) is real tail-hedge value that the covariance matrix does not capture. Governing policy is config/ips.yaml, which is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 4.19% | the most pessimistic available candidate is `bl_equilibrium` at 4.19%, -1.79pp against the judged estimate. Equilibrium excess return +0.16% at a 2.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| **base** | 5.98% | The judge's estimate, 5.98%, by custom blend across 5 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 8.23% | the most optimistic available candidate is `regime_adjusted` at 8.23%, +2.25pp against the judged estimate. After the 155 past months labelled expansion, excess returns over the next 3 years averaged +4.58% a year (all months +3.23%); credibility weight 0.72, plus 4.03% T-bill. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **The most rate-sensitive asset in the universe.** Duration around sixteen to seventeen years, so a 100bp move in yields is worth roughly 16% of price. Nothing else here responds to rates on that scale.
2. **A 'safe' asset with equity-like drawdown.** The 2020-2023 decline exceeded 45% peak to trough, deeper than most equity sleeves suffered in the same window. Any narrative calling this a defensive holding has to address that, and the -25% IPS drawdown limit applies to portfolios holding it.
3. **Convexity makes the response asymmetric.** For large yield moves the price gain from falling yields exceeds the loss from an equal rise. That is a genuine positive for a tail hedge and it is invisible to a covariance matrix, which sees only symmetric variance.
4. **The term premium is the judgement call.** Expected return decomposes into the expected average short rate plus a term premium, and estimates of that premium have been near zero or negative for much of the past decade. Say what you assume for it; it is the difference between this sleeve and intermediate Treasuries.
5. **A poor inflation hedge and a good deflation hedge.** The longest nominal duration means the largest loss if inflation surprises upward, and the largest gain in a deflationary growth shock. It is a bet on the direction of that surprise.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `crsp:mcti[b20ret/b30ret]` (index): 1980-01-31 to 2002-07-31, 271 months
- `TLT` (etf): 2002-08-31 to 2026-09-30, 290 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

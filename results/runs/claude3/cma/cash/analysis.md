# Cash — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 3.62%** over 3 years, nominal, against expected volatility of 0.62%. Judge confidence **medium_high**, selection by **custom blend** (`yield_building_block` 60%, `survey_consensus` 40%). The 6 available candidates span 3.00%–4.03% (1.03pp), described as **tight** dispersion.

## 2. The asset class

**Cash** (cash), tracked by `BIL` against Bloomberg 1-3 Month US Treasury Bill.

- **Macro sensitivity:** Growth (0), Rates (+), Inflation (0), Dollar (0)
- **Primary valuation lens:** the policy path: `DTB3`, `DGS1MO` and `DFF`
- **Return history from** 1980-01-31 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> For cash the regime matters only through the expected policy-rate path over the next three years; there is no premium to tilt. The stage-1 view is a fragile, late-cycle-adjacent expansion, classified at low confidence (0.35), with a 20-30% recession probability. Inflation is sticky and above its history, and the monetary-policy score is mildly negative (-0.22). This skews the 3-year path asymmetrically. Sticky inflation limits how far and how fast the Fed can cut in the base case. If the fragile expansion breaks, though, cuts would be fast and deep and would pull the average bill rate well below today's 4.03%. Quoting the spot yield for three years implicitly assumes no cuts at all, and that is the tail the regime view makes least likely. The regime_adjusted candidate does not capture this. Its -0.10% regime excess return is just the spot bill rate restated, because cash's excess return over T-bills is roughly zero by construction.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 3.66% | 0.10% | -0.85 | -1.07 | 0.0% | 0.3% | 100% |
| 3y (36m) | 4.45% | 0.21% | -0.27 | -0.37 | 0.0% | 0.3% | 100% |
| 5y (60m) | 3.65% | 0.51% | -1.28 | -1.33 | -0.1% | -0.0% | 90% |
| 10y (120m) | 2.30% | 0.56% | -1.41 | -1.49 | -0.2% | -0.0% | 82% |
| since_1990 (441m) | 2.67% | 0.65% | -0.75 | -0.96 | -0.4% | -0.2% | 78% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| short_treasuries | +0.35 | commodities | -0.15 |
| gold | +0.18 | us_small_cap | -0.06 |
| intermediate_treasuries | +0.12 | us_value | -0.04 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| yield_level | +4.0300 | +0.572 | DTB3: starting yield against its own history: the dominant predictor of bond return |

The judge's valuation assessment:

> The valuation lens for cash is the policy path (DTB3, DGS1MO, DFF), and the build-up is the expected average overnight rate over the horizon (Key consideration 2). The starting DTB3 of 4.03% is high against its own history, which the yield_level signal of +0.57 reflects. The SPF median BILL10 of 3.00% is the professional consensus for the average bill rate over ten years, so it embeds an eventual decline toward a neutral rate. Three of the five available candidates add essentially no information. historical_erp and regime_adjusted (-0.10pp excess) and bl_equilibrium (+0.00pp at a 2.8% weight) all reduce to the same 4.03% T-bill plus a near-zero term. They are one input counted three times, so I gave them zero weight rather than let the auto-blend triple-count the spot rate. auto_blend is also unweighted because its inputs are already represented directly. The remaining disagreement is between 4.03% spot and the 3.00% ten-year survey. This is a horizon mismatch rather than a data problem, and the 3-year average should sit between them, closer to spot because the early years of the path are anchored near today's rate. No forward curve is supplied to this stage, so I do not claim a market-implied path. The 60/40 weighting is a judgment of where a gradual glide from 4.03% toward a roughly 3.0-3.25% neutral rate averages over 36 months.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.0332 | +0.497 | 11-month return skipping the last 1, vs. its own history |
| trend | +0.0132 | +0.480 | price against its 10-month moving average |
| mean_reversion | +0.1311 | -0.726 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.0332 | -0.222 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite of +0.24 is mostly an artefact of how bill returns accrue rather than a directional view. Momentum (+0.50), trend (+0.48) and mean reversion (-0.73) reflect three years of unusually high carry (4.45% trailing 3-year return). A T-bill does not mean-revert in price; its income resets with policy. The meaningful signals are macro. Monetary-policy alignment (+0.14) and inflation alignment (+0.06) say sticky inflation and a not-yet-easy policy stance support near-term bill income, which argues against cutting the estimate toward the survey too aggressively. Regime_fit (-0.28) says bill returns in past expansion months ran below the unconditional mean, consistent with rates drifting lower over a multi-year window. Together they support an estimate below spot but well above the 10-year consensus, which is where 3.62% sits. Fund-flow or positioning signals are not available to this pipeline, and I make no claim about them.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | -0.0003 | -0.280 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | -0.3837 | -0.020 | correlation with the growth score (-0.38) times its level today (+0.05) |
| inflation_alignment | -0.2293 | +0.062 | correlation with the inflation score (-0.23) times its level today (-0.27) |
| monetary_policy_alignment | -0.6323 | +0.137 | correlation with the monetary_policy score (-0.63) times its level today (-0.22) |
| financial_conditions_alignment | +0.1761 | +0.062 | correlation with the financial_conditions score (+0.18) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (0.62%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 3.93% | 0.30 | — | -0.10% mean excess return over T-bills across 441 months since 1990-01, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 3.93% | 0.25 | — | After the 155 past months labelled expansion, excess returns over the next 3 years averaged -0.10% a year (all months -0.09%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 4.03% | 0.40 | — | Equilibrium excess return +0.00% at a 2.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to cash |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to cash |
| `survey_consensus` | 3.00% | 0.50 | 40% | SPF median BILL10 3.00% a year over 10 years + 0.00% variance add-back. |
| `yield_building_block` | 4.03% | 0.80 | 60% | 4.03% starting yield - 0.00% expected credit loss + 0.00% variance add-back (mean of DTB3). |
| `auto_blend` | 3.78% | 0.53 | — | Confidence-weighted average of 5 methods: historical_erp 13%, regime_adjusted 11%, bl_equilibrium 18%, survey_consensus 22%, yield_building_block 36%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 60%, `survey_consensus` 40%. Final estimate 3.62%, inside the hard [3.00, 4.03] range Exhibit 4 requires.

> I chose a custom blend of 60% yield_building_block (4.03%) and 40% survey_consensus (3.00%), giving 3.62%, inside the [3.00, 4.03] range. The governing IPS (config/ips.yaml) is ratified. The starting yield is the strongest single anchor for a bill, but the agent file is explicit that a 3-year CMA must average the expected path rather than quote today's yield. The ten-year SPF bill forecast supplies the direction and approximate destination of that path, and the 60/40 split reflects that the early part of the horizon stays near spot. The historical, regime and Black-Litterman candidates are excluded because each is the 4.03% spot rate plus a near-zero excess term, so they would repeat the spot input rather than add evidence. The 0.41pp shortfall versus the auto-blend's 3.78% comes from removing that duplication. This number matters well beyond cash. Under decision 38 it becomes the risk-free rate in every Sharpe ratio, so a lower cash CMA modestly raises every risky asset's implied Sharpe ratio and keeps cash from appearing strictly dominated. The negative historical Sharpe ratios in the stats table reflect exactly the mismatch that decision fixes. Cash's 0.62% volatility remains the universe floor, so variance-minimising methods will gravitate to it absent IPS floors; that follows from its risk, not from this CMA. A 3.62% nominal return minus sticky above-target inflation falls well short of the CPI + 3% objective, so a cash-heavy portfolio cannot meet the IPS. That is a true property of the asset, which earns its place as the funding and liquidity account and for optionality rather than return. Confidence is medium-high: the asset is near-mechanical, but the low-confidence regime call makes the policy path, and therefore the 3-year average, the main source of uncertainty.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 3.00% | the most pessimistic available candidate is `survey_consensus` at 3.00%, -0.62pp against the judged estimate. SPF median BILL10 3.00% a year over 10 years + 0.00% variance add-back. |
| **base** | 3.62% | The judge's estimate, 3.62%, by custom blend across 6 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 4.03% | the most optimistic available candidate is `bl_equilibrium` at 4.03%, +0.41pp against the judged estimate. Equilibrium excess return +0.00% at a 2.8% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **This asset's CMA *is* the risk-free rate the whole pipeline uses.** Decision 38 sets the Sharpe-ratio denominator's risk-free rate to this asset's own judged CMA, because cash is the risk-free asset of this universe. Two different numbers for one thing gave cash a negative Sharpe and made every return-optimised method treat it as strictly dominated. Your estimate therefore reprices the risk-adjusted ranking of all eighteen assets - the most consequential CMA in the set, and the one least likely to look that way.
2. **The build-up is the expected average overnight rate, not a premium over anything.** There is no risk premium to estimate. The forward curve and the macro agent's monetary-policy score are the inputs, and the horizon matters: a 3-year CMA has to average the expected path, not quote today's bill yield.
3. **It sets the volatility floor of the universe at 0.62%,** about a thirty-sixth of emerging markets'. That is why every variance-minimising PC method converges on it when the IPS sets no asset-class floors, and why four of our candidates hold 62-92% cash. The CMA is not the cause, but your rationale is the right place to note the consequence.
4. **It fails the IPS return objective by construction.** A bill yield minus expected inflation does not clear CPI + 3% in any ordinary state, so a portfolio that holds much of it cannot meet the objective. That is a true statement about the asset, not a defect in it.
5. **It is the funding and liquidity account, not a return-seeking holding.** The honest case for cash is optionality and the ability to meet obligations without selling, neither of which appears in an expected-return number.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `crsp:mcti[t30ret]` (index): 1980-01-31 to 2007-05-31, 329 months
- `BIL` (etf): 2007-06-30 to 2026-09-30, 232 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

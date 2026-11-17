# USD Emerging Market Debt — investment case

_13-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). Horizon 3 years, nominal. Section contents are our reconstruction; the paper names the report without listing its sections._

## 1. Recommendation

**Expected return 6.96%** over 3 years, nominal, against expected volatility of 13.99%. Judge confidence **medium**, selection by **custom blend** (`yield_building_block` 65%, `bl_equilibrium` 20%, `regime_adjusted` 15%). The 5 available candidates span 6.45%–10.33% (3.88pp), described as **moderate** dispersion.

## 2. The asset class

**USD Emerging Market Debt** (fixed income), tracked by `EMB` against J.P. Morgan EMBI Global Core.

- **Macro sensitivity:** Growth (+), Rates (--), Inflation (-), Dollar (-)
- **Primary valuation lens:** the yield level (`DGS10`) and an EM corporate spread (`BAMLEMCBPIEY`)
- **Return history from** 1993-06-30 to 2026-09-30

## 3. Macro view

**Expansion** — fragile, late-cycle-adjacent expansion with sticky above-history inflation. Confidence low (0.35); recession probability 20–30%. Dimension scores: growth +0.053 · inflation -0.270 · monetary_policy -0.217 · financial_conditions +0.353.

The judge's reading of what that implies for this asset:

> Stage 1 reads a fragile, late-cycle-adjacent expansion at low confidence (0.35), with recession odds of 20-30%. For EM sovereign debt that calls for caution on spread capture rather than extrapolation. In late cycle Exhibit 4 tilts toward valuation and regime-adjusted methods, and for a bond the valuation method is the starting yield, so yield_building_block anchors the estimate. I kept a 15% weight on regime_adjusted (9.74%) to recognise that expansions have historically favoured EM credit carry. Per Key consideration 4 I capped it there: the history begins in June 1993, so the expansion sample is only 155 months, and the series still contains post-Brady spread compression. The negative inflation (-0.27) and monetary-policy (-0.22) scores argue against expecting further Treasury-yield declines to add to returns over three years. Dollar sensitivity (Key consideration 1) reaches this asset through issuer funding stress and spreads, not FX translation. A late-cycle dollar spike is the main left-tail path, and it is one reason not to lean on the higher historical figures.

## 4. Return and risk history

| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1y (12m) | 0.43% | 6.85% | -0.44 | -0.52 | -4.6% | -3.7% | 75% |
| 3y (36m) | 8.81% | 7.36% | 0.59 | 0.93 | -4.6% | -3.7% | 69% |
| 5y (60m) | 1.19% | 10.36% | -0.20 | -0.27 | -25.1% | -6.7% | 58% |
| 10y (120m) | 2.27% | 10.14% | 0.04 | 0.05 | -26.7% | -15.0% | 60% |
| since_1990 (400m) | 8.01% | 14.01% | 0.45 | 0.60 | -39.6% | -35.9% | 68% |

## 5. Correlations and portfolio role

Over the 10y window, against the other 17 asset classes:

| Most correlated | | Least correlated | |
|---|---:|---|---:|
| ig_corporates | +0.87 | cash | +0.10 |
| hy_corporates | +0.84 | commodities | +0.23 |
| intl_corporates | +0.84 | short_treasuries | +0.37 |

## 6. Valuation and fundamentals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| yield_level | +5.2900 | +0.797 | DGS10: starting yield against its own history: the dominant predictor of bond return |

The judge's valuation assessment:

> The starting yield of 6.47% is the strongest predictor at a 3-year horizon, which is short of the asset's roughly 7-year duration but still yield-dominated. The yield_level signal (+0.80, DGS10 against its own history) says the rate leg is starting from an attractive level. Taking the two legs separately (Key consideration 3): the Treasury leg supplies most of the carry and carries duration risk if yields rise. The spread leg is the excess of 6.47% over Treasuries, from which the method subtracts a 1.00% expected credit loss. Two caveats temper the yield candidate. First, it uses the ICE EM corporate yield (BAMLEMCBPIEY) as a proxy, because no free sovereign EMBI yield exists, and EMB holds sovereigns. Second, the 1.00% loss is a corporate-style default-times-recovery haircut, which transfers poorly to negotiated sovereign restructurings (Key consideration 2). I did not adjust the loss further or deduct credit risk again, because the spread already prices it. I relied on the EM corporate series in the CMA method, not the US IG proxy that the signal layer uses (Key consideration 5). The historical_erp figure of 10.33% reflects 1993-2026, when spreads were far wider at the start and both spreads and Treasury yields fell secularly. Those starting conditions do not repeat today, so I gave that method zero weight.

## 7. Technical signals

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| momentum_12_1 | +0.0437 | -0.039 | 11-month return skipping the last 1, vs. its own history |
| trend | -0.0281 | -0.472 | price against its 10-month moving average |
| mean_reversion | +0.2622 | -0.311 | 36-month return, inverted: a stretched run tends to revert |
| relative_momentum | +0.0437 | +0.000 | momentum rank against the other 17 asset classes |

The judge on how the signals line up against the methods:

> The composite is mildly positive (+0.26), but almost all of it comes from the valuation yield signal, which supports anchoring on the starting yield rather than chasing a higher number. The technicals lean the other way. Trend is -0.47 (price below its 10-month average) and mean reversion is -0.31 after a strong 3-year run of 8.81%. Momentum is flat. Together these argue against weighting the backward-looking historical and regime figures heavily. Macro alignments are near zero. Financial-conditions alignment is modestly positive (+0.11), but it is measured partly through the US IG spread proxy, so I treat it as weak confirmation. Net, the signals confirm a yield-anchored estimate with no case for an upward tilt.

## 8. Macro sensitivity and regime fit

| Signal | Value | Score | Reading |
|---|---:|---:|---|
| regime_fit | +0.0008 | +0.042 | mean return in 160 past 'expansion' months vs. its unconditional mean |
| growth_alignment | +0.0067 | +0.000 | correlation with the growth score (+0.01) times its level today (+0.05) |
| inflation_alignment | +0.1405 | -0.038 | correlation with the inflation score (+0.14) times its level today (-0.27) |
| monetary_policy_alignment | -0.0459 | +0.010 | correlation with the monetary_policy score (-0.05) times its level today (-0.22) |
| financial_conditions_alignment | +0.3164 | +0.112 | correlation with the financial_conditions score (+0.32) times its level today (+0.35) |

_`by_regime` is empty in this run: the historical-analysis skill fills it only when a regime history is supplied, so the measured dimension alignments above are the whole of the regime evidence for this asset._

## 9. Capital market assumption: the candidates

Eight candidates are computed by script with no model involved (§3.3). Volatility (13.99%) comes from the covariance matrix, not from a candidate.

| Method | Estimate | Confidence | Judge weight | Note |
|---|---:|---:|---:|---|
| `historical_erp` | 10.33% | 0.30 | — | +6.30% mean excess return over T-bills across 400 months since 1993-06, plus the 4.03% T-bill yield. |
| `regime_adjusted` | 9.74% | 0.25 | 15% | After the 155 past months labelled expansion, excess returns over the next 3 years averaged +5.46% a year (all months +6.37%); credibility weight 0.72, plus 4.03% T-bill. |
| `bl_equilibrium` | 6.55% | 0.40 | 20% | Equilibrium excess return +2.52% at a 0.9% market weight and risk aversion 2.50, plus 4.03% T-bill. Weights are ETF sizes (fund snapshot AUM, 2026-10-01), a proxy for asset-class size. |
| `inverse_gordon` | — | — | — | unavailable: not applicable to fixed_income |
| `implied_erp_cape` | — | — | — | unavailable: not applicable to fixed_income |
| `survey_consensus` | — | — | — | unavailable: no public consensus forecast for this asset; the judge may use the macro agent's view instead (the paper's alternative) |
| `yield_building_block` | 6.45% | 0.56 | 65% | 6.47% starting yield - 1.00% expected credit loss + 0.98% variance add-back (mean of BAMLEMCBPIEY; proxy yield). |
| `auto_blend` | 7.79% | 0.41 | — | Confidence-weighted average of 4 methods: historical_erp 20%, regime_adjusted 17%, bl_equilibrium 26%, yield_building_block 37%. |

## 10. The judgment

Selection: **custom blend** — `yield_building_block` 65%, `bl_equilibrium` 20%, `regime_adjusted` 15%. Final estimate 6.96%, inside the hard [6.45, 10.33] range Exhibit 4 requires.

> Final estimate 6.96% from a custom blend: 65% yield_building_block (6.45%), 20% bl_equilibrium (6.55%) and 15% regime_adjusted (9.74%). For fixed income the starting-yield builder is the strongest candidate, and I depart from it only slightly, for one stated reason. Its input is an EM corporate proxy with a corporate-style credit-loss haircut, while sovereign recoveries are bargained, so I add a small regime-conditional carry component. That component acknowledges sovereign spreads that may differ from the corporate proxy and the expansion backdrop. Black-Litterman (6.55%) independently corroborates the yield anchor and is given 20%. historical_erp (10.33%) gets zero weight because it embeds post-Brady spread compression and three decades of falling yields. I preferred this blend to the auto-blend (7.79%), which weights by stated confidence alone and so gives 37% combined to the two backward-looking methods. That is too much in a fragile late-cycle regime with weak technicals and dollar-driven spread risk. The estimate sits inside the [6.45, 10.33] range. Against 13.99% volatility and a 4.03% T-bill it implies a modest Sharpe of about 0.21, consistent with a credit-plus-duration asset whose drawdowns (-39.6% worst, -25% in the last five years) are equity-like. Confidence is medium: the yield anchor is sound, but the proxy yield and thin history limit precision. Governing policy is config/ips.yaml, which is ratified.

## 11. Scenarios

| Scenario | Return | Derivation |
|---|---:|---|
| **bear** | 6.45% | the most pessimistic available candidate is `yield_building_block` at 6.45%, -0.51pp against the judged estimate. 6.47% starting yield - 1.00% expected credit loss + 0.98% variance add-back (mean of BAMLEMCBPIEY; proxy yield). |
| **base** | 6.96% | The judge's estimate, 6.96%, by custom blend across 5 available candidates. This is the recommendation and the number every downstream agent consumes. |
| **bull** | 10.33% | the most optimistic available candidate is `historical_erp` at 10.33%, +3.37pp against the judged estimate. +6.30% mean excess return over T-bills across 400 months since 1993-06, plus the 4.03% T-bill yield. |

## 12. Key risks and what would invalidate the view

From this asset's own description file — the asset-class-specific instructions of Exhibit 3, which the judge was given before deciding:

1. **Dollar-denominated, so no direct currency translation - but strong indirect dollar sensitivity.** A strong dollar tightens the funding conditions of the issuers themselves, so the credit risk rises exactly when the currency would have hurt a local-currency index. The exposure is real; it just arrives through spreads rather than through FX.
2. **Sovereign credit is a political event, not a statistical one.** Defaults are negotiated restructurings with recoveries set by bargaining, so a default-rate-times-recovery calculation borrowed from corporate credit transfers poorly.
3. **It carries both US rate risk and spread risk.** Duration near seven years, so a Treasury selloff hits it alongside any spread widening. Separate the two legs in your rationale.
4. **The shortest history in the universe.** June 1993, which is 1993 onward only - no pre-Brady-era data, and the regime-conditional and backtest evidence for this asset is correspondingly thinner than for the Treasury sleeves. Weight the regime-adjusted method accordingly.
5. **Our spread signal is proxied.** FRED's EM corporate OAS has only a few years of history, so `config/signals.yaml` substitutes the US IG spread for the signal layer. The CMA methods use the EM series where it reaches; say which you relied on.

The `cma` contract carries no free-text notes field, so anything the judge wanted to flag beyond these appears in section 10's rationale.

## 13. Provenance and limitations

Return history is spliced from the longest-lived proxies backwards from the ETF (decision 3):

- `FNMIX` (active_fund): 1993-06-30 to 2007-12-31, 175 months
- `EMB` (etf): 2008-01-31 to 2026-09-30, 225 months

**Known limitations of this case.**

- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a runtime web search; this pipeline reads data only through `DataStore` (decision 26), so the category is omitted rather than proxied.
- **The scenario range is methodological disagreement, not a stress test.** Tail risk is computed at the portfolio level by the CRO.
- **Expected volatility is the covariance matrix's**, estimated over the full history with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.
- **The governing IPS (v0.2) is ratified.**

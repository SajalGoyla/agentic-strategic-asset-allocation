# Board memo — strategic asset allocation

Run `claude2`, as of 2026-10-01. Recommended by the CIO agent; ensemble
**composite score**.

## Recommendation
Adopt the composite-score blend as the recommended allocation. It combines the portfolios proposed by 14 of the 15 candidate investment methods, giving more weight to those that scored better on return, risk, IPS compliance and robustness.

We chose a blend over the single best-scoring method because our economic outlook is uncertain this quarter. Spreading the decision across many methods reduces the chance that one method's error drives the result.

The raw blend was slightly too conservative for the policy's minimum risk level. It was adjusted by moving about 13.5% of the portfolio to bring it into compliance.

## Expected performance against the benchmark
Expected annual return is about 6.9% with expected volatility of 8.0%, an expected return-to-risk (Sharpe) ratio of 0.39. In a historical test since 1993, rebalanced quarterly, the risk-adjusted return was 0.64 and the worst peak-to-trough loss was -23.2%, inside the -25% policy limit.

The portfolio is expected to deviate from the 60% US stocks / 30% Treasuries / 10% corporate bonds benchmark by about 3.6% a year (tracking error), well inside the 6% allowed.

It holds less in US large-cap stocks than the benchmark and spreads money across more asset types: value stocks, gold, cash, short-term bonds and international assets. In a strong, narrow US stock rally it would probably lag the benchmark. In a broad sell-off or a period of mixed markets it should hold up better. These are estimates, not promises.

## Macro rationale
Our macro analysis judges the economy to be in expansion, but with low confidence: 0.36 on a 0-1 scale, below the 0.4 level at which the policy requires us to tell you. Expansion normally favours growth assets such as stocks and credit. Low confidence argues against a concentrated bet on that view.

The recommended blend therefore keeps meaningful exposure to stocks while holding diversifiers (gold, cash, short- and long-term government bonds) that tend to help if the outlook turns out wrong.

## Largest positions
The largest positions are each about 10% of the portfolio:
- cash
- US large-cap stocks
- US value stocks
The rest is spread across many asset classes, equivalent to about 14.5 equally sized holdings, including government bonds of several maturities, gold, international and emerging-market assets, and corporate bonds.

The single largest contributing method is the resampled efficient frontier, at about 18% of the blend.

## Changes since the last review
This is the first recommendation produced under the current process and the draft IPS v0.2. No previously approved allocation was provided for comparison, so there are no position-by-position changes to report.

Within this review cycle, the five shortlisted methods revised their proposals after peer review, and those revised versions are what the blend uses.

## Key risks to monitor
- Low confidence in the economic outlook (0.36). If the expansion call is wrong, the return assumptions behind every method are wrong too.
- Stocks and bonds falling together, as in 2022. Several building blocks rely on bonds cushioning stock losses.
- Drawdown headroom is limited. The historical worst loss of -23.2% is under 2 points from the -25% limit. The test period starts in 1993, so it excludes the 1970s inflation shock and probably understates the risk.
- The portfolio sits exactly at the 8% minimum volatility. Small market changes could push it out of the band and require a trade to restore compliance.
- About 13.5% of the portfolio was moved to meet the policy minimum risk. This adjustment added risk the methods themselves did not choose.
- Some building blocks have known weaknesses. Reviewers found technical errors in two of the top-ranked methods, Black-Litterman and the resampled frontier. Some smaller ingredients breach the policy on their own, even though the blend does not.
- Lagging the benchmark in a strong US large-cap stock rally, because the portfolio holds less US large-cap stock than the benchmark.

## Rebalancing plan
Rebalance quarterly, as the IPS requires. At each quarter-end we will:
1. Refresh the economic outlook and return assumptions.
2. Recompute the blend.
3. Confirm it still meets every IPS limit: return, the 8-12% volatility band, the 25% drawdown limit, the 6% tracking-error budget, and the long-only, no-leverage rule.
4. Trade back to the target weights.

We will report to the board between quarters if any of these happen:
- the portfolio's loss from peak passes -20%
- volatility drifts outside 8-12%
- the economic regime is reclassified
- stocks and bonds begin moving together persistently

The allocation will also be reviewed if the adjustment needed for compliance grows above 20% of the portfolio.

## IPS compliance
The governing Investment Policy Statement is v0.2 and is still a DRAFT. It has not been finally approved, and its limits may change.

The recommended allocation complies with every hard limit in the draft:
- expected real return at or above CPI + 3%
- ex-ante volatility of 8.00%, within the 8% floor to 12% ceiling band
- historical maximum drawdown of -23.2%, better than the -25% limit
- tracking error of 3.64% against the 60/30/10 benchmark, within the 6% budget
- long only, with no leverage and no derivatives

Compliance was reached after adjusting the raw blend, which moved 13.5% of the portfolio to lift its volatility from 6.72% to the 8% floor.

One escalation rule is triggered: the macro agent's regime confidence is 0.36, below the 0.4 threshold, so it is flagged here for the board. All return assumptions inherit that uncertainty.

The chosen allocation's composite score is 0.787, above the 0.3 threshold, so the low-composite escalation is not triggered. At least one candidate portfolio cleared every hard limit after revision, so no unresolved hard violation requires human escalation.

## What would make this recommendation wrong
- The macro agent reclassifies the regime away from expansion (to late-cycle, slowdown or recession), or its confidence falls below 0.25. Either would undermine the CMAs that drive the composite weights; re-run the selection.
- Ex-ante volatility falls below 8.0% at any quarterly rebalance, or rises above 12.0%. The allocation currently sits exactly at the floor.
- Realised peak-to-trough drawdown exceeds -20%. That is an early warning against the -25% hard limit, given only 1.8 points of backtest headroom; review immediately.
- The rolling 12-month correlation of US large-cap equity and intermediate Treasury returns turns positive above +0.3. Several ingredients, including Black-Litterman and CVaR minimisation, rely on bonds cushioning equity losses.
- The CMA equity risk premium (US large cap or US value) is revised down by 1.0 percentage point or more. So is invalidation if the intermediate or long Treasury CMA moves by 0.75 points or more.
- Ex-ante tracking error to the 60/30/10 benchmark rises above 5.0%, or expected real return falls within 0.5 points of the CPI + 3% floor.
- At the next rebalance the projection needed to bring the ensemble into compliance exceeds 20% of the portfolio. At that point the allocation is mostly the IPS adjustment, not the candidates' judgment.
- A post-revision drawdown re-check of Black-Litterman, CVaR minimisation or pc_researcher shows a breach of -25%.
- The final, non-draft IPS changes the volatility band, drawdown limit or tracking-error budget.

## Escalations under the IPS
- regime_confidence_below: the macro agent's regime confidence is 0.36, below 0.4; action: flag_in_board_memo. Macro agent's regime confidence is low; downstream CMAs inherit that uncertainty.

## Dissenting views
- Meta-optimisation offers a higher Sharpe (0.41 ex-ante, 0.69 backtest), the lowest tracking error (2.78%), the shallowest drawdown (-23.1%) and needed no projection. A reasonable CIO could prefer it. I declined because it is effectively a single Black-Litterman bet in a low-confidence regime, resting on a candidate with an unverified post-revision drawdown and a reviewer-identified technical error.
- Single-method resampled efficient frontier has the highest composite (0.802) and needs no projection. I declined because its drawdown headroom is under 1 point and a reviewer found its objective mislabelled (a gamma-utility rather than a tangency portfolio). It is also the largest single share of my chosen ensemble at about 18%, so part of that weakness carries through.
- Black-Litterman reviewers found the claimed volatility-sensitive shrinkage is in practice close to a uniform 50/50 blend. Black-Litterman is a material ingredient of the composite ensemble, so its claimed robustness should be discounted.
- pc_researcher, ranked 3rd in the vote, still breaches the volatility floor ex-ante after revision (6.71%). Reviewers found its delivered portfolio contradicts its stated case. It enters the ensemble at a modest weight, which contributes to the need for projection.
- Several ingredients breach the IPS on their own:
- equal_weight (-26.7%) and volatility_targeting (-28.1%) breach the drawdown limit.
- market_cap_weight, bottom-flagged on 9 of 15 ballots, has a -40.6% drawdown.
- Several cash-heavy risk-structured portfolios breach the return, volatility and tracking-error limits.
The composite weighting gives these low weights, but they are present. Their low-volatility members are why the raw blend sat below the 8% floor.
- The 13.5% projection is a policy-driven adjustment, not a candidate's judgment. A trustee could reasonably ask whether a volatility floor is forcing risk the agents would not themselves have taken. This matters more because the IPS is still a draft.

## The allocation
| asset | weight |
|---|---|
| cash | 10.4% |
| us_large_cap | 10.3% |
| us_value | 10.2% |
| intermediate_treasuries | 9.9% |
| gold | 8.3% |
| short_treasuries | 8.0% |
| long_treasuries | 7.9% |
| us_growth | 6.9% |
| us_small_cap | 6.2% |
| emerging_markets | 5.4% |
| usd_em_debt | 4.7% |
| reits | 2.7% |
| intl_developed | 2.3% |
| intl_corporates | 2.0% |
| ig_corporates | 1.9% |
| intl_sovereigns | 1.1% |
| hy_corporates | 1.0% |
| commodities | 0.9% |

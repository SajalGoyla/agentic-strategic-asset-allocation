# Board memo — strategic asset allocation

Run `claude3`, as of 2026-10-01. Recommended by the CIO agent; ensemble
**composite score**.

## Recommendation
Adopt the composite-score blend of the committee's candidate portfolios as the Fund's strategic allocation for the coming quarter. The blend combines 13 of the 15 independently built portfolios. Each is weighted by how well it scored with the reviewers, the risk officer and the committee vote, so the best-reviewed portfolios count most. No single approach dominates: the largest, the vote winner, makes up 15% of the blend.

## Expected performance against the benchmark
The blend has an expected annual return of about 6.7%, with expected volatility of 8.0%, at the bottom of the IPS 8-12% band. The benchmark is 60% US large-cap equity, 30% intermediate Treasuries and 10% investment-grade corporates. Expected tracking error to it is 3.8%, so in a typical year the Fund's return could differ from the benchmark's by roughly ±4 percentage points. The Fund carries less equity than the benchmark, so it should lag in strong stock rallies and lose less in sharp equity sell-offs. Over the historical test (quarterly rebalancing since 1993) the worst peak-to-trough loss was -23.3%, inside the -25% limit, with a risk-adjusted return (Sharpe ratio) of 0.63.

## Macro rationale
The macro team judges the economy to be in expansion, but with low confidence (0.35). That is low enough to trigger a policy flag. Expansion normally rewards equity and credit risk. Because the call is uncertain, we chose a blend that spreads exposure across many independent methods and asset classes. We did not choose the higher-scoring but concentrated option, which leaned heavily on one forecast about value stocks. We keep meaningful equity for growth, Treasuries as ballast, and real assets and credit for breadth.

## Largest positions
The largest holdings are intermediate-term US Treasuries (about 16%), US large-cap equity (about 14%) and long-term US Treasuries (about 8%). The rest is spread across US value, small-cap and international equity, investment-grade and high-yield credit, international bonds, real estate, gold and commodities. The portfolio's diversity is equivalent to about 15 equally weighted assets. No single position is large enough to drive results alone.

## Changes since the last review
This is the first recommendation made under the ratified IPS v0.2, and no prior allocation is recorded in this run. Compared with a straightforward average of the candidates, the blend was adjusted before submission. The raw mix was slightly too cautious, with 7.4% volatility, under the 8% IPS minimum. About 11% of the blend's weight therefore moved toward the more equity-heavy candidates and away from the two most bond- and cash-heavy ones. This changed roughly 5.6% of the actual holdings. The adjustment raised expected risk to the policy minimum and reduced the cushion against the drawdown limit from about 4 points to about 1.7 points.

## Key risks to monitor
- Stocks and bonds falling together, as in 2022 or the 1970s. Several building blocks rely on Treasuries cushioning equity losses, and this is the scenario most likely to push losses toward the -25% limit.
- Thin drawdown cushion. The historical worst loss of -23.3% leaves only about 1.7 points before the -25% hard limit.
- Sitting at the volatility floor. Expected volatility is exactly 8.0%, so a calmer market estimate could put the portfolio below the IPS minimum at the next rebalance.
- Credit spread widening. High-yield, international and emerging-market debt sleeves tend to fall together in a credit shock.
- Uncertain regime call. The macro team's confidence is 0.35, so the forecasts the portfolio relies on carry extra uncertainty.
- Lagging a strong equity rally, since the portfolio holds less equity than the 60/30/10 benchmark.

## Rebalancing plan
Rebalance quarterly, as the IPS requires. At each quarter-end the team will:
1. Re-estimate the forecasts and risk model.
2. Re-run the candidate portfolios and the blend.
3. Confirm that expected volatility is within 8-12%, tracking error is at most 6%, the historical worst loss is no worse than -25%, and expected return clears inflation plus 3%.
4. Trade back to target weights.

Between rebalances, the risk officer will monitor the stock-bond correlation, drawdown and volatility against the invalidation triggers listed with this recommendation. If any trigger is hit, the allocation returns to the committee before the next scheduled date rather than waiting for quarter-end.

## IPS compliance
The recommended allocation complies with every hard rule of the governing IPS, version 0.2, which has been ratified:
- Expected real return at least CPI + 3%: met.
- Ex-ante volatility between 8% and 12%: 8.00%, at the floor.
- Backtest maximum drawdown no worse than -25%: -23.3%.
- Ex-ante tracking error to the 60/30/10 benchmark at most 6%: 3.76%.
- Long only, no leverage, no derivatives: met.

Compliance was reached after a disclosed reweighting of the blend, which raised volatility from 7.43% to the 8% floor.

Escalations:
- TRIGGERED (regime confidence below 0.4). The macro agent's regime confidence is 0.35. The board should note that the forecasts behind this allocation inherit that uncertainty.
- Not triggered (CIO selects below composite threshold). The chosen blend's composite score of 0.800 is well above the 0.3 threshold.
- Not triggered (hard violation unresolved). Several candidate portfolios clear every hard rule after the revision cycle.

## What would make this recommendation wrong
- Ex-ante volatility, recomputed at any quarterly rebalance, falls below the IPS 8% floor (it is exactly 8.00% today) or rises above 12%.
- The backtest maximum drawdown, re-run on the latest data or an alternative rebalance date, is worse than -24%. That leaves under 1 point of headroom to the -25% hard limit.
- The trailing 12-month correlation between US large-cap equity and intermediate Treasuries turns positive above +0.3, meaning the stock-bond hedge has failed.
- The macro agent changes the regime call away from expansion (to late-cycle, contraction or stagflation), or its confidence falls below 0.25.
- The CMA for US equity (large-cap or value) is cut by 1 percentage point or more, or the investment-grade or high-yield spread forecast widens by 1.5 percentage points or more. Either would undercut the return case and the credit sleeves.
- Ex-ante tracking error to the 60/30/10 benchmark rises above 5%, against the 6% limit, or expected return falls below the CPI + 3% real-return floor.

## Escalations under the IPS
- regime_confidence_below: the macro agent's regime confidence is 0.35, below 0.4; action: flag_in_board_memo. Macro agent's regime confidence is low; downstream CMAs inherit that uncertainty.

## Dissenting views
- Meta-optimisation has the better Sharpe (0.43 ex-ante, 0.68 backtest), slightly more drawdown room (-23.2%) and needs no repair. A Sharpe-first committee would choose it. I did not, because it is 37% max_sharpe, which breached the drawdown limit on its own and rests on an untested value-equity forecast.
- market_cap_weight was bottom-flagged on 14 of 15 ballots, yet the repair raised its share by 6pp. The regime-conditional ensemble raised it by only 3pp. I accept this because the added exposure is mostly benchmark US large-cap equity and the result complies. Its standalone -40.6% drawdown is still why headroom fell to 1.7 points.
- resampled_efficient_frontier, the largest ingredient at 15%, passes the drawdown limit by only 16bp on one historical path, as the CRO and both reviewers note. The ensemble dilutes this but inherits some of the fragility.
- risk_parity is shortlisted and weighted here, but its revised version still breaches the 8% volatility floor ex-ante and its drawdown was not re-checked after revision. Reviewers also found technical errors in its diversification and Sharpe claims. It is acceptable only as a minority ingredient within a compliant blend.
- inverse_volatility, an ingredient, carries about 43% in credit and sovereign spread assets that fall together in a spread-widening shock. Its reviewers found its diversification overstated.
- The pc_researcher and resampled_efficient_frontier reviewers note that the stock-bond hedge behind cvar_minimization, black_litterman and risk_parity failed in 2022 and the 1970s. That is the main unhedged scenario for this allocation.

## The allocation
| asset | weight |
|---|---|
| intermediate_treasuries | 15.8% |
| us_large_cap | 13.9% |
| long_treasuries | 8.3% |
| us_value | 8.0% |
| gold | 6.7% |
| ig_corporates | 5.2% |
| short_treasuries | 4.4% |
| reits | 4.3% |
| hy_corporates | 4.3% |
| us_small_cap | 3.9% |
| us_growth | 3.9% |
| intl_sovereigns | 3.8% |
| intl_corporates | 3.8% |
| commodities | 3.6% |
| usd_em_debt | 3.2% |
| intl_developed | 3.2% |
| emerging_markets | 2.9% |
| cash | 0.7% |

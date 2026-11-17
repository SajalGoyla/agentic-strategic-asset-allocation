# Board memo — strategic asset allocation

Run `claude3`, as of 2026-10-01. Recommended by the CIO agent; ensemble
**regime conditional**.

## Recommendation
We recommend a blended portfolio that combines the allocations proposed by 13 of the 15 investment methods we evaluated, using the 'regime-conditional' blending rule. No single method's view dominates: the largest contribution from any one method is about 11%.

The blend had to be adjusted slightly to meet the policy's minimum risk level. Weight was moved toward the methods the review panel rated most highly, and away from methods that broke policy limits on their own. This changed about 6% of the portfolio.

## Expected performance against the benchmark
Our forecasts for the portfolio are:
- expected annual return of about 6.7%;
- expected volatility of 8.0%, at the bottom of the policy's 8-12% band;
- a forward-looking return-to-risk (Sharpe) ratio of 0.39.

Compared with the 60% US large-cap / 30% intermediate Treasury / 10% investment-grade corporate benchmark, we expect returns to differ by about 3.7 percentage points in a typical year (tracking error 3.72%, against a 6% policy maximum). Because the portfolio holds less in US large-cap stocks and more in Treasuries, other bonds and real assets than the benchmark, it should lag in strong US equity rallies and hold up better in equity sell-offs. It may still lose ground if stocks and bonds fall together.

In a quarterly-rebalanced historical test, the portfolio's worst peak-to-trough loss was -23.3%, inside the -25% policy limit. Its historical return-to-risk ratio was 0.63. These are estimates, not promises.

## Macro rationale
The macro team's best reading is that the economy is in expansion, but it holds that view with low confidence (0.35 on a 0-1 scale). We therefore chose a blend whose results barely depend on the regime call: it looks almost identical to the plain averages of the methods. In other words, we did not bet heavily on the expansion view. Instead, we spread the portfolio across many approaches so that no single forecast drives the outcome.

## Largest positions
Intermediate-term US Treasuries are the largest holding at about 15%, followed by US large-cap stocks at about 14% and long-term US Treasuries at about 9%. The rest is spread across US value, growth and small-cap stocks, international stocks, corporate and international bonds, gold and other real assets. In total the portfolio holds the equivalent of about 15 equally-sized positions.

## Changes since the last review
No prior recommended allocation was supplied to this review, so this is the first recommendation recorded under the ratified IPS v0.2. Within this review, two adjustments were made to the raw blend:
- To lift its risk from 7.5% to the 8% policy floor, weight moved toward the CVaR-minimisation and inverse-volatility methods (about +3 points each).
- Weight moved away from the maximum-entropy method (-7 points) and the hierarchical risk parity method (-3 points). Both broke policy limits on their own.

## Key risks to monitor
- Stocks and bonds falling together, as in 2022 or the 1970s. Much of the portfolio's protection assumes Treasuries rise when stocks fall, so this would hit the largest holdings at once.
- Limited room under the loss limit. The historical worst loss of -23.3% is only about 1.7 points from the -25% policy limit.
- Risk at the policy floor. Volatility sits exactly at the 8% minimum, so small changes in markets or estimates could push it outside the band at a rebalance.
- Credit stress. A meaningful share of the portfolio is in corporate, high-yield, international and emerging-market bonds, which tend to fall together when credit spreads widen.
- Uncertain economic regime. The macro team's confidence in its expansion call is low, so return forecasts carry extra uncertainty.
- Lagging the benchmark in a strong US equity rally, because the portfolio holds less US large-cap stock than the benchmark.

## Rebalancing plan
Each quarter we will rebalance back to target weights and re-check every policy limit:
- expected return of at least inflation + 3%;
- volatility between 8% and 12%;
- tracking error of no more than 6%;
- historical worst loss no worse than -25%;
- long-only, with no leverage or derivatives.

If the portfolio's loss from peak reaches -20%, tracking error exceeds 5%, or the stock-bond relationship turns positive for a quarter, the investment committee will review the allocation before the next scheduled date.

## IPS compliance
The governing policy is IPS v0.2, which is ratified. The recommended portfolio complies with every hard limit:
- expected real return at or above inflation + 3%;
- ex-ante volatility of 8.00%, within the 8% floor and 12% ceiling;
- historical worst loss of -23.3%, inside the -25% limit;
- tracking error of 3.72%, within the 6% maximum;
- long-only, with no leverage and no derivatives.

Compliance was reached after a disclosed reweighting of the methods in the blend; no new exposures were added.

One escalation rule is triggered and is flagged here as the policy requires: the macro team's regime confidence (0.35) is below the 0.4 threshold, so the return forecasts inherit that uncertainty. Two other escalation rules are not triggered:
- the chosen blend's composite score (0.799) is well above the 0.3 threshold;
- compliant candidates exist, so no unresolved hard violation requires human escalation.

## What would make this recommendation wrong
- Re-estimated ex-ante volatility of the held portfolio falls below 8.0% or rises above 12.0% at a quarterly rebalance. Either is an IPS hard breach requiring re-optimisation.
- The portfolio's realised peak-to-trough drawdown reaches -20%. This is an early-warning trigger set 5 points inside the -25% IPS limit, given the backtest's -23.3% leaves little headroom.
- The rolling 12-month correlation between US large-cap equity and intermediate Treasury returns turns positive and stays above +0.3 for a full quarter. That breaks the stock-bond hedge the main ingredients rely on.
- The macro agent moves its regime call away from expansion (to late-cycle, contraction or stagflation), or its confidence remains below 0.4 at the next quarterly review.
- The equity CMA for US large-cap or US value is cut by 1 percentage point or more, or the intermediate-Treasury CMA moves by 75bp or more. Either changes the blend's return and risk balance.
- Ex-ante tracking error to the 60/30/10 benchmark rises above 5.0%, leaving less than 1 point of the 6% budget.
- High-yield credit spreads widen by 200bp or more within a quarter. That would activate the credit and sovereign cluster carried in via inverse_volatility and risk_parity.

## Escalations under the IPS
- regime_confidence_below: the macro agent's regime confidence is 0.35, below 0.4; action: flag_in_board_memo. Macro agent's regime confidence is low; downstream CMAs inherit that uncertainty.

## Dissenting views
- Meta-optimisation offers the best Sharpe (0.43 ex-ante, 0.68 backtest), needs no repair, and has the smallest drawdown (-23.2%). I declined it because 37% rests on max_sharpe, which breaches the drawdown limit on its own, got zero vote points, and was criticised for amplifying one CMA spread into a 51% value-equity position.
- resampled_efficient_frontier won the vote (49 points, composite 1.000) and would need no repair as a single method. I declined it because its -24.8% drawdown is 16bp from the limit, which the CRO and two reviewers call fragile, and its 4.51% tracking error is the highest of the offered options.
- The regime confidence of 0.35 argues against any regime-conditioned blend, and the paper's own late-cycle choice was inverse tracking-error weighting. I kept regime_conditional because its statistics are essentially those of the unconditional blends, and because its repair (6.1% of the portfolio) is smaller than inverse tracking-error's (7.2%) and its breadth larger (12.4 against 9.8 effective candidates).
- Three shortlisted ingredients (cvar_minimization, black_litterman, risk_parity) share the CRO's binding risk: a joint stock-bond sell-off of the 2022 or 1970s kind. The blend does not diversify this away, and the repaired drawdown leaves only about 1.7 points of headroom.
- inverse_volatility gained weight in the repair, but reviewers found its diversification overstated: an implicit 43% credit and sovereign spread cluster, plus a minor technical error equating inverse volatility with equal risk contribution.
- black_litterman is the largest single share (11%). A reviewer found its equilibrium prior double-counts overlapping US equity ETFs, which may distort its large-cap and value split.
- market_cap_weight was bottom-flagged on 14 of 15 ballots, with a -40.6% drawdown. It is one of the ensemble's inputs, but its composite of 0.000 means it carries little weight. I note the dissent and do not rely on it.

## The allocation
| asset | weight |
|---|---|
| intermediate_treasuries | 15.1% |
| us_large_cap | 13.9% |
| long_treasuries | 9.1% |
| us_value | 8.8% |
| gold | 6.7% |
| ig_corporates | 5.1% |
| short_treasuries | 4.3% |
| hy_corporates | 4.1% |
| us_growth | 4.1% |
| us_small_cap | 4.0% |
| commodities | 3.9% |
| reits | 3.9% |
| intl_sovereigns | 3.8% |
| intl_corporates | 3.7% |
| intl_developed | 3.0% |
| usd_em_debt | 2.9% |
| emerging_markets | 2.7% |
| cash | 0.8% |

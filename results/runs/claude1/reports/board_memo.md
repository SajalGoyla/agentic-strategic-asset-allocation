# Board memo — strategic asset allocation

Run `claude1`, as of 2026-10-01. Recommended by the CIO agent; ensemble
**meta optimization**.

## Recommendation
We recommend the 'meta-optimisation' blend. It combines three of the strongest candidate portfolios proposed by the investment team into a single allocation, weighting them to get the best balance of return and risk.

This blend meets every hard rule in the draft Investment Policy Statement without any adjustment. It has the most cushion of all the options against the drawdown limit and the benchmark-tracking limit.

We chose it over the committee's top-voted single portfolio because that portfolio sits very close to the maximum-loss limit. We chose it over broader averages because those had to be substantially altered (14-29% of the portfolio moved) to meet the policy's minimum-risk requirement.

## Expected performance against the benchmark
Expected annual return is about 7.3%, with expected volatility of about 8%. This is the bottom of the policy's 8-12% risk band, so the portfolio is designed to be steadier than the benchmark (60% US large-cap stocks, 30% intermediate Treasuries, 10% investment-grade corporates).

Tracking error to the benchmark is about 3.3% a year. In a typical year, the portfolio's return should land within roughly 3 percentage points of the benchmark's.

It holds fewer large-cap US stocks and more value stocks and Treasuries than the benchmark. It should hold up better in sell-offs and lag in a strong rally led by large US growth companies.

In historical testing it delivered a risk-adjusted return (Sharpe ratio) of 0.67. Its worst peak-to-trough loss was -23.1%, inside the -25% limit.

## Macro rationale
The economy is assessed to be in expansion. That favours owning growth assets such as equities to earn their risk premium. Policy caps risk at a moderate level, so the portfolio pairs a meaningful equity allocation, tilted toward value stocks, with high-quality government bonds that have historically cushioned stock declines.

The blend draws on candidates that use the team's return forecasts with some discipline: a maximum-entropy approach with a return floor, among others. It avoids the cash-heavy approaches that would fail the policy's return and risk requirements in a growth environment.

## Largest positions
The largest holdings are:
- US value stocks: about 24%
- Intermediate-term US Treasuries: about 20%
- Long-term US Treasuries: about 13%

The rest is spread across other asset classes, equivalent to roughly 10 equally sized holdings. The blend draws on three candidate portfolios; the largest contributor is the maximum-entropy candidate at about 39%.

## Changes since the last review
No prior board-approved allocation is recorded for this pipeline run, so this is presented as the initial recommendation under draft IPS v0.2.

Against the benchmark, the main differences are:
- substantially less US large-cap equity
- more US value equity
- more Treasury duration across intermediate and long maturities

## Key risks to monitor
- Volatility sits at the policy floor of 8%. A calm market could push measured risk below the minimum, requiring a rebalance toward riskier assets.
- Concentration in three source portfolios: if their shared return forecasts are wrong, there are fewer independent approaches to offset the error. Reviewers found technical inconsistencies in the largest contributor's original write-up.
- Stocks and bonds falling together, as in an inflation-driven rate shock, would remove the bond cushion and deepen losses.
- Lagging the benchmark in a rally led by large US growth stocks, given the underweight there.
- Drawdown: historical worst loss of -23.1% against a -25% limit, a margin of about 2 points.
- A change in the economic regime away from expansion would undercut the macro case for this mix.

## Rebalancing plan
The portfolio is reviewed and rebalanced quarterly back to target weights. At each quarter, the team will:
- re-check volatility (within 8-12%), tracking error (at most 6%), the drawdown limit (-25%) and the real-return target (inflation plus 3%)
- confirm the economic regime call
- review the return forecasts

If any invalidation condition is triggered, including volatility below 8%, drawdown beyond -20%, tracking error above 5% or a regime change, the full selection process will be re-run before the next scheduled rebalance and the board notified.

## IPS compliance
The recommended allocation complies with every hard limit of IPS v0.2:
- Expected real return: at least inflation plus 3%.
- Ex-ante volatility: 8.00%, within the 8% floor and 12% ceiling, at the floor.
- Backtest maximum drawdown: -23.1%, within the -25% limit.
- Tracking error to the benchmark: 3.34%, within the 6% limit.
- Holdings: long-only, with no leverage or derivatives.

No adjustment was needed to achieve compliance. The governing IPS (config/ips.yaml, v0.2) is a DRAFT and has not been finally adopted. Compliance is assessed against draft limits that may change on adoption. No escalation rule was triggered: compliant candidates exist, and the chosen ensemble's composite score (0.798) is well above the 0.3 flag threshold.

## What would make this recommendation wrong
- The macro agent's regime call moves out of expansion (to late-cycle, slowdown or recession), or its regime confidence falls below 0.4. If either happens, re-run the pipeline and reconsider the averaging ensembles.
- Ex-ante or trailing 12-month realised volatility falls below 8.0% or rises above 12.0% at a quarterly check. The portfolio is parked at the 8.00% floor, so a low-side breach is the most likely failure.
- Live drawdown from peak exceeds -20%, or a re-run backtest maximum drawdown worse than -24.5%.
- Ex-ante tracking error to the 60/30/10 benchmark rises above 5% (against the 6% hard limit).
- The CMA for US value equity relative to US large-cap is cut by 1 percentage point or more. Separately, the expected nominal return falls by more than 1.5 percentage points, or the CPI assumption rises by a similar amount. Either would erode the margin over the CPI+3% real-return floor.
- Rolling 12-month stock-bond correlation turns and stays positive (above +0.3) for two consecutive quarters, removing the Treasury cushion the allocation depends on.
- The IPS is finalised with limits different from draft v0.2, in particular a volatility floor above 8% or a drawdown limit tighter than -25%.

## Dissenting views
- Peer reviewers found two technical errors in pc_researcher, the largest ingredient at 39%. Its stated constraints included the IPS volatility cap, yet the original breached the band at 3.82%. Its reported Sharpe also exceeded the max-Sharpe figure it claimed to sit below. The revised version is compliant (8.22% volatility). However, the ensemble inherits a construction whose specification and output did not match, and the CRO flagged its large US large-cap underweight as a tracking-error risk. I proceed because the revision cured the breaches and the ensemble's tracking error is 3.34%, but this ingredient warrants scrutiny at the next review.
- Single-method resampled efficient frontier was ranked first by the vote (68 points, composite 1.000) and scores marginally higher on the six-dimension composite. A trustee could reasonably prefer the committee's clear favourite. I did not choose it because its -24.3% drawdown leaves 0.7 points of headroom against a hard limit, the CRO's binding risk. Reviewers also noted that resampling does nothing to correct systematic CMA bias.
- The averaging ensembles, especially composite-score and inverse-tracking-error, spread the bet across 14-15 methods, which is the diversification §4.4's CIO valued in an uncertain regime. That argument is real. I judged that moving 14-28% of the book to force compliance makes the adjusted portfolio a different, untested allocation, and that this cost outweighs the breadth.
- Reviewers flagged technical errors in black_litterman (an inconsistent risk-aversion tuning description, and Ω not carrying per-view confidence). It is a shortlisted, high-ranked candidate, and any reliance on it shares that reproducibility concern.
- hierarchical_risk_parity was bottom-flagged on 11 of 15 ballots. It does not bear on this recommendation because it carries no meaningful weight in the chosen ensemble.

## The allocation
| asset | weight |
|---|---|
| us_value | 24.4% |
| intermediate_treasuries | 20.4% |
| long_treasuries | 12.7% |
| us_large_cap | 7.2% |
| us_growth | 6.6% |
| short_treasuries | 5.7% |
| gold | 5.6% |
| us_small_cap | 3.6% |
| ig_corporates | 3.3% |
| hy_corporates | 2.6% |
| reits | 2.0% |
| emerging_markets | 1.6% |
| commodities | 1.3% |
| intl_developed | 0.9% |
| usd_em_debt | 0.8% |
| intl_corporates | 0.7% |
| intl_sovereigns | 0.6% |

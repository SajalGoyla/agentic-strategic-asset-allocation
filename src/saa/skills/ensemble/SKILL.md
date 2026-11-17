# Ensemble Skill

Used by: the CIO agent (stage 6). Paper reference: Ang, Azimbayev & Kim (2026) §3.6, §4.4 and
Exhibit 10.

## What it does

Builds every ensemble of the candidate portfolios the paper gives the CIO, and profiles each
one exactly as a candidate is profiled, with the CRO's risk skill: ex-ante volatility and
tracking error, the quarterly-rebalanced backtest and its drawdown, and the full IPS check.
Only a compliant ensemble may be recommended (§3.6, "non-negotiable"). Deterministic; the
choice among compliant ensembles is the CIO agent's.

```bash
uv run saa-agent cio --run-id <run> [--no-llm]
```

The candidates are all fifteen proposals, with the five shortlisted agents' **revised**
proposals in place of their originals. Writes `reports/cio_ensembles.md`.

## The techniques

| Ensemble | Weights the candidates by |
|---|---|
| `single_method` | all on the top-ranked candidate in the vote that the IPS permits on its own |
| `simple_average` | equally |
| `inverse_tracking_error` | 1 / tracking error to the centroid — closeness to consensus (the paper's March 2026 choice) |
| `backtest_sharpe_weighted` | backtest Sharpe ratio; a negative one gets nothing |
| `meta_optimization` | the highest ex-ante Sharpe over the candidates' weighted sums, subject to the volatility band, the tracking-error budget **and the drawdown limit** |
| `regime_conditional` | each candidate's regime-fit score (how it did in past months of today's regime) |
| `composite_score` | the Exhibit 9 composite: the vote blended with the metric score |
| `trimmed_mean` | equally, after dropping the 10% of candidates furthest from the centroid |

## IPS discipline

**The drawdown limit binds here.** Constraining a realised drawdown fits weights to the
1993-2026 path, so it is kept off the fifteen candidates and put on the recommendation — one
in-sample fit instead of fifteen. Since decision 49 no IPS limit is forced on a candidate, so
this is also where the volatility band and the tracking-error budget first bind. The meta-optimisation imposes it
directly. Inside the optimiser the backtest is a vectorised monthly-rebalanced approximation
with a 0.5pp margin; the CRO's quarterly backtest then verifies the result.

**A breaching ensemble is projected, not discarded.** On the 2026-10-01 free run, every
averaging ensemble landed just past the limits: drawdowns of -25.8% to -27.2% against -25%, and
two at 7.97-7.99% volatility, below the 8% floor. Averaging portfolios pinned to the floor
diversifies risk away. That is the paper's own situation: its chosen ensemble had a 7.54%
volatility and a -25.6% drawdown. Discarding them would leave the CIO only the two concentrated
ensembles that comply outright (about 5 effective assets). So a breaching ensemble is moved to
the nearest allocation (squared weight distance) that meets the band, the budget and the
drawdown limit, kept only if the CRO's backtest verifies it, and marked as projected with its
figures before projection. On that run all six projected ensembles verified, at 13.5-15.7
effective assets.

**Since decision 49 the projections are larger.** With candidates no longer forced into the
band, 7 of 15 sit inside it on the 2026-10-01 inputs and the simple average of all fifteen has
4.81% volatility. On that free run six of the eight ensembles were projected for volatility
alone; the chosen composite-score ensemble went from 6.39% to 8.00% at 16.3% one-way turnover.
The CIO sees each projected ensemble's figures before projection and is told to treat the
projection as a real cost; the meta-optimisation and the single best-voted compliant candidate
need none.

**Since decision 62 the first repair reweights the candidates, not the assets.**
`reweight_to_policy` finds the mix of the candidates nearest the technique's own weights
(squared distance) whose blend meets the band, the budget and the drawdown limit; the asset
projection above runs only when no such mix complies. Both are verified on the CRO's backtest
and recorded (`Ensemble.repair`, `recipe_weights`, and `policy_repair` in `cio_decision.json`).
With decision 61's candidates on the claude2 inputs, the averaging ensembles start at
7.31-7.75% volatility and the reweighting moves 9-16% of ensemble weight, 5-7% of the
portfolio; before decision 61 they started at 4.96-6.72% and the asset projection moved
13.5-29.5%. Reweighting costs a little more asset turnover than the nearest asset projection
(5.2% against 2.4% for the composite-score ensemble) and buys an allocation made only of what
the methods proposed. An increase in a candidate's ensemble weight is priced at 1 / its vote
composite (a cut at 1), so the repair leans on the methods the peers approved rather than on
whichever offers the cheapest volatility (`reweight_costs`).

## The free-run choice

Every ensemble is scored on the candidates' six-dimension rubric by
`method_scoring.score_mix` (decision 50). What the allocation has is measured on it: backtest
Sharpe, IPS compliance, diversification, and its Sharpe ratio in the current regime placed on
the candidates' range. What only a method has, estimation robustness and whether it reads the
CMAs, is the mix-weighted average of its candidates'. `--no-llm` picks the compliant ensemble
with the best composite. With a model, the CIO chooses and has to say what it traded.

Each `Ensemble` also reports its composition, so a concentrated mix is visible: the candidates
holding at least 1% of it, the largest single share, the effective number of candidates, and
for a repaired ensemble the one-way turnover the repair cost and, if it was reweighted, the
share of ensemble weight that moved.

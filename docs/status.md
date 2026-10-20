# Status

Where the project stands against `Agentic_SAA_12Week_Project_Plan.md`. Update this when a phase
item lands; it is the first thing a new session should read after `CLAUDE.md`.

**As of 2026-10-16** (project week 7 of 12). Phases 1 and 2 are complete and closed. Phase 3
is in progress: week 7's half — the CRO agent and the peer-review assignment — is done; the
review cycle, the Borda vote and the CIO follow in weeks 8-9. `main` is the only source of
truth.

## By pipeline stage

| Stage | State | Owner |
|---|---|---|
| Data layer: 8 sources, 14 datasets, 18-asset history, validation | Done | Sajal |
| Historical-analysis skill (writes the shared contracts) | Done | Sajal |
| Run context: run ids, directory layout, headers | Done | Sajal |
| IPS (`config/ips.yaml`, `check_compliance`) | Done, v0.2 draft with faculty answers | Shambhawi |
| Output contracts (16) + generated schemas | Done, schema 2.0.0 | Shambhawi |
| LLM layer (routing, budget, retries) | Done | Shambhawi |
| 1. Macro regime agent | Done: scoring skill + agent + `regime_history` | Shambhawi |
| 2. Asset-class agents: CMA method calculators (all 18 assets) | Done | Sajal |
| WRDS CMA inputs: US and international equity valuation, corporate bond yields, ETF market values | Done | Sajal |
| 2. Asset-class agents: signals skill (`signals.json`) | Done | Shambhawi |
| 2. Asset-class agents: CMA judge (`cma.json`) | Done | Shambhawi |
| 3. Covariance skill (Ledoit-Wolf default, chosen by out-of-sample test) | Done | Sajal |
| 4. PC agents: heuristic (1/N, inverse vol, inverse variance) | Done | Shambhawi |
| 4. PC agents: return-optimized (max Sharpe, Black-Litterman) | Done | Shambhawi |
| 4. PC agents: risk-structured (risk parity, HRP), non-traditional (CVaR, tail-risk parity) | Done | Sajal |
| 4. PC agents: researcher, adversarial diversifier | Done | Sajal (for Shambhawi) |
| Risk skill (backtest, VaR, drawdown, concentration, risk score) | Done | Sajal |
| 5. CRO agent (`saa-agent cro`) | Done | Sajal |
| 5. Peer-review assignment and review prompts (`saa-skill review-assign`) | Done | Shambhawi |
| 5-6. Six-dimension metric score, shared by the vote and the CIO (`saa-skill method-scores`) | Done | Sajal |
| 5. Peer-review agent (the reviews themselves, `saa-agent peer-review`) | Done | Sajal (for Shambhawi) |
| 5. PC revision step after the reviews | Not started (week 8) | Sajal |
| 5. Borda vote, metric blend, diversity rule | Not started (week 8) | Shambhawi |
| 6. CIO agent + board memo | Not started (week 9) | both |
| Backtest, stress tests, visualisation | Not started (weeks 10-12) | both |

**Milestone M1 (data and macro layer live, week 3): met.**
**Milestone M2 (CMA layer complete, week 6): met, a week early** — all 18 assets have candidate
methods, a judge and a validation check; the covariance agent is live; the full PC roster (15
agents across Exhibit 5's four families, plus the researcher and the adversarial diversifier)
produces candidate portfolios.

## Phase 1 closeout (2026-09-29)

- The historical-analysis skill now builds the shared contracts directly; its duplicate models
  are gone, and a test asserts the skill uses the contracts.
- `saa.run.RunContext` owns run ids, the run directory layout and the header; the skill writes
  through it, and the macro agent should adopt it next time it is touched.
- The `macro_inputs` skill was dropped in favour of `skills/macro_regime/scoring.py`, which the
  macro agent already uses. Its one safeguard — proportional change refuses a non-positive base,
  so a mistaken `yoy` on CFNAI fails visibly — was ported into that module.
- Units settled on percent (decision 15), schema 1.0.0.
- Integration tests run against a real lake and skip without one;
  `docs/data_quality_report.md` records the Week 2 validation deliverable.

## Phase 2 progress (2026-10-01)

- **Signals skill** writes `cma/<asset>/signals.json` for all 18 assets: four technical
  signals, valuation by asset type (CAPE, yield level, credit spread), and two macro signals
  from the regime history. Sentiment is deliberately absent — Exhibit 3 sources it from web
  search, which the pipeline does not do (decision 26).
- **CMA judge** (`saa-agent cma-judge`) is the first stage-2 agent. It reads the eight
  candidates, the signals, the historical statistics and the macro view, and writes `cma.json`
  plus a per-asset `cma.md`. Exhibit 4's hard constraint — the estimate must sit inside the
  candidate range — is enforced in three places: the prompt, the contract, and the retry that
  feeds a rejection back. Assets run concurrently and one failure does not stop the stage.
- **PC agents** (`saa-agent pc`) cover the two Phase 2 families: equal weight, inverse
  volatility, inverse variance, maximum Sharpe and Black–Litterman. The optimisers are
  deterministic and the agent writes only the case for the weights, which is what the Phase 3
  peer review will argue over. `--no-llm` produces every portfolio and statistic for free.

## Phase 2 closeout (2026-10-08)

- **The PC roster is complete: 15 agents** (decision 33), chosen from the paper's 20 for
  quality. Heuristic: equal weight, inverse volatility, inverse variance, market-cap weight,
  volatility targeting. Return-optimised: maximum Sharpe, Black–Litterman, resampled efficient
  frontier. Risk-structured: risk parity, hierarchical risk parity, maximum diversification.
  Non-traditional: CVaR minimisation, tail-risk parity. The **PC-researcher** chooses a method
  the registry lacks from an implemented library (maximum entropy, global minimum variance) and
  its portfolio is reviewed like any other; the **adversarial diversifier** runs last and
  maximises tracking variance to the centroid of the other 14 under the paper's
  75%-of-maximum Sharpe floor. Decisions 29-31, 33.
- **CMA validation** (`saa-skill cma-validate`) checks every asset's estimate against expected
  ranges (`config/cma_validation.yaml`): plausibility per group, bonds against their starting
  yield, the implied Sharpe ratio, the equity classes against the paper's Exhibit 8, and the
  return-risk ordering across all 18. On the 2026-10-01 auto-blends: 17 pass, 1 warns (US
  Growth, +4.2pp above the paper's judge value — the gap the judge exists to close), 0 fail;
  return-risk rank correlation 0.76.
- Black–Litterman's market weights could never use CRSP's monthly ETF values (the loader
  expected a ticker-indexed frame); fixed, so it has weights at every date from 2010.

### What the first full stage-4 run showed

Running all five methods against the real lake, **four of the five fail the IPS volatility
floor**: inverse volatility (3.10%), inverse variance (0.73%), maximum Sharpe (2.29%) and
Black–Litterman (7.35%) all sit below the 8% band minimum, and only equal weight (8.40%)
complies. This is the concrete version of the question already open with Prof. Glasserman —
whether the volatility band should bind from below. If it does, most of the method roster is
disqualified before the peer review sees it, and the deliberation protocol has little to
deliberate over.

The full roster sharpens it (a free `--no-llm` run, auto-blends standing in for judged CMAs):
**10 of 11 failed** (with the four later additions, 13 of 15 do;
volatility targeting and equal weight pass). Every risk-based method concentrates in cash, the 0.6%-volatility asset —
risk parity 62%, HRP 92%, CVaR minimisation 97%, tail-risk parity 53% — at 0.6-2.5%
volatility. Maximum entropy misses the floor narrowly (7.5%), and the adversarial diversifier
breaks the 12% cap (13.2%). The cause is structural, not a bug: cash is in the risky universe,
and with no leverage a low-risk portfolio cannot be scaled up to the band.

### Resolved: where the volatility floor binds (decision 32, 2026-10-08)

The paper does not make candidates comply: its CRO "scores risk … but does not vote", IPS
compliance is 15% of the CIO's score, and the adversarial diversifier (−46.3% drawdown) still
gets ensemble weight. Compliance is "non-negotiable" only for the CIO's choice of ensemble. We
adopted the same rule. Tested on the free run: averaging the 11 portfolios gives 3.3-4.0%
volatility, but a meta-optimisation over them constrained to the IPS reaches 8.0% volatility,
Sharpe 0.47 and 2.9% tracking error, so a compliant recommendation exists without distorting
any method. Forcing each optimiser into the band was rejected (risk parity forced to 8% is no
longer risk parity: contributions spread 0-7.1% instead of 5.6% each), as was dropping cash from
the risk methods (still 1.6-5.7% volatility, now in short Treasuries).

## Decisions still open

| Question | Who decides | Blocks |
|---|---|---|
| IPS ratification as a whole (`status: draft` today) | Prof. Glasserman | Nothing yet; every header records the draft status |
| Note to faculty: the return objective is now a floor only, CPI + 3% (decision 41), not the paper's 3-4% band | Prof. Glasserman (FYI) | Nothing; adopted |
| Orchestration: how the six stages run end to end | Shambhawi | Week 6 onward |

## Phase 3 progress (2026-10-16, week 7)

Week 7 of the plan: the CRO agent, and the peer-review assignment with its prompt templates.
Both are in; the review cycle itself, the vote and the CIO are weeks 8 and 9.

- **Risk skill** (`skills/risk/`) computes everything §3.5 asks a risk report to cover:
  ex-ante volatility and tracking error from the covariance matrix; backtest volatility,
  Sharpe, monthly 95% VaR and CVaR and maximum drawdown from holding the proposed weights
  through the 1993-06 panel with quarterly rebalancing; Meucci effective N and the Herfindahl
  index; active weight by asset-class group plus realised benchmark beta; and IPS compliance
  through the same `check_compliance` the proposal already ran. Two conventions the paper
  leaves open are fixed here: VaR is **monthly**, stated as a loss (it can legitimately be
  negative — a cash-heavy portfolio's fifth-percentile month is a gain), and drawdown is
  negative, so it compares directly with the IPS limit.
- **CRO agent** (`saa-agent cro`) writes one `cro_report.json` per candidate. It has no ballot
  in its contract and sees one portfolio per call, which is how §3.5's "neutral assessor ...
  does not vote" is enforced rather than prompted. The **risk score is script-computed**
  (decision 34) — a fixed five-component formula against the IPS limits — so 15 candidates are
  scored on one ruler and the number can be re-derived; the model writes the reading of it.
- **Peer-review assignment** (`saa-skill review-assign`) pairs every agent with one
  intra-category and one inter-category peer, seeded from the run id so the pairing reproduces
  from the run's name alone. Reviews are **balanced** (every proposal gets exactly two on the
  15-agent roster) and a **one-member family substitutes** a second inter-category review, both
  recorded rather than silent (decision 35). `templates.py` holds the two review prompts, which
  are the paper's own account of why each pairing exists: intra-category audits the execution,
  inter-category attacks the premise.
- Schema 3.0.0: `cro_report` gained a nested `CroJudgment` and lost its flat `commentary`
  (decision 36).

### What the CRO run showed: the drawdown limit binds too

The free run over all 15 candidates (`--no-llm`, auto-blend CMAs, run `20261006T000000Z`) adds
the one hard limit the PC stage could not evaluate — realised drawdown needs the weights held
through history. **14 of 15 now fail the IPS, and only the PC-researcher's maximum-entropy
portfolio passes it outright** (8.11% volatility, −24.36% drawdown, 3.94% tracking error).

The three portfolios that cleared the volatility band fail on drawdown instead: equal weight
8.40% volatility but −26.65%, volatility targeting 8.90% and −28.14%, market-cap weight 11.79%
and −40.60%. The adversarial diversifier is −53.21%, close to the paper's own −46.3%. The
paper's own §4.4 portfolio is in the same bind (7.54% volatility, −25.6% drawdown, both just
outside). None of this changes decision 32: the limits bind on the CIO's recommendation, and an
ensemble has room a single method does not.

**Corrected 2026-10-18.** An earlier version of this section read the above as the volatility
band and the drawdown limit leaving "almost no room for a single method". That was an artefact
of looking only at return-maximising portfolios. Minimising realised drawdown subject to the
volatility band instead reaches **−12.4% at 8% volatility and −19.0% at 12%** — the two limits
are jointly satisfiable across the whole band with room to spare. What those portfolios hold is
another matter (the shallowest 10%-volatility portfolio is 48% gold, which is a statement about
gold's 1993-2026 path, not a recommendation). The genuinely tight limit is the **return band**,
and how tight depends on a deflator bug — see "The return target and the inflation deflator"
below.

### Tuning volatility without leverage (Prof. Glasserman, 2026-10-16)

Asked whether methods have parameters that could be tweaked to raise volatility without
leverage. Measured on run `20261006T000000Z` — yes, for the families with a return input, and
the dial is wide:

| Method | As shipped | Parameter | Range it reaches |
|---|---|---|---|
| `max_sharpe` | 2.29% vol (tangency) | risk aversion δ in `max w'μ − (δ/2)w'Σw` | 1.86% (δ=40) to 15.58% (δ=1) |
| `cvar_minimization` | 0.62% vol | the return floor `w'μ ≥ R` in Rockafellar–Uryasev's own formulation | 1.97% (R=5%) to 9.85% (R=8.5%) |
| `black_litterman`, `resampled_efficient_frontier` | 7.35%, 4.46% | inherit the same mean-variance step | follows `max_sharpe` |
| `maximum_entropy` | 8.11% | Sharpe floor fraction (0.75 today) | already in the band |
| risk-structured and the inverse-vol heuristics | 0.65-3.10% | **none** | see below |

The long-only, fully-invested frontier spans 2% to 19.5% volatility, so the band is reachable
with no leverage at all. Two caveats that matter more than the answer:

- **Tuning *up the frontier* breaks the other two limits.** δ=5 puts `max_sharpe` at 8.44%
  volatility but at a 4.09% real return (over the CPI+4% ceiling) and a −25.3% drawdown. The
  frontier's tilt above 8% is equity- and REIT-heavy. The methods should be tuned toward the
  *band*, not up the frontier.
- **The risk-structured family has no such parameter, by definition.** §3.4 defines it as
  optimising "risk metrics without explicit return forecasts", so there is no return side to
  trade off. Generalising risk parity to group risk budgets was tested: even a 90% equity risk
  budget reaches only 4.88% volatility, because cash at 0.62% volatility and eight fixed-income
  classes dominate any equal-risk-contribution solution. The honest options are to run them on a
  risky sub-universe (tested for cash alone: still 1.6-5.7%, decision 32) or to leave them below
  the band and let the CIO's ensemble do the work. Decision 32 is therefore load-bearing, not a
  convenience.

`maximum_diversification`'s 82% cash was checked for a convergence failure and is a genuine
optimum: diversification ratio 2.056, unbeaten by 4000 random long-only portfolios, against
1.506 for equal weight ex-cash. Cash is nearly uncorrelated with everything, which is exactly
what the diversification ratio rewards.

### Getting the candidates inside the IPS — built, 2026-10-18

Twelve of the fifteen methods could not reach the IPS volatility floor on their own, which made
them unreviewable: a 0.65%-volatility portfolio is not a candidate anyone can weigh against the
mandate. Three changes, all on `main`'s successor branch.

**The IPS's ex-ante limits now bind on every candidate (decision 37).** Each method is solved
*subject to* the volatility band and the tracking-error budget, keeping its own objective —
maximum Sharpe is still the best risk-adjusted portfolio, risk parity still the flattest risk
contributions, each now over the portfolios policy permits. Closed-form rules and HRP, which
have no objective to re-run, are projected to the nearest permitted portfolio. The drawdown
limit is deliberately *not* imposed: constraining a realised drawdown fits weights to the
1993-2026 path, which is the look-ahead §5.1 warns about. Every adjusted proposal carries
`policy_adjusted` and `unconstrained_volatility_pct` so a reviewer can tell the method under
policy from the method unconstrained.

**Two inputs were inconsistent and both decided compliance (decision 38).** The risk-free rate
is now cash's own CMA rather than the spot T-bill yield — cash *is* the risk-free asset, and the
two numbers differing (3.73% against 3.97%) gave cash a Sharpe of −0.38 while every risk-based
method piled into it. And the return test is deflated by expected inflation (T5YIE, 2.41%)
rather than trailing realised CPI (3.71%), which is what `expected_inflation_pct` was always
called.

**The return objective is a floor only (decision 41, superseding 39).** Once the deflator was
corrected, 13 of 15 candidates forecast more than CPI + 4%, so a hard ceiling disqualified
almost the whole roster for being too profitable. The ceiling is gone: at least CPI + 3%, and
nothing above it is reported.

#### Where that leaves the roster

| | Before | After |
|---|---|---|
| inside the 8-12% volatility band | 4 / 15 | **15 / 15** |
| satisfying every *ex-ante* IPS rule (volatility, tracking error, return floor) | 1 / 15 | **15 / 15** |
| satisfying all of those **and** the realised drawdown limit | 1 / 15 | **6 / 15** |
| mean pairwise tracking error across candidates | 4.65% | 4.50% |
| candidate volatility spread | 0.62-14.99% | 8.00-12.00% |

The nine that still fail do so **only** on drawdown, which is where it should bind: the CIO's
meta-optimisation over the fifteen reaches **8.00% volatility, −22.6% drawdown, 5.17% real
return, Sharpe 0.50, 3.48% tracking error, 7.0 effective assets** — fully compliant, from one
in-sample fit on the recommendation rather than fifteen on the candidates.

The deliberation survives: mean pairwise tracking error barely moves (closest pair 0.35%,
widest 9.20%), risk parity keeps risk contributions spread 3.21-7.10% around the 5.56% equal
level on 16 of 18 assets, and the adversarial diversifier is still the furthest from the
centroid (6.56%) at the top of the band. Shrinking the universe instead was tested and is
worse: dropping cash leaves the risk-based methods at 2.24-5.66%, and dropping cash, short
*and* intermediate Treasuries still only gets 5 of 7 into the band.

Two knock-on fixes came with it. §3.4's Sharpe floor is now measured against the best Sharpe
the IPS *permits* rather than the unconstrained maximum — the unconstrained tangency portfolio
is 90% short Treasuries at a Sharpe of 0.663, and 75% of that (0.498) is above the 0.505 best
attainable in the band, so the floor admitted a single portfolio and the adversarial diversifier
and the maximum-entropy researcher both collapsed onto it. And the PC-researcher now substitutes
when its method duplicates a registry portfolio, with **mean-downside risk** added to its
library from Exhibit 5 so it has a genuinely distinct objective to fall back to (decision 40).

### The return target and the inflation deflator

Two problems, and the second is a bug.

**The deflator is wrong.** `gather_inputs` sets `inflation_pct` from trailing 12-month realised
CPI — 3.71% on this run — and hands it to `check_compliance` as `expected_inflation_pct`. The
CMAs are 3-year-horizon nominal forecasts (Exhibit 8), so the matching deflator is *expected*
inflation over that horizon, which the lake already carries: T5YIFR 2.35%, T10YIE 2.38%, T5YIE
2.41%. A 1.3pp error, and it decides compliance. The field name already says what it should be.

**The two-sided return band is what actually binds, and the deflator decides it.** Taking the
return-maximising portfolio at each volatility, the volatility range satisfying each limit:

| Limit | Volatilities that satisfy it |
|---|---|
| volatility band 8-12% | 8.00-11.75% |
| drawdown ≥ −25% (return-maximising portfolios) | ≤ 8.25% |
| return CPI+3-4%, trailing CPI (3.71%) | 6.00-8.00% |
| return CPI+3-4%, expected inflation (2.40%) | 3.00-5.00% |
| return CPI+3% **as a floor**, either deflator | 6.00-12.25% / 3.00-12.25% |

Read two-sidedly with the correct deflator, the intersection is **empty**. Read as a floor, it
is the whole band. Which is the answer to the open question "should exceeding the return target
disqualify a portfolio?" — if it does, the IPS has no feasible portfolio once the deflator is
fixed; if the target is a floor, everything works and the binding limits are volatility and
drawdown, as §4 reads them.

**Also inconsistent: cash's CMA is below the risk-free rate.** `cma.json` gives cash 3.73% while
every Sharpe ratio in the pipeline uses DTB3 at 3.97%, so cash scores a Sharpe of −0.38. Cash
*is* the risk-free asset in this universe; two numbers for one thing. The consequence is visible
in the roster: every return-optimised method treats cash as strictly dominated while every
risk-based method piles into it. It also inflates short Treasuries to the joint-highest Sharpe
in the universe (0.33), which is why `max_sharpe` holds 86.5% of them.

One thing not to over-read: ex-ante and backtest volatility agree to within 0.1pp on almost
every candidate (8.40 vs 8.41, 14.99 vs 15.09). That is not independent confirmation — the
Ledoit–Wolf matrix is estimated over the same history the backtest runs through. It will stop
agreeing once the Phase 4 backtest estimates the matrix out of sample.

## Next, in order

Phase 3, weeks 8-9:

1. A first paid run of the CMA judge and the 15 PC agents (`--cap-usd` set), then
   `saa-skill cma-validate` on the judged CMAs, then the CRO with a model. Everything so far is
   `--no-llm`: total API spend is still $0.00.
2. The peer-review agent: run the 30 assignments, write `peer_review-<reviewed>.json`, with the
   seed in every header.
3. The revision step for the top five, after the reviews and the CRO report.
4. The modified Borda vote: ballots, the metric blend with its regime-dependent weight, and the
   three-of-four-families diversity rule on the shortlist.
5. The CIO: the ensemble techniques, including a meta-optimisation constrained to the IPS, the
   six-dimension score, and the board memo. Only a compliant ensemble may be recommended.
6. Wiring: point the macro agent at `RunContext`, then a single `saa-run` command.

## Data facts worth not re-deriving

- All 18 assets have monthly returns from **1993-06**; most from 1980. ETFs alone would start 2010-06.
- **8 of 62** FRED series carry true ALFRED vintages; the earliest starts 1991, the latest 2016.
- Latest validation (2026-10-01, full ingest with WRDS): **269 checks pass, 1 warning, 0 failures**.
  starting 1993-06 rather than 1990.
- Yahoo ETF returns match CRSP within **0.45%** annualised tracking error for all 18 ETFs.
- CRSP stock and index data end **2024-12**; ETFs cover later months.

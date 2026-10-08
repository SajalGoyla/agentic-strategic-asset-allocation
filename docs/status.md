# Status

Where the project stands against `Agentic_SAA_12Week_Project_Plan.md`. Update this when a phase
item lands; it is the first thing a new session should read after `CLAUDE.md`.

**As of 2026-10-08** (project week 5 of 12). Phases 1 and 2 are complete; Phase 3
(deliberation and the CIO) is next. `main` is the only source of truth.

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
| 5. CRO, peer review, Borda vote | Not started (weeks 7-8) | both |
| 6. CIO agent + board memo | Not started (week 9) | Shambhawi |
| Backtest, stress tests, visualisation | Not started (weeks 10-12) | both |

**Milestone M1 (data and macro layer live, week 3): met.**
**Milestone M2 (CMA layer complete, week 6): met, a week early** — all 18 assets have candidate
methods, a judge and a validation check; the covariance agent is live; the full PC roster (11
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

- **The PC roster is complete: 11 agents.** Risk-structured (risk parity, hierarchical risk
  parity) and non-traditional (CVaR minimisation, tail-risk parity) join the five above. The
  **PC-researcher** chooses a method the registry lacks from an implemented library (maximum
  entropy, maximum diversification, global minimum variance) and its portfolio is reviewed like
  any other; the **adversarial diversifier** runs last and maximises tracking variance to the
  centroid of the other ten under the paper's 75%-of-maximum Sharpe floor. Decisions 29-31.
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
**10 of 11 fail**. Every risk-based method concentrates in cash, the 0.6%-volatility asset —
risk parity 62%, HRP 92%, CVaR minimisation 97%, tail-risk parity 53% — at 0.6-2.5%
volatility. Maximum entropy misses the floor narrowly (7.5%), and the adversarial diversifier
breaks the 12% cap (13.2%). The cause is structural, not a bug: cash is in the risky universe,
and with no leverage a low-risk portfolio cannot be scaled up to the band.

## Decisions still open

| Question | Who decides | Blocks |
|---|---|---|
| IPS ratification as a whole (`status: draft` today) | Prof. Glasserman | Nothing yet; every header records the draft status |
| Should exceeding the return target really disqualify a portfolio? | Prof. Glasserman | CRO agent, week 7 |
| Orchestration: how the six stages run end to end | Shambhawi | Week 6 onward |
| Should the volatility band bind from below? 10 of 11 PC agents fail it | Prof. Glasserman | The CRO agent and the vote, week 7 |

## Next, in order

1. Settle the volatility-floor question, since the CRO enforces it and the vote depends on
   which proposals survive. Options on the table: enforce the band inside each optimiser, hold
   cash outside the risk-based methods, or let the floor bind only on the CIO's final portfolio.
2. A first paid run of the CMA judge and the PC agents on the full roster (`--cap-usd` set),
   then `saa-skill cma-validate` on the judged CMAs.
3. Phase 3 (weeks 7-9): the CRO agent, peer-review assignment and the Borda vote, the revision
   step, and the CIO ensemble with the board memo.
4. Point the macro agent at `RunContext`, then a single `saa-run` command that chains the
   stages.

## Data facts worth not re-deriving

- All 18 assets have monthly returns from **1993-06**; most from 1980. ETFs alone would start 2010-06.
- **8 of 62** FRED series carry true ALFRED vintages; the earliest starts 1991, the latest 2016.
- Latest validation (2026-10-01, full ingest with WRDS): **269 checks pass, 1 warning, 0 failures**.
  starting 1993-06 rather than 1990.
- Yahoo ETF returns match CRSP within **0.45%** annualised tracking error for all 18 ETFs.
- CRSP stock and index data end **2024-12**; ETFs cover later months.

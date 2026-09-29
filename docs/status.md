# Status

Where the project stands against `Agentic_SAA_12Week_Project_Plan.md`. Update this when a phase
item lands; it is the first thing a new session should read after `CLAUDE.md`.

**As of 2026-09-29** (project week 3 of 12). **Phase 1 is complete**; `main` has 171 passing
tests and is the only source of truth.

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
| 2. Asset-class agents: signals skill, CMA judge | Next (plan weeks 4-5) | Sajal + Shambhawi |
| 3. Covariance skill (Ledoit-Wolf default, chosen by out-of-sample test) | Done | Sajal |
| 4. Portfolio-construction agents (10) | Not started (weeks 5-6) | both |
| 5. CRO, peer review, Borda vote | Not started (weeks 7-8) | both |
| 6. CIO agent + board memo | Not started (week 9) | Shambhawi |
| Backtest, stress tests, visualisation | Not started (weeks 10-12) | both |

**Milestone M1 (data and macro layer live, week 3): met.**

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

## Decisions still open

| Question | Who decides | Blocks |
|---|---|---|
| IPS ratification as a whole (`status: draft` today) | Prof. Glasserman | Nothing yet; every header records the draft status |
| Should exceeding the return target really disqualify a portfolio? | Prof. Glasserman | CRO agent, week 7 |
| Orchestration: how the six stages run end to end | Shambhawi | Week 6 onward |

## Next, in order

1. WRDS valuation ingestion: Compustat buybacks and earnings, I/B/E/S growth, CRSP market caps.
   Lifts the Gordon method (no buyback yield today) and replaces ETF AUM as the
   Black-Litterman weights.
2. Signals skill (`signals.json`), the other deterministic input to the judge.
3. The CMA judge agent (`cma.json`), the first stage-2 agent.
4. Point the macro agent at `RunContext` so every stage files outputs the same way.

## Data facts worth not re-deriving

- All 18 assets have monthly returns from **1993-06**; most from 1980. ETFs alone would start 2010-06.
- **8 of 62** FRED series carry true ALFRED vintages; the earliest starts 1991, the latest 2016.
- Latest validation: **266 checks pass, 1 warning, 0 failures**. The warning is USD EM Debt
  starting 1993-06 rather than 1990.
- Yahoo ETF returns match CRSP within **0.45%** annualised tracking error for all 18 ETFs.
- CRSP stock and index data end **2024-12**; ETFs cover later months.

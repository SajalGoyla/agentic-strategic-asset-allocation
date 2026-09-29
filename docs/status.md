# Status

Where the project stands against `Agentic_SAA_12Week_Project_Plan.md`. Update this when a phase
item lands; it is the first thing a new session should read after `CLAUDE.md`.

**As of 2026-09-29** (project week 3 of 12). `main` has 159 passing tests.

## By pipeline stage

| Stage | State | Owner |
|---|---|---|
| Data layer: 8 sources, 14 datasets, 18-asset history, validation | Done | Sajal |
| Historical-analysis skill | Done | Sajal |
| IPS (`config/ips.yaml`, `check_compliance`) | Done, v0.2 draft with faculty answers | Shambhawi |
| Output contracts (16) + generated schemas | Done | Shambhawi |
| LLM layer (routing, budget, retries) | Done | Shambhawi |
| 1. Macro regime agent | Done: scoring skill + agent + `regime_history` | Shambhawi |
| Macro-inputs skill, run context, contracts migration | **In review** (see below) | Sajal |
| 2. Asset-class agents, CMA methods | Not started (plan weeks 4-5) | Sajal + Shambhawi |
| 3. Covariance agent | Not started (week 5) | Sajal |
| 4. Portfolio-construction agents (10) | Not started (weeks 5-6) | both |
| 5. CRO, peer review, Borda vote | Not started (weeks 7-8) | both |
| 6. CIO agent + board memo | Not started (week 9) | Shambhawi |
| Backtest, stress tests, visualisation | Not started (weeks 10-12) | both |

**Milestone M1 (data + macro layer live, week 3): met**, once the branch below merges.

## Open pull request

`feature/phase1-contracts-and-macro-inputs` was raised before the macro agent landed and now
overlaps it. It should be reconciled against `main` before more work builds on either side:

1. **Keep:** `saa.run.RunContext` (run id, directory layout, header). The macro agent currently
   builds its own run id inline; it should use this instead.
2. **Keep:** the historical-analysis migration onto the shared contracts (`main` still has
   duplicate models in `skills/historical_analysis/models.py`).
3. **Keep:** the integration tests and the data-quality report (`docs/data_quality_report.md`,
   which exists on that branch only).
4. **Drop:** the `macro_inputs` skill. `skills/macro_regime/scoring.py` on `main` covers the same
   transforms, and it is the version the macro agent already uses.

## Decisions still open

| Question | Who decides | Blocks |
|---|---|---|
| Units: decimals vs percent across contracts (decision 15) | Sajal + Shambhawi | CMA agents, week 4 |
| IPS ratification as a whole (`status: draft` today) | Prof. Glasserman | Nothing yet; every header records the draft status |
| Should exceeding the return target really disqualify a portfolio? | Prof. Glasserman | CRO agent, week 7 |
| Orchestration across stages: how the six stages are run end to end | Shambhawi | Week 6 onward |

## Next, in order

1. Reconcile the open PR against `main` (above).
2. Settle units before the CMA work starts.
3. Covariance skill → `covariance.json` (sample, Ledoit-Wolf, exponential estimators).
4. WRDS valuation ingestion: Compustat CAPE and buybacks, I/B/E/S growth, CRSP market caps —
   needed by three of the six CMA methods.
5. CMA method calculators → `cma_methods.json` for all 18 assets, then the CMA judge agent.

## Data facts worth not re-deriving

- All 18 assets have monthly returns from **1993-06**; most from 1980. ETFs alone would start 2010-06.
- **8 of 62** FRED series carry true ALFRED vintages; the earliest starts 1991, the latest 2016.
- Latest validation: **266 checks pass, 1 warning, 0 failures**. The warning is USD EM Debt
  starting 1993-06 rather than 1990.
- Yahoo ETF returns match CRSP within **0.45%** annualised tracking error for all 18 ETFs.
- CRSP stock and index data end **2024-12**; ETFs cover later months.

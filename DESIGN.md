# Design

How the pipeline is built and why. Paper references are to Ang, Azimbayev & Kim (2026),
*The Self-Driving Portfolio*. For progress see `docs/status.md`; for the reasoning behind
individual choices see `docs/decisions.md`.

## The pipeline

Six stages, each writing JSON contracts plus a markdown narrative that the next stage reads.

```
                    config/ (universe, macro series, IPS, scoring)
                                      |
  8 sources -> data lake (versioned parquet, point-in-time) -> DataStore
                                      |
   +----------------+-----------------+--------------------+
   |                |                 |                    |
1. macro agent   2. asset-class    3. covariance      (deterministic skills
   regime call      agents x18        agent            feed all of them)
   macro-view.json  cma.json          covariance.json
                                      |
                          4. portfolio construction agents
                             pc_proposal.json
                                      |
                          5. strategy review: CRO report,
                             peer reviews, Borda vote
                                      |
                          6. CIO agent: ensemble + board memo
                             cio_decision.json
```

Stages 1-4 exist today: the macro agent; the CMA methods, signals, judge and validation behind stage 2; the covariance skill; and the 11 PC agents. Stages 5-6 (review, vote, CIO) are Phase 3 work (`docs/status.md`).

## Layers

**Config is the source of truth.** `load_config()` parses and cross-validates every YAML file:
the 18-asset universe, 62 FRED series, the IPS, source settings, and the macro scoring weights.
Cross-validation fails loudly — a CMA series not declared in `macro_series.yaml`, a benchmark
weight on an asset outside the universe, a history link naming an unknown dataset.

**The data layer** turns eight public and licensed sources into 14 curated tables. Each
ingestion run writes immutable parquet versions plus a catalog entry with row counts, date
ranges and a SHA-256, so any later result can name the exact bytes it used. Per-item failures
are warnings, and an entity a source fails to deliver is carried forward from the previous
version rather than silently disappearing.

**`DataStore` is the only read path.** It serves wide frames (prices, returns, macro, curves,
factors, surveys) and enforces point-in-time semantics. The first read of a dataset pins its
version, and `provenance()` reports those pins for the output header.

**Skills are deterministic.** A skill is a `SKILL.md` methodology document plus Python that
computes: `historical_analysis` (returns, risk, drawdowns, correlations per asset) and
`macro_regime` (transforms, indicator scoring, regime classification), `covariance`
(sample, Ledoit-Wolf, exponential and regime-conditional estimators) and `cma_methods` (every
candidate expected return per asset, the input to the CMA judge). They never call a model,
so they are testable, cheap, and identical across runs.

**Agents add judgment.** Following §3.2 an agent is four things: an `AGENT.md` description read
at runtime, scripts, skills, and an output contract. The macro agent scores the four dimensions
deterministically, hands the model a table it may not recompute, and asks only for the regime
call, confidence, recession probability and narrative.

## Point-in-time

The paper backtests 1996-2026, so every look-ahead-sensitive row carries `available_from`, the
first date the value could have been known:

- **Revised macro series** (8 of 62) keep ALFRED vintages: the value *as published then*. Their
  vintages start as late as 2011, so earlier dates fall back to revised values with estimated
  release dates, and the contract records which case applied (`point_in_time`, `pit_quality`).
- **Everything else** uses period end plus a per-source release lag: one day for market data,
  about 60 for the Ken French library.
- **`evaluation_only` series** (NBER recession dates) are excluded from as-of queries entirely.

`DataStore(as_of=...)` applies all of this, so a 2020-04-01 run sees February payrolls and an
unrecovered COVID drawdown.

The paper's own caveat (§5.1) still stands: an LLM's training data leaks future knowledge that
no data discipline can remove. Backtests are indicative, not clean out-of-sample evidence.

## Return history for 18 asset classes

ETFs only overlap from 2010, which is too short for the paper's 1996-2026 backtest. So
`data/history.py` splices each asset month by month: the ETF where it exists, otherwise the
first available link in that asset's chain in `config/universe.yaml` — index funds, futures,
Ken French portfolios, synthetic par-bond returns from Treasury yields, CRSP indexes, or World
Bank prices. Every month records its source, and every link is scored against its own ETF over
their overlap. Those tracking errors decided the ordering and are published in
`docs/asset_data_map.md`. All 18 assets now reach 1993-06, most 1980.

## Contracts

Every file is `header` + `body`:

- **The header is machine-written**: contract name, agent, pipeline run id, `as_of`, producer,
  dataset provenance, upstream inputs, IPS version and status, model calls, report path.
- **The body is the agent's output.** Where a stage both computes and judges, the body holds a
  deterministic half and a judgment half, and `Producer` records which is which.
- **The LLM is constrained to the judgment model only** via structured outputs, so it cannot
  fabricate provenance, token counts or a run id.
- **Extra fields are forbidden**, which is what makes the generated schemas strict and a
  renamed field fail loudly.
- **Percent is the unit**, marked by a `_pct` suffix (5.0 = 5%), because that is how the paper
  and the IPS state their figures. Ratios such as Sharpe and correlation carry no suffix.

`contracts/registry.py` lists all 16 contracts with their filename, stage and producer;
`uv run saa-contracts` regenerates `schemas/`, and a test fails if they drift.

## Runs and reproducibility

```
data/runs/<pipeline_run_id>/
  macro/macro-view.json, regime_history.json
  cma/<asset_id>/{historical_stats,correlation_row,cma_methods,cma,signals,scenarios}.json
  pc/{covariance.json, <agent_id>/pc_proposal.json}
  review/{<agent_id>/{cro_report,vote}.json, vote_tally.json}
  cio/cio_decision.json
  reports/*.md
```

One run id ties every file together; each header names the dataset versions it read. The layout
and header are owned by a single run context rather than by each agent, so paths and run ids
cannot drift apart (`saa.run.RunContext`, pending merge — see `docs/status.md`). Ingestion logs
live separately from pipeline runs.

## The IPS

`config/ips.yaml` encodes the paper's three layers — universe, objectives (CPI + 3-4% real,
8-12% volatility, -25% drawdown), and a 6% tracking-error budget against a 60/40 benchmark — as
machine-readable rules. `ips.check_compliance()` is the single implementation the CRO and CIO
agents share, so the rules cannot drift apart. Metrics that do not exist yet land in
`not_evaluated`, never in "passed": a report can be compliant while having verified nothing.

Faculty answered the open questions on 2026-09-25 (v0.2): every limit binds hard, and there are
no per-asset or per-group weight limits, leaving volatility, drawdown and tracking error as the
binding constraints. The document stays `draft` until it is ratified as a whole, and every agent
records which version and status it ran under.

## The LLM layer

`llm.py` wraps the Messages API: tier-to-model routing (`FLAGSHIP` → Opus, `LOW_COST` → Sonnet),
schema-constrained judgments with retries, per-call cost estimation, and a run-level `Budget`
that warns at 80% and stops at a boundary rather than mid-fan-out. Every call is recorded in
`header.model_calls`, which also makes the paper's §5.1 monoculture question answerable after
the fact.

## Testing

- **Unit tests** cover every parser, metric and rule, including hand-calculated cases.
- **Contract tests** validate round-trips and pin the schemas against the models.
- **Integration tests** run against a real data lake and skip cleanly without one, so a fresh
  clone passes.
- **Fakes, not network**: LLM and source clients are injected in tests.

## Extending

| Task | Steps |
|---|---|
| New data source | `DatasetSpec` in `data/datasets.py` → `Source` subclass → register → settings in `data_sources.yaml` → validation check → parser test |
| New contract | model in `contracts/` → register in `registry.py` → `uv run saa-contracts` → bump `SCHEMA_VERSION` |
| New skill | folder with `SKILL.md` + pure Python → unit tests → expose on `saa-skill` |
| New agent | folder with `AGENT.md` + `agent.py` → judgment model → write through the contract → expose on `saa-agent` |

## Known limits

Gold before 2000 and commodities before 2006 are the weakest proxies; international corporates
reuse the sovereign proxy before 2010; ICE BofA credit spreads on FRED cover only three years;
CRSP ends 2024-12; and the ETF fundamentals snapshot only accumulates going forward.
`docs/asset_data_map.md` lists, per asset, which proxy covers which months and how well it
tracks — the list of things to disclose when reporting results.

# CLAUDE.md

Working rules for this repository. Read this first; it is deliberately short and points at the
document that carries the detail, so a session does not have to read the codebase to start.

**What this is:** a scaled replication of Ang, Azimbayev & Kim (2026), *The Self-Driving
Portfolio* — LLM agents that classify the macro regime, build capital market assumptions for 18
asset classes, construct portfolios, peer-review and vote on them, and produce a CIO allocation
plus a board memo. Python 3.11+, `uv`, pandas, pydantic, Anthropic SDK.

| Question | Document |
|---|---|
| How is it built, and why in that shape? | `DESIGN.md` |
| What is done, what is next, what is blocked? | `docs/status.md` |
| Why was a choice made (and what was rejected)? | `docs/decisions.md` |
| What data exists, how good is it? | `docs/data_sources.md`, `docs/asset_data_map.md` |
| What must each agent output? | `docs/contracts.md`, `schemas/` |
| What constrains a portfolio? | `docs/ips.md`, `config/ips.yaml` |
| How does one skill or agent work? | its own `SKILL.md` / `AGENT.md` beside the code |

## Commands

```bash
uv sync                                   # environment
uv run pytest                             # all tests (integration ones skip without a data lake)
uv run ruff format src tests && uv run ruff check src tests --fix

uv run saa-data ingest                    # fetch every source, build history, validate
uv run saa-data validate | status         # data-quality report | dataset versions
uv run saa-data wrds-login | wrds-check   # licensed CRSP access (optional)
uv run saa-skill historical-analysis      # per-asset return/risk statistics
uv run saa-skill covariance               # 18x18 covariance matrix (Ledoit-Wolf default)
uv run saa-skill cma-methods              # every CMA candidate per asset -> cma_methods.json
uv run saa-skill signals                  # asset-level macro/technical/valuation signals
uv run saa-skill cma-validate --run-id <run>  # CMA layer vs expected ranges
uv run saa-agent macro [--no-llm]         # stage 1: macro regime
uv run saa-agent cma-judge --run-id <run> # stage 2: select the final CMA per asset
uv run saa-agent pc --run-id <run> [--no-llm]   # stage 4: the 11 PC agents
uv run saa-contracts                      # regenerate schemas/ after changing a contract
```

## Map

```
config/       universe.yaml (18 assets) · macro_series.yaml (62 FRED series) · ips.yaml
              macro_scoring.yaml · signals.yaml · data_sources.yaml · cma_inputs.yaml
              cma.yaml · cma_validation.yaml · wrds.yaml
src/saa/
  config.py   loads and cross-validates every config file; `load_config()`
  ips.py      IPS model + `check_compliance()` — the CRO and CIO share this one function
  llm.py      Anthropic client: model tiers, budget, retries, schema-constrained judgments
  contracts/  one model per JSON file the pipeline writes; `registry.py` is the index
  data/       sources/ (8 connectors) · lake.py (versioned parquet) · store.py (DataStore)
              history.py (18-asset spliced returns) · equity_valuation.py (WRDS group
              aggregates) · validation.py · pipeline.py
  skills/     deterministic, no LLM: historical_analysis/ · macro_regime/ · covariance/
              cma_methods/ · signals/ · portfolio_construction/
  agents/     LLM agents: macro/ · cma_judge/ · pc/ · pc_researcher/ (each AGENT.md + agent.py)
schemas/      generated JSON Schemas — never edit by hand
data/         git-ignored: raw payloads, curated parquet, runs/, reports/
```

## Rules

**Data**
- Tickers and series IDs live in `config/`, never in code.
- Agents and skills read data only through `DataStore`. No direct file or network reads.
- Anything that feeds a backtest passes `as_of`; respect `available_from` and never use
  `evaluation_only` series (NBER dates) as an input.
- Record `store.provenance()` in every output header.

**Licensed data (WRDS/CRSP)**
- Never commit or publish WRDS data itself: extracts, firm- or bond-level rows, or the
  curated `wrds/` datasets stay in git-ignored `data/`. Research results computed from them
  (CMA estimates, validation statistics, evidence tables) may be published (owner's
  ruling, 2026-10-01).
- Every WRDS-backed history link has a public fallback, so the pipeline still runs without
  credentials. Keep it that way.

**Contracts**
- Change a contract model → `uv run saa-contracts` → `uv run pytest` → bump `SCHEMA_VERSION`
  in `contracts/base.py` (minor for additive, major for breaking).
- The header is machine-written. An LLM only ever fills a *judgment* model nested in the body.
- Models forbid extra fields. A renamed field must fail loudly, not vanish.
- Percent everywhere, named `_pct` (5.0 = 5%). Ratios — Sharpe, beta, correlation — carry no
  suffix. `metrics.py` returns decimals and the skill converts once at the boundary.

**Agents and LLM**
- An agent is four things (paper §3.2): an `AGENT.md` description, scripts, skills, and an
  output contract. Keep arithmetic in scripts and judgment in the model.
- Skills never call an LLM. If it needs a model, it belongs in an agent.
- Route by tier (`Tier.FLAGSHIP` for judgment, `Tier.LOW_COST` for formatting) and record every
  call in `header.model_calls`; the project's total API budget is $210–290.
- Every agent states in its narrative that the IPS is a draft while `ips.status == "draft"`.

**Code**
- `ruff format` + `ruff check` before committing; line length 100.
- Comments explain *why*; the code already says what.
- New parser, metric or rule gets a unit test. Integration tests must skip without a data lake.
- Choices between methods are settled with measured evidence (e.g. tracking error), and the
  number goes in the doc that records the choice.

**Git**
- Branch per piece of work, PR into `main`; never commit `data/`, `.env`, `*.pdf`, or credentials.
- Sync with `main` before starting: two people work in parallel here.

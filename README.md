# Agentic Strategic Asset Allocation

A scaled replication of Ang, Azimbayev & Kim (2026), *The Self-Driving Portfolio*: LLM agents
for macro regime classification, capital market assumptions, portfolio construction, peer
review, and a CIO ensemble. See `Agentic_SAA_12Week_Project_Plan.md` for scope and milestones.

**Current status:** Phase 1 data layer (ingestion, validation, point-in-time access) and
the IPS that governs every downstream agent (`docs/ips.md`, draft pending faculty
ratification), plus the output contracts every agent reads and writes (`docs/contracts.md`).

## Setup

```bash
uv sync                      # Python >= 3.11; creates .venv with runtime + dev dependencies
cp .env.example .env         # add FRED_API_KEY (free) for revision vintages and metadata
uv run saa-data ingest       # fetch all sources, build asset return history, validate
uv run saa-data status       # dataset versions, row counts, date ranges
uv run saa-data validate     # re-run data-quality checks
uv run saa-data build-history  # rebuild spliced monthly returns without re-downloading
uv run saa-skill historical-analysis [--as-of YYYY-MM-DD]  # per-asset stats and correlations
uv run saa-contracts        # regenerate schemas/ after changing a contract model
uv run pytest
```

Ingest a subset with `uv run saa-data ingest --sources fred yahoo`. Available sources are
`fred`, `yahoo`, `french`, `treasury`, `shiller`, `spf`, `worldbank` and `wrds`. All are public
except `wrds` (licensed CRSP data), which is skipped without WRDS credentials.

## WRDS (licensed, optional)

The pipeline runs on public data alone. With a WRDS account, do a one-time login so later
connections are non-interactive (approve the Duo prompt if one appears):

```bash
# 1. add WRDS_USERNAME=<your username> to .env
# 2. in your own terminal: prompts for the password, tests it, and saves it to
#    %APPDATA%\postgresql\pgpass.conf (~/.pgpass on macOS/Linux), never to the repo
uv run saa-data wrds-login
# 3. see which relevant WRDS tables your subscription can read
uv run saa-data wrds-check
```

Queries use `psycopg2` directly. The official `wrds` package is not used because it pins
SQLAlchemy < 2, which pandas 3 cannot use.

WRDS data is licensed to you: it stays in the git-ignored `data/` folder and must never be
committed, published, or put in shared dashboards.

## Layout

```
config/
  universe.yaml        the 18 asset classes: ETF, pre-ETF history chain, CMA series
  macro_series.yaml    FRED series by macro dimension, release lags, vintage flags
  cma_inputs.yaml      data inputs for the 6 CMA methods (+ auto-blend), with known gaps
  data_sources.yaml    source endpoints, rate limits, validation thresholds
  ips.yaml             Investment Policy Statement: universe, objectives, risk budget
src/saa/
  config.py            typed config loading and cross-validation
  ips.py               IPS model and check_compliance(), shared by the CRO and CIO agents
  contracts/           agent output contracts: one model per JSON file the pipeline writes
  cli.py               `saa-data` command
  data/
    sources/           one connector per source (FRED, Yahoo, French, Treasury, Shiller, SPF, World Bank, WRDS)
    wrds_client.py     psycopg2 WRDS client and password-file login
    wrds_access.py     `saa-data wrds-check`: which WRDS tables the account can read
    datasets.py        canonical dataset schemas (the contract with the agents)
    lake.py            versioned parquet lake + catalog
    history.py         18-asset monthly returns: ETF spliced with public proxies, with diagnostics
    pipeline.py        fetch -> archive raw -> merge -> write -> build history -> validate
    validation.py      freshness, coverage, outlier and key checks
    store.py           DataStore: point-in-time read API for agents and skills
  skills/              deterministic skills agents call (SKILL.md methodology + Python, no LLM)
    historical_analysis/  returns, risk, drawdowns, correlations -> historical_stats.json
docs/data_sources.md   source rationale, point-in-time rules, gaps and alternatives
docs/ips.md            the IPS in narrative form, and the numbers awaiting ratification
docs/contracts.md      the output contracts, and the paper rules they validate
schemas/               generated JSON Schemas (`uv run saa-contracts`)
data/                  (git-ignored) raw payloads, curated versions, run logs, reports
```

## Using the data from agents and skills

Agents never read files directly. They use `DataStore`, which pins dataset versions and can
serve point-in-time views:

```python
from saa.data import DataStore

store = DataStore()
history = store.asset_returns(start="1990-01-31")              # 18 assets, monthly, ETF + proxies
sources = store.asset_returns(field="source")                  # which source each month used
links = store.history_links()                                  # proxy tracking error vs. ETF
monthly = store.returns(freq="M")                              # ETF-only returns (from inception)
growth = store.macro(dimension="growth", as_of="2020-03-31", freq="M")  # only data public then
curve = store.yield_curve("nominal", as_of="2026-03-31")
cape = store.shiller()["cape"]
stock10 = store.survey("STOCK10", horizon="point")             # SPF 10y S&P 500 return forecast

store.provenance()   # {"market/prices_daily": {"run_id": ..., "sha256": ...}, ...}
```

Record `provenance()` in each agent's JSON output. To reproduce a past pipeline run, pass
the recorded versions to `DataStore(run_ids={...})`.

## Checking a portfolio against the IPS

Every agent reads the IPS; the CRO agent checks each candidate portfolio against it and the
CIO agent is bound by it. Both call one function, so the rules cannot drift apart:

```python
from saa.config import load_config
from saa.ips import PortfolioMetrics, check_compliance

config = load_config()
metrics = PortfolioMetrics(expected_volatility_pct=9.8, ex_ante_tracking_error_pct=3.1)
report = check_compliance(weights, metrics, config.ips, config.universe)

report.compliant      # False if any hard violation -- the CIO may not select it
report.hard           # disqualifying violations
report.soft           # flag in the board memo, do not disqualify
report.not_evaluated  # rules no metric was supplied for; not the same as passing
report.to_dict()      # embed in risk_report.json / cio_decision.json
```

`config.ips.is_draft` is true until the policy is ratified; agents should say so in their
output. See `docs/ips.md` for the three layers, the benchmark choice, and the open questions.

## Data layer design

- **Config-driven.** Tickers and series IDs live only in `config/`.
- **Versioned and reproducible.** Each ingestion run writes immutable curated parquet files
  (`data/curated/<dataset>/<run_id>.parquet`), archives raw payloads, and logs to `data/runs/`.
- **Resilient.** Per-item failures are recorded as warnings. Entities a source fails to deliver
  are carried forward from the previous version instead of disappearing.
- **Point-in-time.** Every look-ahead-sensitive row has an `available_from` date, and revised
  macro series keep ALFRED vintages.
- **Validated.** Each run writes `data/reports/validation_<run_id>.json`, covering freshness,
  history start vs. fund inception, return outliers, gaps, key uniqueness and the common
  sample start across all 18 ETFs.

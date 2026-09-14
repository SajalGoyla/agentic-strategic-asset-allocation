# Agentic Strategic Asset Allocation

A scaled replication of Ang, Azimbayev & Kim (2026), *The Self-Driving Portfolio*: LLM agents
for macro regime classification, capital market assumptions, portfolio construction, peer
review, and a CIO ensemble. See `Agentic_SAA_12Week_Project_Plan.md` for scope and milestones.

**Current status:** Phase 1 data layer (ingestion, validation, point-in-time access).

## Setup

```bash
uv sync                      # Python >= 3.11; creates .venv with runtime + dev dependencies
cp .env.example .env         # add FRED_API_KEY (free) for revision vintages and metadata
uv run saa-data ingest       # fetch all sources, write the versioned lake, validate
uv run saa-data status       # dataset versions, row counts, date ranges
uv run saa-data validate     # re-run data-quality checks
uv run pytest
```

Ingest a subset with `uv run saa-data ingest --sources fred yahoo`. Available sources are
`fred`, `yahoo`, `french`, `treasury`, `shiller` and `spf`.

## Layout

```
config/
  universe.yaml        18 asset classes: ETF proxy, backfill fund, history proxy, CMA series
  macro_series.yaml    FRED series by macro dimension, release lags, vintage flags
  cma_inputs.yaml      data inputs for the 6 CMA methods (+ auto-blend), with known gaps
  data_sources.yaml    source endpoints, rate limits, validation thresholds
src/saa/
  config.py            typed config loading and cross-validation
  cli.py               `saa-data` command
  data/
    sources/           one connector per source (FRED, Yahoo, French, Treasury, Shiller, SPF)
    datasets.py        canonical dataset schemas (the contract with the agents)
    lake.py            versioned parquet lake + catalog
    pipeline.py        fetch -> archive raw -> merge -> write -> validate
    validation.py      freshness, coverage, outlier and key checks
    store.py           DataStore: point-in-time read API for agents and skills
docs/data_sources.md   source rationale, point-in-time rules, gaps and alternatives
data/                  (git-ignored) raw payloads, curated versions, run logs, reports
```

## Using the data from agents and skills

Agents never read files directly. They use `DataStore`, which pins dataset versions and can
serve point-in-time views:

```python
from saa.data import DataStore

store = DataStore()
monthly = store.returns(freq="M")                              # 18 ETFs, total returns
growth = store.macro(dimension="growth", as_of="2020-03-31", freq="M")  # only data public then
curve = store.yield_curve("nominal", as_of="2026-03-31")
cape = store.shiller()["cape"]
stock10 = store.survey("STOCK10", horizon="point")             # SPF 10y S&P 500 return forecast

store.provenance()   # {"market/prices_daily": {"run_id": ..., "sha256": ...}, ...}
```

Record `provenance()` in each agent's JSON output. To reproduce a past pipeline run, pass
the recorded versions to `DataStore(run_ids={...})`.

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

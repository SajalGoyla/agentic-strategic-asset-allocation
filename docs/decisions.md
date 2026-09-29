# Decision log

One entry per decision that would otherwise be re-litigated or silently reversed: what we chose,
why, and what it costs. Newest last. Status is **settled**, **provisional** (works, revisit when
cheap) or **open**.

---

### 1. Tickers and series IDs live in config, never in code — settled, 2026-09-14
The paper names no ETF tickers and no FRED series. Every such choice is ours, so it belongs
where it can be reviewed and changed without touching code: `config/universe.yaml` and
`config/macro_series.yaml`. `load_config()` cross-validates them.

### 2. Public data first, licensed data as an upgrade — settled, 2026-09-15
The project had no paid data and no manual inputs; WRDS arrived later. Every asset therefore has
a public history chain, and CRSP links sit *in front of* those public links rather than replacing
them. Consequence: the pipeline still runs for a collaborator without WRDS, with slightly
different pre-ETF history, and licensed extracts never have to leave `data/`.

### 3. Splice pre-ETF history, ordered by measured tracking error — settled, 2026-09-15
ETFs only overlap from 2010; the paper backtests from 1996. Each asset gets an ordered chain of
proxies, chosen by scoring candidates against their own ETF over the overlap (about 950 CRSP
funds were tested). Evidence overturned intuition twice: returns computed from Treasury yields
beat the index funds, and Moody's-yield synthetics lost badly to a corporate bond fund.
Consequence: every month carries its source, and weak links (gold pre-2000, commodities
pre-2006) are disclosed rather than hidden. See `docs/asset_data_map.md`.

### 4. Availability dates on every row, not a backtest-time filter — settled, 2026-09-15
Look-ahead is prevented at the data layer: each row carries `available_from`, revised series keep
ALFRED vintages, and NBER dates are marked `evaluation_only`. Doing it later, in each agent,
would mean re-deciding it eighteen times. Cost: vintages only start in 1991-2016 depending on the
series, so early backtest dates fall back to revised values — recorded per indicator rather than
glossed over.

### 5. Immutable dataset versions with a catalog — settled, 2026-09-14
Each ingestion writes a new parquet file per dataset and records rows, date range and SHA-256.
Agents pin versions through `DataStore.provenance()`. This is what makes a run reproducible after
the data has moved on; the cost is disk, which is trivial at this size.

### 6. `psycopg2` directly instead of the official `wrds` package — settled, 2026-09-15
The `wrds` package pins SQLAlchemy < 2, which pandas 3 cannot use; every query failed with a
confusing cursor error. We query WRDS over `psycopg2` and keep a `saa-data wrds-login` command
for the password file. Consequence: one less dependency conflict, and no interactive prompt can
hang a pipeline.

### 7. The contract envelope is machine-written — settled, 2026-09-16
Every output is `header` + `body`; the model only fills a judgment model nested in the body.
An agent therefore cannot invent its own provenance, cost or run id, and the schema handed to the
API stays small. Extra fields are forbidden so a rename fails loudly.

### 8. Deterministic skills, judgment in agents — settled, 2026-09-16
Following §3.2, arithmetic lives in skills that never call a model, and agents reason about the
results. This keeps runs reproducible, tests cheap, and the API bill attributable.

### 9. One definition per contract — settled, 2026-09-17
The historical-analysis skill briefly carried its own copies of the models it writes. They were
deleted; the skill now builds `saa.contracts` models directly, and a test asserts it. Duplication
that "mirrors field for field" drifts the moment either side changes.

### 10. Pipeline runs are a first-class object — settled, 2026-09-17
`saa.run.RunContext` owns the run id, the directory layout and the header. Without it each agent
invents its own paths. Ingestion logs moved to `data/ingestion_runs/` so `data/runs/` means one
thing. *(Landed on branch `feature/phase1-contracts-and-macro-inputs`; see `docs/status.md`.)*

### 11. IPS as machine-readable policy with provenance tags — settled, 2026-09-16
Each number in `config/ips.yaml` is tagged `[paper]`, `[faculty]` or `[proposed]`, and
`check_compliance()` is shared by the CRO and CIO. Encoding the paper literally disqualified the
paper's own example portfolio, which is what made the faculty conversation concrete.

### 12. Faculty answers: every limit binds hard, no weight limits — settled, 2026-09-25
Prof. Glasserman: treat the IPS limits as hard constraints, allow no leverage or shorting, and
impose no per-asset or per-group weight bounds — "why rule out the possibility of going all in on
one asset class". The binding constraints are therefore the 8-12% volatility band, the -25%
drawdown limit and the 6% tracking-error budget. Two consequences worth watching: a portfolio
forecast to earn *more* than CPI + 4% is disqualified like one that earns less, and unbounded
weights make the deliberation protocol, not the constraint set, the thing that keeps portfolios
sensible. The 60/40 benchmark is 60% US Large Cap / 30% Intermediate Treasuries / 10% IG
Corporates. `status` stays `draft` until the document is ratified as a whole.

### 13. Model routing, budget and retries in one place — settled, 2026-09-28
`llm.py` maps `Tier.FLAGSHIP` to Opus and `Tier.LOW_COST` to Sonnet, constrains output to the
judgment schema, retries twice, prices each call, and enforces a run budget that stops at a stage
boundary rather than mid-fan-out. The project's total API budget is $210-290, so per-call cost is
recorded from the first call rather than reconstructed later.

### 14. The macro agent may overrule the rule-based regime, but must say so — settled, 2026-09-28
The scoring script's classification is given to the model as a prior, not an instruction. This
keeps the paper's "LLM handles judgment" property while leaving an audit trail when the model
departs from the arithmetic.

### 15. Units: decimals in historical stats, percent everywhere else — open
`historical_stats` and `correlation_row` use decimals (0.05 = 5%); the IPS, CRO, CIO and board
memo use percent, as the paper states its figures. Nothing converts silently and the suffix says
which (`max_drawdown` vs `max_drawdown_pct`), but the split should be settled before the CMA
agents read both. Standardising on percent changes one module; on decimals, five.

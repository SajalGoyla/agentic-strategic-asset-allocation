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

### 15. Percent everywhere, with a `_pct` suffix — settled, 2026-09-29
`historical_stats` and `correlation_row` briefly used decimals because the skill computes them
that way, while the IPS, CRO, CIO and board memo used percent, as the paper states its figures.
Two conventions in one pipeline is a bug waiting for the CMA agents, which read the first and
write the second. Percent won: it matches the paper and changed one module instead of five.

A field carrying a percentage now ends in `_pct` and holds 5.0 for 5%; ratios (Sharpe, Sortino,
beta, correlation, skewness, kurtosis) keep no suffix. `metrics.py` still returns decimals,
because it is generic statistics code, and the skill converts once at the boundary.
Consequence: renaming fields breaks any reader, so `SCHEMA_VERSION` went to 1.0.0 under the
rule in `contracts/base.py` (major for a breaking change). That is a statement about the
contract format, not a claim that the project is finished.

### 16. Covariance matrices in decimal-squared, volatilities in percent — settled, 2026-09-29
`CovarianceBody.matrix` is what optimisers consume, so it stays in decimal-squared (a 20%
volatility is a variance of 0.04); `volatilities_pct` follows the percent rule. A covariance is
not a percentage, so this is not an exception to decision 15 — but the two numbers must agree,
and the contract validator now rejects a matrix whose implied volatility is off by more than
rounding. That catches a matrix written in percent-squared, which would be 100x off.

### 17. Ledoit-Wolf over all history is the default covariance — settled, 2026-09-29
Chosen by an out-of-sample test on 1993-2026 data (`skills/covariance/SKILL.md`). Risk forecasts
from all estimators were within noise of each other, so robustness decided it: the sample and
exponential estimators were singular in every year before 2008, because International
Sovereigns and Corporates share a proxy fund until 2007, while Ledoit-Wolf never was. Over all
history it also gave the best-conditioned matrices and the most accurate benchmark-volatility
forecast. The a-priori default of a 10-year window lost on every measure and was dropped. The
exponential estimator stays as the reactive alternative, with a 60-month half-life.
Consequence: any optimiser downstream can invert the matrix at every backtest date.

### 18. A fixed-income CMA method, and no placeholder numbers — settled, 2026-09-29
Exhibit 4's six methods are written for equities; §3.3 separately gives fixed-income agents "a
fixed-income CMA builder emphasising yield and credit-spread duration". It is now a method of
its own, `yield_building_block` (starting yield less expected credit losses), so bond and cash
agents get a yield-based candidate and not only historical ones. A method that does not apply
or lacks data now carries `expected_return_pct: null` and zero confidence, rather than a number
an LLM could mistake for an estimate, and every `cma_methods.json` lists all eight methods in
the same order. Making a required field nullable breaks readers, so `SCHEMA_VERSION` is 2.0.0.

### 19. CMA candidates are arithmetic, nominal, annual percent — settled, 2026-09-29
Optimisers take arithmetic means, and the historical and Black-Litterman methods produce them
natively. Yield, Gordon and survey methods produce compound returns, so they add half the
variance as an explicit `variance_addback_pct` component. The CAPE method adds expected
inflation (SPF CPI10) to the earnings yield: the paper's formula compares a real yield with
nominal candidates. Consequence: the judge compares like with like, and at 15% volatility the
add-back is about 1.1pp, which is worth knowing when reading the paper's figures side by side.

### 20. The regime-adjusted premium is predictive — settled, 2026-09-29
Averaging returns *during* past months in the current regime uses hindsight: a month is
labelled recession partly because of the crash in it. The method averages the excess return
over the 3-year horizon *after* each such month instead, then shrinks it toward the
unconditional premium (credibility weight n/(n+60)). On real data this moved US Large Cap in
expansion from +13.7% to +9.7% excess, next to the paper's 9.8%.

### 21. Black-Litterman risk aversion 2.5 — provisional, 2026-09-29
Calibrated from 1990-2026, δ = 5.4, which scales every equilibrium premium up by 2.2x because the
sample's equity returns were unusually strong. The literature value 2.5 (He & Litterman 1999) is
the default; `risk_aversion: historical` in `config/cma.yaml` restores the calibration. Revisit
when WRDS market caps replace ETF AUM as the weights.

### 22. WRDS valuation as group aggregates, built in the pipeline — settled, 2026-09-29
The equity CMA methods need payout, earnings and book yields per asset class with history, and
only the S&P 500 has them publicly (Shiller). The WRDS source now rebuilds rule-based stand-ins
each month from CRSP (CIZ `msf_v2`; the legacy `msf` stops at 2024-12), Compustat and I/B/E/S:
the top 500 US common stocks, the top 1,000 split at median book-to-market, ranks 1,001-3,000,
and all REITs. Rank rules, not vendor membership lists, because the lists are not in WRDS for
all five groups and the rules are transparent and reproducible. Fundamentals count six months
after fiscal year-end, so each month is point-in-time. Only the aggregates are stored; the
firm-level extract is never written, which keeps the licensed footprint small. The large-cap
dividend yield tracks Shiller's closely, which validates the construction. WRDS Bond Returns
supplies IG/HY yields from 2002 and CRSP the ETFs' monthly market values. Its `t_spread` field
was rejected as sparse and mis-benchmarked. Consequence: every WRDS-backed input has a public
fallback, and the CMA rationale names the input actually used.

### 23. Gordon uses net payout; the CAPE method prefers the ETF's P/E — settled, 2026-09-29
The Gordon yield is dividends plus buybacks less issuance, which pairs with aggregate (GDP)
growth. Dividends alone understate US income return, because buybacks are larger. The CAPE
method keeps the ETF's trailing P/E when a snapshot exists, because the aggregate earnings of US
small caps can be negative (loss-makers the index vendor's P/E excludes). WRDS is used only for
earlier dates, and never when negative. A WRDS valuation older than 190 days is rolled forward by
the ETF's price change, up to 400 days, since CRSP and Compustat are released only a few times
a year.

### 24. International valuation from Compustat Global — settled, 2026-10-01
International Developed and Emerging Markets had valuation only from the fund snapshot, i.e.
none before 2026-09. Compustat Global supplies it from 1994 for the same rule-based groups as the
US: the 700 largest firms headquartered in MSCI EAFE countries and the 1,200 largest in MSCI EM
countries, in dollars. Three findings shaped it. Annual dividend fields are mostly empty (under
a fifth of Australian and French firms), so dividends come from the security file's payment
records as a trailing 12-month yield, the way index vendors quote it. Banks are filed in the
`FS` format, and reading it lifted coverage from about 70% to over 90% of market cap. A few
firm-months show yields in the thousands of percent after currency redenominations, so firm
yields above 25% are dropped. Validated against EFA/EEM's own snapshot figures (dividend yield
2.9% vs 3.1% developed). Consequence: the Gordon and CAPE candidates exist for both groups at
every backtest date. International buybacks are unknown, so the Gordon method counts them as
zero at reduced confidence. Rejected: matching MSCI's free-float and partial-inclusion weights,
which are not in WRDS.

### 25. Results derived from WRDS may be published — settled, 2026-10-01
The project owner ruled that research results computed from licensed data (CMA estimates,
validation statistics, evidence tables) can be committed to this public repo. The WRDS data
itself — extracts and the curated `wrds/` datasets — still never leaves git-ignored `data/`.
CLAUDE.md's licensed-data rule now says exactly that.

### 26. Signals skill: what is scored, and what is deliberately absent — settled, 2026-10-01
Exhibit 4 lists `signals.json` among the CMA judge's inputs, but the paper names the signals
without defining them, so the definitions and weights in `config/signals.yaml` are ours. Every
signal is scored to [-1, +1] where +1 is bullish for forward return, against the signal's own
20-year history, using the macro skill's `tanh(z/2)` mapping so the two read the same way.
Three things are left out on purpose. **Sentiment**: Exhibit 3 step 5 sources fund flows and
positioning from web search at runtime, which the pipeline does not do, so the category is
omitted rather than proxied. **An earnings-yield signal for equities outside US Large Cap**:
`market/fund_snapshot` only accumulates from the first ingest, so there is no history to judge
today's reading against; a signal scored 0.0 is not neutral evidence, it takes weight from
signals that do carry information, so nothing is emitted and the judge sees those valuations
through `cma_methods.json` instead. **A separate earnings yield for US Large Cap**: it is
1/CAPE, and emitting both would weight one piece of evidence twice. The composite renormalises
over the categories that produced signals, so an asset without a valuation signal is scored on
what it has rather than dragged toward zero.

### 27. The PC stage requires judged CMAs, even for methods that ignore them — settled, 2026-10-01
§3.1 step 4 has the PC agents take "the CMAs from step (2) and the covariance matrix from step
(3)". Equal weight and the inverse-risk methods choose weights without looking at expected
returns, so it was tempting to let them run before the judge. They cannot: `pc_proposal` still
has to report an expected return and a Sharpe ratio, which the CRO and the CIO both read.
Running without CMAs produced NaN in those fields, which pydantic serialised to `null`, which
then failed validation on read — the stage was writing files it could not read back. The stage
now raises with the command to run instead. `--no-llm` still works once the judge has run, and
remains free, so iterating on weights costs nothing.

### 28. Portfolio-construction methods work in decimals — settled, 2026-10-01
`covariance.json` stores the matrix in decimal-squared and the judged CMAs are percent, so the
PC methods had to pick one. They work in decimals, because that is the form π = δΣw and the
mean-variance formulas assume: in percent-squared the Black–Litterman equilibrium came out 100×
too large, implying a 634% equity premium, which is how the mistake was caught. `analysis.py`
converts once at the boundary — returns and the risk-free rate in, every statistic out — so
everything the pipeline writes stays percent, per decision 15.

### 29. The rest of the PC roster: which methods, and two definitions of ours — settled, 2026-10-08
The plan asks for 2-3 methods per Exhibit 5 family plus the researcher and the adversarial
diversifier. Risk-structured: risk parity and hierarchical risk parity, the plan's own
choices and both in the paper's top five. Non-traditional: CVaR minimisation and tail-risk
parity, the two of that family the paper's CIO weighted. Two definitions are ours. **Risk
parity** is solved through Spinu's (2013) convex programme rather than least squares on risk
contributions, which stalls when risks differ by two orders of magnitude (cash against
equities). **Tail-risk parity** is equal risk contribution on the downside semicovariance; an
expected-shortfall budget was rejected because a hedge with a negative tail contribution cannot
take an equal positive share, so no long-only solution need exist. Both are tested to give equal
contributions to machine precision on the real 18-asset data.

### 30. The PC-researcher chooses from an implemented library — settled, 2026-10-08
§3.4 has the researcher propose "a novel method not spanned by the current registry". A method
the pipeline cannot run cannot be reviewed or voted on, so the researcher chooses from
`RESEARCH_LIBRARY` — maximum entropy (the paper's own March 2026 proposal), maximum
diversification (first in the paper's vote) and global minimum variance — enforced by the
judgment schema's enum rather than the prompt. The judgment is which gap matters this run, read
from what the registry's portfolios actually look like. Promoting a successful proposal into
the registry is a code change, as the paper's "will be added to the registry" implies. It runs
at the flagship tier: one call, and the only open-ended judgment in the stage. Without a model
it proposes maximum entropy.

### 31. CMA validation thresholds — provisional, 2026-10-08
The plan's Phase 2 deliverable "validation of CMA outputs against expected ranges" needed
ranges, and the paper publishes final CMAs only for the equity classes (Exhibit 8). So only the
plausibility band fails an asset — it exists to catch unit slips and broken inputs, not views —
and every other check warns: bonds more than 2pp from their starting yield, an implied Sharpe
ratio outside [-0.1, 0.8], equities more than 3pp from the paper's judge value, and a
return-risk rank correlation below 0.3 across the 18. All thresholds are tagged [proposed] in
`config/cma_validation.yaml`; revisit after the first judged run.

### 32. IPS limits bind on the CIO's recommendation, not on each candidate — settled, 2026-10-08
With the full roster, 10 of 11 candidate portfolios break the IPS, mostly by sitting below the
8% volatility floor: every risk-based method concentrates in cash (0.6% volatility), and with no
leverage a low-risk mix cannot be scaled up to the band. The paper never asks candidates to
comply. Its CRO "scores risk and produces commentary, but does not vote" (§3.5); IPS compliance
is one input to the vote's metric score and 15% of the CIO's six-dimension score (§4.4); and the
CIO weights the adversarial diversifier at 3.1% despite a −46.3% drawdown that "would disqualify
it under any single-method selection rule". "Non-negotiable" (§3.6) is said of the CIO's choice
of ensemble. We adopted the same rule (project owner, 2026-10-08): candidates are checked by
`check_compliance` and their violations reported and scored, never disqualifying; the CIO may
recommend only a compliant portfolio, which `CioDecisionBody` already enforces. Faculty's
"treat them as hard constraints" therefore applies to the recommendation; to be confirmed.

Evidence on the free run (auto-blends standing in for judged CMAs): a simple average of the 11
portfolios gives 4.0% volatility and the paper's inverse-tracking-error ensemble 3.3%, but a
meta-optimisation over them constrained to the IPS reaches 8.0% volatility, Sharpe 0.47 and
2.9% tracking error (Sharpe 0.45 with no method above 25%). Rejected: forcing each optimiser into
the band, which turns risk parity into something else (contributions 0-7.1% instead of 5.6%
each) and collapses the diversity the vote exists to weigh; and dropping cash from the risk
methods, which only moves the concentration to short Treasuries (1.6-5.7% volatility).

**Superseded by decision 33.** Also considered and rejected at the time: adding market-cap
weight and volatility targeting, the paper's two largest CIO ensemble weights. They are not needed for a compliant recommendation — the
constrained meta-optimisation is identical with or without them — and they would grow the
heuristic family to five against the plan's 2-3 per family. The roster stays at 11: the plan's
three named heuristics (equal weight, inverse volatility, inverse variance), two methods in each
other family, the PC-researcher and the adversarial diversifier. (The paper runs 20 agents, 21
portfolios with the researcher's; the plan's "10 to start" counts two heuristics.)

### 33. A 15-agent PC roster, chosen from the paper's 20 for quality — settled, 2026-10-08
The paper is the source of truth and the plan's "10 PC agents to start" a floor, so the roster
was chosen on quality rather than to match a count (project owner, 2026-10-08). This supersedes
the last paragraph of decision 32, which rejected market-cap weight and volatility targeting on
the plan's 2-3-per-family scope. The 11 already built stay — inverse variance included, since
the paper's CIO gave it 6.0%, tied for third-largest — and four are added:

- **Maximum diversification** (risk-structured): first in the paper's peer vote. It was in the
  researcher's library, so the paper's top method ran only if the researcher happened to pick
  it; it is now in the registry.
- **Market-cap weight** (heuristic): the paper's largest CIO ensemble weight (11.1%), the
  neutral market reference the other methods are argued against.
- **Resampled efficient frontier** (return-optimised, Michaud 1998): the remedy for maximum
  Sharpe's concentration (6.1 effective assets against 1.6 on the 2026-10-01 inputs), giving
  the forecast-driven family a credible member in the vote; 4.1% in the paper's ensemble.
- **Volatility targeting** (heuristic): the paper's second-largest CIO weight (6.7%) and the
  only method aimed at the IPS volatility band.

Left out: global minimum variance (near-identical to CVaR minimisation here, 99% against 97%
cash; kept in the researcher's library), minimum correlation (overlaps maximum
diversification), robust mean-variance and mean-downside risk (overlap resampling and CVaR),
and max-drawdown-constrained and Total Portfolio Allocation (each needs substantial new
machinery; TPA scored lowest in the paper). Cost: about $0.43 per agent per full run at the
plan's estimates, almost all of it two flagship peer reviews — roughly $1.70 a run for the four,
+17% on the plan's $10. Effect on the free run: the paper's inverse-tracking-error ensemble
rises from 3.3% to 4.1% volatility; a meta-optimised ensemble constrained to the IPS still
reaches 8.0% volatility, Sharpe 0.47.

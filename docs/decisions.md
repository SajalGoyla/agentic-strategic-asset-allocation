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

### 32. IPS limits bind on the CIO's recommendation, not on each candidate — superseded in part by 37, 2026-10-08
**Superseded for the ex-ante limits by decision 37:** the volatility band and the tracking-error
budget now bind on every candidate. What still stands: the drawdown limit binds only on the
CIO's recommendation, and the CIO may recommend only a compliant portfolio.

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

### 34. The CRO's risk score is computed, not judged — settled, 2026-10-16
§3.5 says the CRO "scores risk and produces commentary", without saying which half of the agent
produces the score. It is a script here: a fixed, published formula over the metrics
(`skills/risk/SKILL.md`), with the components written into the contract so the number can be
audited. Two reasons. The CIO blends the CRO's score with the vote using a regime-dependent
weight (§3.5) and compares it across 15 candidates — a number a model assigns portfolio by
portfolio, each in its own call, is not comparable, and the paper's own CIO rubric gives IPS
compliance a fixed 15% rather than asking for a judgment. And a score that cannot be
re-derived from the run inputs cannot be checked by anyone reading the result.

The model's half is the reading: `key_risks`, `concentration_assessment`,
`tail_risk_assessment`, `ips_assessment` and `commentary`. The agent is told the score is not
its to re-weight and that disagreeing with it in the commentary is the useful move. Cost: the
score cannot reflect a risk nobody wrote a component for, which is why the commentary is a
required field and not an afterthought.

Two conventions the formula fixes, because the paper leaves them open: a portfolio **below** the
volatility floor scores 0 on the volatility component (it is non-compliant, not dangerous —
scoring it as risky would have ranked the cash-heavy portfolios as the most dangerous in the
roster), and a component with no data is dropped with the rest renormalised, so a candidate with
no backtest is never credited with zero risk. The second rule is the one the signals composite
already uses (decision 26).

### 35. Peer reviews are balanced, and a one-member family substitutes — settled, 2026-10-16
§3.5 says each agent reviews "exactly two peers — one from its own category ... and one from a
different category", randomised with a recorded seed. Two things it does not say.

**Balance.** A free random draw over 15 agents leaves some proposals with four reviews and
others with none, and an unreviewed proposal still goes to the vote carrying its own unexamined
case. So each reviewer picks the eligible peer with the fewest reviews so far, ties broken by
the seeded shuffle; the pairing stays random, the load does not. On the 15-agent roster every
proposal gets exactly two reviews, and `validate_plan` refuses a plan where any gets none. The
peer list is sorted before the shuffle, so the order the proposals were read off disk cannot
leak into the result and the recorded seed genuinely reproduces the run.

**A category of one.** The PC-researcher is its own category (Exhibit 9 lists it as
"E: PC-Researcher"), so it has no intra-category peer and no shuffle will find one. Rather than
drop its second review, it writes a second inter-category review, and the substitution is
recorded in the plan's `fallbacks` and printed in the report — it changes what the protocol
delivered, so it belongs in the audit trail rather than in a silent branch. The same rule covers
any family with one member in a given run.

The seed defaults to the first 32 bits of the SHA-256 of the run id, so a reader holding the run
id can re-derive who reviewed whom without being handed a separate number. `--seed` overrides it.

### 36. Schema 3.0.0: the CRO report gained a judgment half — settled, 2026-10-16
`CroReportBody` was written in Phase 1 as a flat model with `commentary` on it and the whole body
registered as the judgment schema, which would have had the model filling in its own volatility
and drawdown. Splitting it the way `cma` is split — script metrics on the body, a nested
`CroJudgment` for the LLM — removes and renames fields, so the global `SCHEMA_VERSION` goes to
3.0.0 by the project's own rule. Nothing had ever written a `cro_report`, so nothing broke in
practice; the bump records that a reader of the old shape would have.

### 37. The IPS's ex-ante limits bind on every candidate; drawdown does not — settled, 2026-10-18
Twelve of the fifteen methods could not reach the IPS volatility floor on their own, which made
them unreviewable: a 0.65%-volatility portfolio is not a candidate a peer reviewer or the CIO
can weigh against the mandate. §3.1 makes the IPS the governing document every agent reads, so
each method is now solved **subject to** the limits rather than left outside them, in
`enforce_ex_ante_limits`.

Which limits, and why only those:

- **Imposed: the volatility band and the tracking-error budget.** Both are computed from the
  covariance matrix the method already consumed, so imposing them adds no information the
  method did not have. 15 of 15 now satisfy every ex-ante rule.
- **Not imposed: the drawdown limit.** Constraining a *realised* drawdown picks weights to suit
  the 1993-2026 path, which is the look-ahead bias §5.1 warns about. Measured: it does reach 15
  of 15, but seven candidates then sit exactly on the −23% constraint and the methods move a
  mean 5.07% tracking error from themselves. The CRO measures drawdown and it binds on the
  CIO's recommendation (decision 32), which is one in-sample fit instead of fifteen. Verified:
  a meta-optimisation over the fifteen reaches 8.00% volatility, −22.6% drawdown, 5.17% real
  return, Sharpe 0.50 and 3.48% tracking error — fully compliant.
- **Not imposed: the return objective.** It is reported; see decision 39.

The method keeps its own objective — maximum Sharpe is still the best risk-adjusted portfolio,
risk parity still the flattest risk contributions, each now over the portfolios policy permits.
A closed-form rule (inverse volatility) and an algorithm (HRP) have no objective to re-run, so
those are projected to the nearest permitted portfolio by weight distance.

**Cost, measured, and smaller than decision 32 assumed.** Mean pairwise tracking error across
the fifteen candidates moves 4.65% → 4.50%, so the vote still has genuinely different
portfolios to weigh (closest pair 0.35%, widest 9.20%). Risk parity keeps risk contributions
spread 3.21-7.10% around the 5.56% equal level on 16 of 18 assets, against a flat 5.56%
unconstrained. The adversarial diversifier remains the furthest from the centroid (6.56%) at
the top of the band. Shrinking the universe instead was tested and is worse: dropping cash
leaves the risk-based methods at 2.24-5.66%, and dropping cash, short *and* intermediate
Treasuries still only gets 5 of 7 into the band. This narrows decision 32 rather than reversing
it: candidates now comply on the ex-ante rules, and compliance remains non-negotiable only for
the CIO.

Every adjusted proposal carries `policy_adjusted` and `unconstrained_volatility_pct`, so a
reviewer can tell the method under policy from the method unconstrained. Schema 3.1.0.

Two consequences had to be fixed with it. §3.4's Sharpe floor of "75% of the maximum Sharpe
portfolio" is now measured against the best Sharpe the *IPS permits*, not the unconstrained
maximum: the unconstrained tangency portfolio here is 90% short Treasuries at a Sharpe of 0.663,
75% of which is 0.498 — above the 0.505 best attainable anywhere in the band, so the floor
admitted one portfolio and the adversarial diversifier and the maximum-entropy researcher both
collapsed onto it. And the PC-researcher now substitutes when its choice duplicates a registry
portfolio (decision 40).

### 38. One number for cash, and expected inflation as the deflator — settled, 2026-10-18
Two inputs were internally inconsistent, and both decided compliance.

**The risk-free rate is now cash's own CMA, not the spot T-bill yield.** Cash *is* the risk-free
asset in this universe, and every Sharpe ratio in the pipeline is over the 3-year CMA horizon,
so a spot 3-month yield was the wrong number — and being a *different* number from cash's own
forecast (3.97% against 3.73%) it gave cash a Sharpe of −0.38. Every return-optimised method
therefore treated cash as strictly dominated while every risk-based method piled into it.
`risk_free_series` remains the fallback for a universe with no cash asset.

**The return test is deflated by expected inflation, not trailing realised CPI.** The CMAs are
nominal forecasts over the CMA horizon, so the deflator has to be expected inflation over that
horizon — which is what the field in `PortfolioMetrics` was already called. On 2026-10-06 the
T5YIE breakeven was 2.41% against 3.71% trailing CPI, a 1.3pp error in the one test the
objective states. `expected_inflation_series: T5YIE` in `config/ips.yaml` names the series;
`inflation_series` stays as the index the objective is *stated* against. Trailing CPI is the
fallback and only the fallback, which a backtest before TIPS breakevens begin in 2003 needs.

### 39. The return objective's floor is hard, its ceiling soft — superseded by 41, 2026-10-18
Faculty answered "treat them as hard constraints" about IPS adherence in general (2026-09-25).
`config/ips.yaml` already flagged the two-sided consequence as "worth confirming": a portfolio
forecast to earn *more* than CPI + 4% was disqualified as surely as one forecast to earn less.
Measuring it settled why that cannot stand. With the deflator corrected (decision 38), 13 of the
15 candidates forecast more than CPI + 4%, so a hard ceiling disqualifies almost the whole
roster for being too profitable; and on the efficient frontier no portfolio inside the 8-12%
volatility band clears both the ceiling and the band at once.

The ceiling is not *infeasible* in the band, and the margins are small, which is why this is a
policy question and not a modelling error. At 8% volatility the attainable real return runs
2.08% to 5.36%, so CPI + 3-4% sits inside it -- but only off the efficient frontier, and the two
candidates that do clear the ceiling (HRP 3.92%, inverse variance 4.00%) clear it by giving up
return at the same risk. The other 13 overshoot by 0.20 to 1.87 percentage points. The target
band is 1pp wide, narrower than the 1.30pp the deflator choice alone moves every candidate, and
far narrower than the estimation error in a 3-year CMA. A two-sided hard target that tight
rewards inefficiency.

So `severity` now governs the floor only and `max_severity` the ceiling, set to `soft`. Both
sides are still reported — a board memo should say when a portfolio is forecast to overshoot its
mandate — but only the floor disqualifies. Falling short of a return objective is a breach of
policy; exceeding it is not. **Provisional: faculty have not ruled on the two-sided reading.**
Setting `max_severity: hard` restores the old behaviour in one line, and nothing else changes.

### 40. The PC-researcher substitutes a method that duplicates the registry — settled, 2026-10-18
§3.4 asks the researcher for "a novel method not spanned by the current registry", and a
portfolio indistinguishable from a registry one is spanned however novel the objective sounds.
Once the IPS band binds (decision 37) that stopped being hypothetical: maximum entropy — the
paper's own March 2026 proposal and our default — reduces to equal weight whenever equal weight
already clears the Sharpe floor, which it does here. The researcher now measures tracking error
against every registry candidate, and at 0.25% or less moves down its library and records that
it did, in the proposal's notes and the research body.

The threshold is 0.25% rather than 0.10% because global minimum variance lands 0.11% from
hierarchical risk parity once both are pushed to the volatility floor — a distance no reviewer
could argue about. That left the library too thin, since both its methods are
minimum-variance-flavoured and converge at the floor, so **mean-downside risk** (maximum
Sortino) was added from the paper's own Exhibit 5 list. It is the one library objective that
trades return against downside risk: the registry's CVaR minimisation and tail-risk parity both
measure downside risk without trading it off against return, and it does not collapse toward
the minimum-variance corner. Decision 33 left it out of the registry as overlapping; as a
researcher-library method it is the one that keeps the researcher's slot distinct.

### 41. The return objective is a floor only — settled, 2026-10-19
Decision 39 made the CPI + 4% ceiling soft. The project owner removed it instead (2026-10-19):
the objective is now "at least CPI + 3%", with no upper limit, reported or binding. A soft
ceiling would still put a violation on 13 of 15 candidates' reports and in the board memo, for
forecasting more return than the objective at the same risk -- noise a reviewer has to read
past, about the one outcome no investor objects to. The paper states CPI + 3-4%; its band is
narrower than the 1.3pp the deflator choice alone moves every candidate (decision 38), and far
narrower than the estimation error in a 3-year CMA. Falling short of the floor is still a hard
breach. `ReturnObjective` forbids extra fields, so a stale `max_pct` in a policy file fails to
load rather than being silently ignored. Deviates from the paper's wording; flagged for faculty.

Decision 37 also stands as the project owner's ruling: the ex-ante limits bind on every
candidate, which is the reading of faculty's "treat them as hard constraints" (2026-09-25) that
holds every portfolio the pipeline produces to the policy, not only the final one.

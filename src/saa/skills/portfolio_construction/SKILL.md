# Portfolio Construction Skill

Used by: the PC agents (stage 4). Paper reference: Ang, Azimbayev & Kim (2026) §3.4 and
Exhibit 5, which groups the methods into four families.

Deterministic: the optimisers run with no LLM. The agents then argue for what the optimiser
produced; they never choose or revise weights.

```bash
uv run saa-agent pc --run-id <run> --no-llm     # the whole roster, weights and statistics only
uv run saa-agent pc --run-id <run>              # with each agent's rationale
uv run saa-agent pc --run-id <run> --methods equal_weight max_sharpe
```

## The roster: 11 agents

All four of Exhibit 5's families, plus the PC-researcher and the adversarial diversifier — the
plan's "2-3 per category plus the adversarial diversifier and PC-researcher agent".

| Family | Agent | Uses CMAs | Reads scenarios | Reference |
|---|---|---|---|---|
| heuristic | `equal_weight` | no | no | DeMiguel, Garlappi and Uppal (2009) |
| heuristic | `inverse_volatility` | no | no | Kirby and Ostdiek (2012) |
| heuristic | `inverse_variance` | no | no | Kirby and Ostdiek (2012) |
| return-optimized | `max_sharpe` | yes | no | Markowitz (1952) |
| return-optimized | `black_litterman` | yes | no | Black and Litterman (1992) |
| risk-structured | `risk_parity` | no | no | Maillard, Roncalli and Teïletche (2010) |
| risk-structured | `hierarchical_risk_parity` | no | no | López de Prado (2016) |
| non-traditional | `cvar_minimization` | no | yes | Rockafellar and Uryasev (2000) |
| non-traditional | `tail_risk_parity` | no | yes | Spinu (2013) |
| PC-researcher | `pc_researcher` | depends on the method it proposes | | §3.4 |
| non-traditional | `adversarial_diversifier` | yes | no | §3.4 |

They run in the paper's order: the nine registry methods in parallel, then the researcher (it
reads what the registry produced), then the adversarial diversifier, which "executes after the
initial 19 have finished" because it moves away from all of them. "Scenarios" are the monthly
returns of the 18 assets over every month they share (from 1993-06), through `as_of`.

### PC-researcher

§3.4: it "proposes a novel method not spanned by the current registry". A proposal the
pipeline cannot run cannot be peer-reviewed, so the choice is constrained — by the judgment
schema, not the prompt — to `RESEARCH_LIBRARY`, methods implemented in advance and absent from
the registry: `maximum_entropy` (Bera and Park 2008, the paper's own March 2026 proposal, under
a Sharpe floor of 75% of the maximum), `maximum_diversification` (Choueifaty and Coignard 2008,
first in the paper's peer vote) and `global_minimum_variance` (Clarke, de Silva and Thorley
2006). The judgment is which gap the registry has this run, read from what the registry's
portfolios actually look like. It writes `pc/pc_research.json` and files its portfolio as
`pc/pc_researcher/pc_proposal.json`. Without a model it proposes maximum entropy.

### Adversarial diversifier

§3.4: maximises tracking variance to the centroid of every other proposal (the researcher's
included) subject to a Sharpe-ratio floor of 75% of the maximum-Sharpe portfolio. "It is not
intended as a standalone recommendation", and its prompt says so. Maximising a convex function
over the simplex puts the optimum at or near a vertex and SLSQP finds local optima, so it starts
from every single-asset portfolio as well as maximum Sharpe and keeps the feasible start that
moves furthest. Its proposal notes record the tracking error to the centroid.

§3.4 explains why both families exist: heuristic methods "avoid optimization-driven estimation
error and dominate when expected returns are poorly measured", while return-optimized methods
"explicitly use return forecasts from the asset class agents". The split is the point — the
peer review in §3.5 is an argument between them, and §4.3 found the agents preferred
covariance-driven methods in a late-cycle regime.

## Constraints

Every method returns **long-only, fully invested** weights, because the ratified IPS permits no
shorting and no leverage. The IPS sets **no per-asset or per-group caps**, so a method may
concentrate; that is deliberate (`docs/ips.md`) and the volatility, drawdown and tracking-error
limits are what binds.

## Implementation notes

- **`max_sharpe`** is not convex in the weights, so SLSQP runs from two starts — equal weight
  and inverse volatility — and the better solution wins. A single start can stop at a local
  optimum when the covariance matrix is close to singular.
- **`black_litterman`** reverse-optimises the market portfolio into equilibrium returns
  (π = δΣw, with ETF market values as the proxy for asset-class size), then blends them with
  the judged CMAs as absolute views. P is the identity, so the posterior is closed-form, and
  Ω = diag(τΣ) holds a view on a volatile asset less tightly than one on a stable asset —
  Black and Litterman's own proportional specification. The posterior then goes through the
  same long-only mean-variance step as `max_sharpe`. Without views it collapses to the market
  portfolio, which is why it belongs in the return-optimized family.
- **`inverse_volatility`** uses only the diagonal of the covariance matrix, so correlation
  estimation error does not reach it. `inverse_variance` tilts harder toward low-volatility
  assets, and is the minimum-variance solution when correlations are assumed equal.
- **`risk_parity`** solves Spinu's (2013) convex problem, min ½y'Σy − (1/n)Σ log y, whose
  first-order condition is exactly equal risk contributions; the non-convex least-squares form
  stalls when risks differ by orders of magnitude, as cash and equities do here.
- **`hierarchical_risk_parity`** orders the assets by a single-linkage dendrogram on the
  correlation distance √((1−ρ)/2), then bisects recursively, splitting each budget in inverse
  proportion to the two halves' inverse-variance variances. No matrix is inverted. On a
  diagonal covariance it reproduces inverse variance exactly (tested).
- **`cvar_minimization`** is Rockafellar and Uryasev's linear programme for the 95% monthly
  expected shortfall, solved with HiGHS over the scenarios — fat tails and asymmetry count.
- **`tail_risk_parity`** is equal risk contribution on the downside semicovariance (shortfalls
  below each asset's mean; Estrada 2008), using the same convex solver. An expected-shortfall
  budget was rejected: a hedge with a negative tail contribution (Treasuries in an equity
  sell-off) cannot be given an equal positive share, so no long-only solution need exist.

## Units

The module works in **decimals**: `covariance.json` stores the matrix in decimal-squared
(0.04 is a 20% volatility), which is the form the standard formulas assume, so
π = δΣw needs no scaling factor. `analysis.py` converts once at the boundary — expected returns
and the risk-free rate in from percent, every statistic out to percent — so everything the
pipeline writes stays percent, per the project convention.

## Statistics

Per portfolio: expected return, volatility, Sharpe ratio, Meucci (2009) effective number of
assets, ex-ante tracking error against the IPS benchmark, and the Herfindahl concentration.
Compliance comes from `saa.ips.check_compliance` — the same function the CRO and CIO call, so a
proposal and its later risk report cannot disagree about what the policy says.

## What a free run shows (as of 2026-10-01)

A `--no-llm` run on the real lake, with each asset's auto-blend standing in for its judged CMA
(the judge was not run, to save spend): only equal weight passes the IPS. Every risk-based
method concentrates in cash, the 0.6%-volatility asset — risk parity 62%, hierarchical risk
parity 92%, CVaR minimisation 97%, tail-risk parity 53% — at 0.6-2.5% volatility, far below the
8% floor. Maximum entropy misses it narrowly (7.5%); the adversarial diversifier overshoots the
12% cap (13.2%). This is the volatility-floor question in `docs/status.md`, now with the full
roster behind it.

## Outputs

`pc/<agent_id>/pc_proposal.json` per agent, `pc/pc_research.json` from the researcher, and
`reports/pc_proposals.md` for the run.

# Portfolio Construction Skill

Used by: the PC agents (stage 4). Paper reference: Ang, Azimbayev & Kim (2026) §3.4 and
Exhibit 5, which groups the methods into four families.

Deterministic: the optimisers run with no LLM. The agents then argue for what the optimiser
produced; they never choose or revise weights.

```bash
uv run saa-agent pc --no-llm                    # every method, weights and statistics only
uv run saa-agent pc                             # with each agent's rationale
uv run saa-agent pc --methods equal_weight max_sharpe
```

## Methods implemented

Phase 2 covers two of Exhibit 5's four families. Risk-structured and non-traditional, plus the
researcher and the adversarial diversifier, are Phase 3.

| Family | Method | Uses CMAs | Reference |
|---|---|---|---|
| heuristic | `equal_weight` | no | DeMiguel, Garlappi and Uppal (2009) |
| heuristic | `inverse_volatility` | no | Kirby and Ostdiek (2012) |
| heuristic | `inverse_variance` | no | Kirby and Ostdiek (2012) |
| return-optimized | `max_sharpe` | yes | Markowitz (1952) |
| return-optimized | `black_litterman` | yes | Black and Litterman (1992) |

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

## Outputs

`pc/<agent_id>/pc_proposal.json` per method and `reports/pc_proposals.md` for the run.

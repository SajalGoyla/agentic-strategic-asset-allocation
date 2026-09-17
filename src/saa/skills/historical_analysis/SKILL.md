# Historical Analysis Skill

Shared by: asset-class agents, covariance agent, CMA judge, CRO agent, PC agents.
Paper reference: Ang, Azimbayev & Kim (2026), Exhibit 3 step 2 ("returns, vol, drawdowns,
correlations") and the CMA judge input `historical_stats.json` (Exhibit 4).

## What it does

Computes return, risk, drawdown and correlation statistics for each of the 18 IPS asset classes
from monthly total returns, using only data that was available on the `as_of` date. It is
deterministic and never calls an LLM. Agents interpret its outputs; they must not recompute them.

## How to run

```bash
uv run saa-skill historical-analysis                     # as of today
uv run saa-skill historical-analysis --as-of 2020-03-31  # point-in-time, e.g. for a backtest
```

```python
from saa.skills.historical_analysis import run_historical_analysis, write_outputs

analysis = run_historical_analysis(as_of="2026-09-15")
write_outputs(analysis, "data/skills/historical_analysis/2026-09-15")
```

## Inputs

| Input | Source |
|---|---|
| Monthly total returns per asset | `DataStore.asset_returns()`: the ETF, spliced with pre-ETF proxies (`market/asset_returns_monthly`) |
| Source of each month | `DataStore.asset_returns(field="source" / "kind")` |
| Risk-free rate | FRED `DTB3` 3-month T-bill; monthly rate = previous month-end yield / 12 |
| Recent daily volatility | ETF daily adjusted closes (`market/prices_daily`) |
| Regime labels (optional) | Month-end series of regime names, e.g. the macro agent's historical scoring |

## Point-in-time rule

A month's return is used only once it was available (`available_from`): the day after month end
for ETF, fund and CRSP data, about 60 days after for Ken French data. With `as_of` equal to a
month end, that month's return is therefore excluded. Pass the rebalance date (e.g. the first
business day of the next month) to include it.

## Windows

| Window | Definition | Sufficient when |
|---|---|---|
| `1y`, `3y`, `5y`, `10y` | Last 12 / 36 / 60 / 120 monthly returns ending at the asset's last available month | All months present |
| `since_1990` | From Jan 1990 (the paper's history start), or the asset's first month if later | At least 36 months |
| `full` | All history (from 1980 at the earliest) | At least 36 months |

When a window is insufficient, `sufficient` is false and every metric is null.

## Metric definitions (decimals; 0.05 = 5%)

| Field | Definition |
|---|---|
| `annualized_return` | Geometric: (product of 1 + r)^(12 / months) - 1 |
| `annualized_volatility` | Sample standard deviation of monthly returns x sqrt(12) |
| `sharpe_ratio` | Mean monthly excess return x 12 / (std of excess returns x sqrt(12)) |
| `sortino_ratio` | Mean excess return x 12 / (sqrt(mean(min(excess, 0)^2)) x sqrt(12)) |
| `max_drawdown` | Worst decline of wealth from its running peak (wealth starts at 1); negative |
| `max_drawdown_peak / trough / recovery` | Month-ends of that drawdown; null peak = window start, null recovery = not recovered |
| `max_drawdown_duration_months` | Months from peak to recovery (or to window end) |
| `current_drawdown` | Decline from the running peak at the window's last month |
| `var_95_monthly` | Historical 5% quantile of monthly returns, as a positive loss |
| `cvar_95_monthly` | Mean of monthly returns at or below that quantile, as a positive loss |
| `skewness`, `excess_kurtosis` | Sample skewness and excess kurtosis of monthly returns |
| `best_month`, `worst_month` | Largest and smallest monthly return, with dates |
| `hit_rate` | Share of months with a positive return |
| `beta_to_us_large_cap` | Cov(asset, US Large Cap) / Var(US Large Cap) over the window |
| `correlation_to_us_large_cap`, `correlation_to_intermediate_treasuries` | Equity and bond anchors |
| `proxy_share` | Share of the window's months that come from proxies rather than the ETF |
| `recent_daily_volatility` | ETF daily returns, last 63 / 252 trading days, x sqrt(252) |

Correlations (`correlation_row.json`) use monthly returns over the `3y`, `5y`, `10y` and
`since_1990` windows ending at the last month every asset has data, pairwise over months both
assets have. `stock_bond_correlation` is the rolling 36-month correlation between US Large Cap and
Intermediate Treasuries: latest, a year ago, and its 10-year range.

Regime statistics (only with labels): per regime, months, arithmetic annualised mean return,
volatility, Sharpe and hit rate. This is the input to the regime-adjusted ERP CMA method.

## Outputs

```
runs/<pipeline_run_id>/cma/<asset_id>/historical_stats.json
runs/<pipeline_run_id>/cma/<asset_id>/correlation_row.json
runs/<pipeline_run_id>/cma/<asset_id>/analysis.md        per-asset narrative
runs/<pipeline_run_id>/reports/historical_analysis.md    table across the 18 assets
```

The models are the shared contracts `historical_stats` and `correlation_row` in
`saa.contracts.asset_class`; this skill does not define its own. `saa.run.RunContext` writes
them, filling the header with the run id, `as_of`, the IPS version and `provenance` (the dataset
versions read). Returns and risk figures are decimals (0.05 = 5%); see `docs/contracts.md`.

`stock_bond_correlation` is returned by `run_historical_analysis()` for the covariance agent but
is not a contract file; it appears in the run-level markdown summary.

## How agents should use it

- **Asset-class agent / CMA judge:** use `since_1990` or `10y` for long-run premia, `3y` for recent behaviour. Check `proxy_share`: a high share means the statistic leans on proxy data (see `docs/asset_data_map.md` for each proxy's tracking error). Quote `max_drawdown` with its dates.
- **Covariance agent:** start from the `5y` or `10y` correlations; compare against `3y` to flag regime shifts. `stock_bond_correlation` shows whether the equity-bond hedge currently works.
- **CRO agent:** `var_95_monthly`, `cvar_95_monthly` and drawdowns are single-asset inputs; portfolio risk needs the covariance agent.
- **PC agents:** `recent_daily_volatility` suits volatility targeting and inverse-volatility; monthly figures suit longer horizons.

## Caveats

- **Pre-ETF months are proxies.** The gold series before 2000 and commodities before 2006 track their ETFs loosely (11-14% and 7% tracking error). International Corporates before 2010 reuse the International Sovereigns proxy, so their correlation there is 1 by construction.
- **Monthly data understates short-horizon tail risk.** Use daily data for intra-month risk.
- **Historical statistics describe the past, not expected returns.** CMAs combine them with valuation, regime and survey information.
- **Without WRDS credentials,** five assets use public proxies, so their pre-ETF statistics differ slightly (see `provenance`).
- **Cash Sharpe and Sortino ratios are not meaningful.** BIL earns slightly less than the T-bill yield (fees, bill maturity mix) with near-zero volatility, so tiny return gaps produce large negative ratios. Use cash return and yield instead.

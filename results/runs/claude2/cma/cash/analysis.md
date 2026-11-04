# Cash (BIL) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 3.7% | 0.1% | -0.85 | 0.0% | 0.0% | 0% |
| 3y | 36 | 4.5% | 0.2% | -0.27 | 0.0% | 0.0% | 0% |
| 5y | 60 | 3.7% | 0.5% | -1.28 | -0.1% | 0.0% | 0% |
| 10y | 120 | 2.3% | 0.6% | -1.41 | -0.2% | 0.0% | 0% |
| since_1990 | 441 | 2.7% | 0.7% | -0.75 | -0.4% | 0.0% | 47% |
| full | 561 | 4.0% | 1.0% | -0.75 | -0.4% | 0.0% | 59% |

## Return history sources

- `crsp:mcti[t30ret]` (index): 1980-01-31 to 2007-05-31, 329 months
- `BIL` (etf): 2007-06-30 to 2026-09-30, 232 months

Recent ETF daily volatility: 3-month 0.2%, 1-year 0.2%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

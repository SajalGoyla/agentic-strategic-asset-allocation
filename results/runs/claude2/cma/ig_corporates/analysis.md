# Investment-Grade Corporates (LQD) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | -4.0% | 5.1% | -1.50 | -6.0% | -6.0% | 0% |
| 3y | 36 | 4.6% | 7.8% | 0.06 | -6.0% | -6.0% | 0% |
| 5y | 60 | -1.3% | 9.8% | -0.47 | -21.9% | -6.7% | 0% |
| 10y | 120 | 1.7% | 8.3% | -0.05 | -23.3% | -8.3% | 0% |
| since_1990 | 441 | 5.3% | 6.9% | 0.39 | -23.3% | -8.3% | 34% |
| full | 561 | 6.5% | 7.4% | 0.34 | -23.3% | -8.3% | 48% |

## Return history sources

- `crsp_fund:ACCBX` (active_fund): 1980-01-31 to 2002-07-31, 271 months
- `LQD` (etf): 2002-08-31 to 2026-09-30, 290 months

Recent ETF daily volatility: 3-month 6.0%, 1-year 5.5%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

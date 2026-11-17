# USD Emerging Market Debt (EMB) - historical analysis

As of 2026-10-01; monthly returns from 1993-06-30 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 0.4% | 6.8% | -0.44 | -4.6% | -4.6% | 0% |
| 3y | 36 | 8.8% | 7.4% | 0.59 | -4.6% | -4.6% | 0% |
| 5y | 60 | 1.2% | 10.4% | -0.20 | -25.1% | -4.6% | 0% |
| 10y | 120 | 2.3% | 10.1% | 0.04 | -26.7% | -4.6% | 0% |
| since_1990 | 400 | 8.0% | 14.0% | 0.45 | -39.6% | -4.6% | 44% |
| full | 400 | 8.0% | 14.0% | 0.45 | -39.6% | -4.6% | 44% |

## Return history sources

- `FNMIX` (active_fund): 1993-06-30 to 2007-12-31, 175 months
- `EMB` (etf): 2008-01-31 to 2026-09-30, 225 months

Recent ETF daily volatility: 3-month 5.7%, 1-year 5.9%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

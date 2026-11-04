# US Large Cap (SPY) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 15.7% | 13.2% | 0.89 | -5.8% | -0.3% | 0% |
| 3y | 36 | 22.8% | 12.4% | 1.37 | -7.6% | -0.3% | 0% |
| 5y | 60 | 13.7% | 15.7% | 0.67 | -23.9% | -0.3% | 0% |
| 10y | 120 | 15.2% | 15.3% | 0.85 | -23.9% | -0.3% | 0% |
| since_1990 | 441 | 10.8% | 14.7% | 0.59 | -50.8% | -0.3% | 8% |
| full | 561 | 11.4% | 15.2% | 0.53 | -50.8% | -0.3% | 28% |

## Return history sources

- `french:F-F_Research_Data_Factors[Mkt-RF + RF]` (academic_index): 1980-01-31 to 1980-01-31, 1 months
- `VFINX` (index_fund): 1980-02-29 to 1993-01-31, 156 months
- `SPY` (etf): 1993-02-28 to 2026-09-30, 404 months

Recent ETF daily volatility: 3-month 11.1%, 1-year 13.0%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

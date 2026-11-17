# International Sovereign Bonds (BWX) - historical analysis

As of 2026-10-01; monthly returns from 1986-10-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | -5.7% | 6.4% | -1.47 | -6.7% | -6.7% | 0% |
| 3y | 36 | 2.0% | 9.3% | -0.21 | -7.9% | -7.2% | 0% |
| 5y | 60 | -4.2% | 10.8% | -0.70 | -26.7% | -19.4% | 0% |
| 10y | 120 | -1.7% | 9.0% | -0.42 | -32.2% | -25.4% | 0% |
| since_1990 | 441 | 3.7% | 8.6% | 0.15 | -32.2% | -25.4% | 49% |
| full | 480 | 4.0% | 8.8% | 0.14 | -32.2% | -25.4% | 53% |

## Return history sources

- `RPIBX` (active_fund): 1986-10-31 to 2007-10-31, 253 months
- `BWX` (etf): 2007-11-30 to 2026-09-30, 227 months

Recent ETF daily volatility: 3-month 7.3%, 1-year 7.5%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

# Gold (GLD) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 7.1% | 27.1% | 0.24 | -23.8% | -21.3% | 0% |
| 3y | 36 | 30.5% | 19.0% | 1.28 | -23.8% | -21.3% | 0% |
| 5y | 60 | 18.3% | 17.2% | 0.86 | -23.8% | -21.3% | 0% |
| 10y | 120 | 11.7% | 15.5% | 0.64 | -23.8% | -21.3% | 0% |
| since_1990 | 441 | 6.2% | 18.1% | 0.27 | -43.6% | -21.3% | 41% |
| full | 561 | 4.7% | 20.5% | 0.13 | -60.8% | -21.3% | 53% |

## Return history sources

- `worldbank:Gold` (monthly_average_price): 1980-01-31 to 1986-04-30, 76 months
- `crsp:CEF(69251)` (bullion_fund): 1986-05-31 to 2000-08-31, 172 months
- `GC=F` (futures): 2000-09-30 to 2004-11-30, 51 months
- `GLD` (etf): 2004-12-31 to 2026-09-30, 262 months

Recent ETF daily volatility: 3-month 24.6%, 1-year 29.6%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

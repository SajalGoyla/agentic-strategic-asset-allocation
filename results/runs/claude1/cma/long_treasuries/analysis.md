# Long-Term Treasuries (TLT) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | -9.0% | 10.1% | -1.24 | -12.1% | -12.1% | 0% |
| 3y | 36 | -0.1% | 13.5% | -0.27 | -13.4% | -13.4% | 0% |
| 5y | 60 | -8.5% | 14.6% | -0.79 | -42.0% | -38.9% | 0% |
| 10y | 120 | -2.8% | 13.6% | -0.32 | -47.6% | -44.8% | 0% |
| since_1990 | 441 | 5.1% | 12.1% | 0.24 | -47.6% | -44.8% | 34% |
| full | 561 | 6.6% | 12.6% | 0.25 | -47.6% | -44.8% | 48% |

## Return history sources

- `crsp:mcti[b20ret/b30ret]` (index): 1980-01-31 to 2002-07-31, 271 months
- `TLT` (etf): 2002-08-31 to 2026-09-30, 290 months

Recent ETF daily volatility: 3-month 9.9%, 1-year 9.4%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

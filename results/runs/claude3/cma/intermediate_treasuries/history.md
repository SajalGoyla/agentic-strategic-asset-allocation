# Intermediate Treasuries (IEF) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | -3.7% | 5.3% | -1.39 | -6.7% | -6.7% | 0% |
| 3y | 36 | 2.9% | 6.7% | -0.20 | -6.7% | -6.7% | 0% |
| 5y | 60 | -2.1% | 7.7% | -0.73 | -19.4% | -10.5% | 0% |
| 10y | 120 | 0.1% | 6.6% | -0.32 | -23.2% | -14.6% | 0% |
| since_1990 | 441 | 5.0% | 6.4% | 0.37 | -23.2% | -14.6% | 34% |
| full | 561 | 6.5% | 7.4% | 0.35 | -23.2% | -14.6% | 48% |

## Return history sources

- `crsp:mcti[b7ret/b10ret]` (index): 1980-01-31 to 2002-07-31, 271 months
- `IEF` (etf): 2002-08-31 to 2026-09-30, 290 months

Recent ETF daily volatility: 3-month 5.2%, 1-year 4.8%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

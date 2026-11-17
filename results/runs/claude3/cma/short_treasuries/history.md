# Short-Term Treasuries (SHY) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 1.5% | 1.1% | -1.98 | -0.5% | -0.5% | 0% |
| 3y | 36 | 3.9% | 1.6% | -0.34 | -0.6% | -0.5% | 0% |
| 5y | 60 | 1.7% | 2.1% | -1.05 | -5.2% | -0.5% | 0% |
| 10y | 120 | 1.6% | 1.6% | -0.51 | -5.4% | -0.5% | 0% |
| since_1990 | 441 | 3.6% | 1.8% | 0.53 | -5.4% | -0.5% | 34% |
| full | 561 | 5.2% | 2.9% | 0.42 | -5.4% | -0.5% | 48% |

## Return history sources

- `crsp:mcti[b2ret]` (index): 1980-01-31 to 2002-07-31, 271 months
- `SHY` (etf): 2002-08-31 to 2026-09-30, 290 months

Recent ETF daily volatility: 3-month 1.5%, 1-year 1.4%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

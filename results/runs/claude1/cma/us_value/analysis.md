# US Value (IWD) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 23.7% | 11.8% | 1.56 | -4.9% | -3.1% | 0% |
| 3y | 36 | 19.9% | 12.4% | 1.18 | -7.9% | -3.1% | 0% |
| 5y | 60 | 11.7% | 15.0% | 0.57 | -17.8% | -3.1% | 0% |
| 10y | 120 | 11.2% | 15.6% | 0.61 | -26.7% | -3.1% | 0% |
| since_1990 | 441 | 10.0% | 14.8% | 0.54 | -55.4% | -3.1% | 28% |
| full | 561 | 12.2% | 14.8% | 0.58 | -55.4% | -3.1% | 44% |

## Return history sources

- `french:6_Portfolios_2x3[BIG HiBM]` (academic_index): 1980-01-31 to 1992-10-31, 154 months
- `VIVAX` (index_fund): 1992-11-30 to 2000-05-31, 91 months
- `IWD` (etf): 2000-06-30 to 2026-09-30, 316 months

Recent ETF daily volatility: 3-month 8.9%, 1-year 11.3%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

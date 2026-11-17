# US Small Cap (IWM) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 16.0% | 16.7% | 0.75 | -7.3% | -7.3% | 0% |
| 3y | 36 | 17.6% | 19.6% | 0.70 | -19.0% | -7.3% | 0% |
| 5y | 60 | 6.2% | 20.9% | 0.21 | -26.8% | -7.3% | 0% |
| 10y | 120 | 9.8% | 20.9% | 0.44 | -32.3% | -7.3% | 0% |
| since_1990 | 441 | 9.6% | 19.4% | 0.43 | -52.5% | -7.3% | 28% |
| full | 561 | 7.4% | 21.1% | 0.25 | -63.3% | -7.3% | 44% |

## Return history sources

- `french:6_Portfolios_2x3[mean(SMALL LoBM, ME1 BM2, SMALL HiBM)]` (academic_index): 1980-01-31 to 1980-01-31, 1 months
- `NAESX` (index_fund): 1980-02-29 to 2000-05-31, 244 months
- `IWM` (etf): 2000-06-30 to 2026-09-30, 316 months

Recent ETF daily volatility: 3-month 13.1%, 1-year 18.6%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

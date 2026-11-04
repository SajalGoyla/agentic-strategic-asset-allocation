# US Growth (IWF) - historical analysis

As of 2026-10-01; monthly returns from 1980-01-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 7.4% | 17.9% | 0.27 | -12.0% | -1.9% | 0% |
| 3y | 36 | 24.1% | 16.3% | 1.15 | -12.0% | -1.9% | 0% |
| 5y | 60 | 13.5% | 19.3% | 0.56 | -30.7% | -1.9% | 0% |
| 10y | 120 | 18.0% | 17.8% | 0.89 | -30.7% | -1.9% | 0% |
| since_1990 | 441 | 11.3% | 16.8% | 0.56 | -61.9% | -1.9% | 28% |
| full | 561 | 12.2% | 17.2% | 0.53 | -61.9% | -1.9% | 44% |

## Return history sources

- `french:6_Portfolios_2x3[BIG LoBM]` (academic_index): 1980-01-31 to 1992-10-31, 154 months
- `VIGRX` (index_fund): 1992-11-30 to 2000-05-31, 91 months
- `IWF` (etf): 2000-06-30 to 2026-09-30, 316 months

Recent ETF daily volatility: 3-month 18.1%, 1-year 17.9%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

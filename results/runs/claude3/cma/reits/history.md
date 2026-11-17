# REITs (VNQ) - historical analysis

As of 2026-10-01; monthly returns from 1986-12-31 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 1.8% | 15.5% | -0.05 | -8.6% | -8.6% | 0% |
| 3y | 36 | 10.0% | 16.6% | 0.40 | -9.1% | -8.6% | 0% |
| 5y | 60 | 1.4% | 19.2% | -0.03 | -32.8% | -8.6% | 0% |
| 10y | 120 | 4.4% | 17.7% | 0.20 | -32.8% | -8.6% | 0% |
| since_1990 | 441 | 9.3% | 18.5% | 0.43 | -68.3% | -8.6% | 40% |
| full | 478 | 8.9% | 18.1% | 0.40 | -68.3% | -8.6% | 45% |

## Return history sources

- `FRESX` (active_fund): 1986-12-31 to 1996-05-31, 114 months
- `VGSIX` (index_fund): 1996-06-30 to 2004-09-30, 100 months
- `VNQ` (etf): 2004-10-31 to 2026-09-30, 264 months

Recent ETF daily volatility: 3-month 12.3%, 1-year 13.6%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

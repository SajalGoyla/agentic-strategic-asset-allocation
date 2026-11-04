# International Developed (EFA) - historical analysis

As of 2026-10-01; monthly returns from 1983-02-28 through 2026-09-30.

| Window | Months | Return p.a. | Volatility | Sharpe | Max drawdown | Current DD | Proxy share |
|---|---|---|---|---|---|---|---|
| 1y | 12 | 15.1% | 12.8% | 0.88 | -7.8% | -3.3% | 0% |
| 3y | 36 | 18.3% | 11.9% | 1.11 | -8.4% | -3.3% | 0% |
| 5y | 60 | 9.3% | 15.6% | 0.41 | -27.5% | -3.3% | 0% |
| 10y | 120 | 9.0% | 15.0% | 0.49 | -27.6% | -3.3% | 0% |
| since_1990 | 441 | 5.9% | 16.0% | 0.27 | -57.4% | -3.3% | 32% |
| full | 524 | 8.9% | 16.0% | 0.40 | -57.4% | -3.3% | 43% |

## Return history sources

- `crsp_fund:RINSX` (active_fund): 1983-02-28 to 2001-08-31, 223 months
- `EFA` (etf): 2001-09-30 to 2026-09-30, 301 months

Recent ETF daily volatility: 3-month 13.0%, 1-year 15.9%.

Pre-ETF months come from proxies; `docs/asset_data_map.md` reports each proxy's tracking error against the ETF.

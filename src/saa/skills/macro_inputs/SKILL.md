# Macro Inputs Skill

Used by: the macro agent (regime scoring), and any agent that needs a macro indicator as it
stood on a past date. Paper reference: Ang, Azimbayev & Kim (2026) §3.2 — the macro-regime skill
holds "the scoring methodology, and the data-fetching script"; this is that data-fetching half.

## What it does

For one FRED series and one date, returns the **transformed value the dimension is scored on**,
the raw value behind it, the observation and availability dates, and whether the number came
from a true ALFRED vintage or from a release-lag estimate. It does **not** score anything:
scores and weights are the macro agent's judgement.

```python
from saa.data import DataStore
from saa.skills.macro_inputs import IndicatorRequest, indicator, indicators, pit_quality

store = DataStore()
payrolls = indicator(store, IndicatorRequest("PAYEMS", "yoy"), as_of="2020-03-31")
payrolls.value  # 0.0146  (transformed: +1.46% year over year)
payrolls.raw_value  # 151786.0 (thousands of jobs, as known on 2020-03-31)
payrolls.point_in_time  # True: an ALFRED vintage, not a release-lag estimate
payrolls.to_score(score=-0.4, weight=0.25)  # -> contracts.macro.IndicatorScore
```

## Transforms (`saa.contracts.macro.Transform`)

| Transform | Meaning | Use for |
|---|---|---|
| `level` | The value as published | Indices already centred on zero (CFNAI, NFCI), rates |
| `yoy` | Proportional change over 12 months | Index levels: payrolls, industrial production, CPI, retail sales |
| `mom_annualised` | One month's change compounded to a year | Spotting turns earlier than year-over-year |
| `diff` | Absolute change over N months (default 12) | Rates, spreads and z-scored indices |
| `zscore` | Standard deviations from the trailing mean | Comparing series with different units |
| `percentile` | Rank within the trailing window, 0 to 1 | Bounded scores, robust to outliers |

Lags are taken **by date**, not by row count, so a quarterly series is compared with the same
quarter a year earlier and a daily series with the nearest earlier observation. `zscore` and
`percentile` use a time-based trailing window (default 20 years), so series of different
frequencies get the same amount of history.

## Point-in-time

Values come from `DataStore.macro_long(as_of=...)`: for series with ALFRED vintages, the vintage
in force on that date; otherwise the published value with an estimated release date. The
`point_in_time` flag records which, and `pit_quality()` aggregates it per dimension for
`MacroScores.pit_quality`.

Only 8 of the 62 ingested series carry vintages, and they start as late as 2011 (CFNAI) and 2016
(GDPNOW). A 1994 regime call therefore rests mostly on revised data — the flag is what lets a
backtest say so rather than overstate its own rigour.

## Notes

- `indicators()` skips a series that lacks enough history at `as_of` (a 20-year z-score early in
  a series' life) rather than failing the whole dimension. Check which ones came back.
- `dimension_requests(config, "growth")` lists every series a dimension declares in
  `config/macro_series.yaml`, excluding `evaluation_only` ones such as the NBER recession flag.
- Series with `evaluation_only: true` are ex-post labels; never score them.
- A transform on a rate (`yoy` on `DGS10`) is meaningless; use `diff` or `level`.

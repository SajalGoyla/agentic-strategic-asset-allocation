# Macro Regime Skill

Scores four macroeconomic dimensions and classifies the result into one of four regimes.
Deterministic: no language model is involved at any point.

Ang, Azimbayev & Kim (2026) §3.2 describe "a macro-regime skill [that] contains the regime
classification framework (four regimes: expansion, late-cycle, recession, recovery, defined by
growth, inflation, monetary policy, and financial conditions scores), the scoring methodology,
and the data-fetching script." The paper does not publish the framework, so everything below is
ours and lives in `config/macro_scoring.yaml`.

## Inputs

FRED series, read through `DataStore.macro(as_of=...)` so a historical run sees only what was
public at the time. 34 series across the four dimensions.

`RECPROUSM156N` — the Chauvet–Piger smoothed recession probability — is deliberately excluded.
It is re-estimated backwards after the fact, which makes it a recession *label* rather than a
signal; scoring it and then evaluating the classifier against NBER dates would be close to
circular. `USREC` is excluded by `DataStore` itself, which blocks `evaluation_only` series from
any `as_of` query.

## Method

**1. Transform.** Each series becomes a comparable quantity: a level, a year-over-year or
annualised monthly change, or a difference over N months.

**2. Score.** The transformed series is z-scored against a trailing window of its own history
(20 years by default, minimum 24 months) and squashed with `tanh(z/2)` onto [-1, +1]. The
rolling statistics use only data up to each point, so the mapping is causal — the score for
March 2008 never sees 2009. `tanh` bounds the contribution of any one extreme print.

**3. Sign.** Each indicator carries `+1` or `-1` so that every dimension reads the same way:
**+1 is the risk-supportive direction.** Growth strong, inflation contained, policy easy,
financial conditions loose. A strongly positive inflation score therefore means inflation is
*low*. Unemployment rising carries `-1`; `NFCI` is constructed so positive means tighter, so it
carries `-1` too.

**4. Combine.** A weighted mean within each dimension, renormalised row by row over whichever
indicators have data. A dimension with fewer than `min_indicators` live series scores null
rather than guessing from one number.

**5. Classify.** Rules are evaluated in order; the first whose conditions all hold wins.
Contraction is defined by the level of growth, and whether that is recession or recovery by
whether growth is still falling or already turning. Late-cycle is positive but deteriorating
growth, or positive growth alongside an inflation or policy squeeze — which is the shape that
produces §4.1's "late-cycle with stagflationary risk".

**6. Confidence.** Falls when dimension scores sit close to the thresholds that decided the
regime, when the four dimensions disagree, when configured indicators have no data, and in the
month a regime first changes.

## The ragged edge

Monthly growth releases lag by weeks, so the newest month-ends usually have too few indicators
to score. Every classification rule tests growth, so a row without a growth score cannot be
classified and would fall through to the default regime — which would be a silent, confident
wrong answer. The scorer trims to the last month growth could actually be scored and reports
that as `data_end`. The gap between `data_end` and `as_of` is real information: a two-month-old
reading is not the same as a calm one.

## Point-in-time

`score_history(point_in_time=False)`, the default, scores the whole history from the latest
vintage of each series. That is correct for a live run and wrong for a backtest: each
historical month is scored with data revised after the fact.

`point_in_time=True` re-queries the lake at every month end so each row sees only what was
public then. Much slower, and what a backtest needs.

Either way the choice is recorded on the output. Note the ceiling: only 8 of the 62 ingested
FRED series carry ALFRED revision history, and their vintages start as late as 2011 (`CFNAI`)
and 2016 (`GDPNOW`). `MacroScores.pit_quality` reports, per dimension, how many contributing
indicators were genuinely point-in-time, so a reader can see how much of a historical call
rests on revised data.

## Outputs

`ScorePanel`, carrying monthly dimension scores, growth momentum, a regime label and a
confidence per month, plus the per-indicator detail. The last row is the current call; the
whole label column is the history that the regime-adjusted CMA method (§3.3 method 2) and
`skills.historical_analysis.conditional_stats` consume.

## Usage

```python
from saa.skills.macro_regime import score_history

panel = score_history(store, scoring_config, as_of="2026-03-31")
panel.latest()  # {"growth": 0.03, "inflation": -0.22, ...}
panel.regimes.iloc[-1]  # "late_cycle"
panel.regimes  # the label history, indexed by month end
```

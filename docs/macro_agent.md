# Macro Regime Agent

Stage 1 of the pipeline. Ang, Azimbayev & Kim (2026) §3.1: "A macro agent classifies the
current economic regime (expansion, late-cycle, recession, or recovery) based on macro and
market indicators, providing a regime signal that conditions all downstream analysis."

Its output is read by all eighteen asset-class agents, by the covariance agent, and by the CIO.
An over-confident call propagates, which is why the confidence score and the point-in-time
quality flags matter as much as the label.

## Shape

The paper's §3.2 anatomy — a description, skills, scripts, an output contract — split so the
deterministic half can run on its own:

| Part | Where |
|---|---|
| Agent description | `src/saa/agents/macro/AGENT.md` |
| Skill methodology | `src/saa/skills/macro_regime/SKILL.md` |
| Scoring (no LLM) | `src/saa/skills/macro_regime/scoring.py` |
| Indicators, weights, rules | `config/macro_scoring.yaml` |
| Agent | `src/saa/agents/macro/agent.py` |
| Contracts | `macro-view.json`, `regime_history.json`, `macro.md` |

`AGENT.md` and `SKILL.md` together form the system prompt, which is what §3.2 means by the
description being "read by the LLM at runtime".

## Running it

```bash
uv run saa-agent macro --no-llm          # deterministic scoring only: no API key, no spend
uv run saa-agent macro                   # full run, writes the contracts
uv run saa-agent macro --as-of 2008-09-30 --point-in-time
uv run saa-agent macro --cap-usd 1.00    # stop rather than overspend
```

`--no-llm` is the quickest way to check the effect of a change to `config/macro_scoring.yaml`,
and it is the mode the backtest below uses.

## What the model does and does not do

The scores are computed before the model sees them. The prompt carries the full indicator
table — every series, its transform, its score, its weight, and whether it was genuinely
point-in-time — and the rule-based regime as a *prior*, explicitly not an instruction. The
model may depart from it, but must name the rule it departed from.

That leaves it the part a weighted average cannot do: spotting that a growth score near zero
hides a labour market rolling over while retail sales hold up, noticing that the newest release
is two months old, and carrying a qualifier the four-way label would lose — which is how §4.1
arrives at "late-cycle with stagflationary risk" rather than plain "late-cycle".

The `MacroJudgment` contract has no field for the dimension scores, so the model cannot restate
them as its own even if it tries.

## Validation against NBER

The deterministic classifier, scored monthly from 1995 to 2026 and compared against `USREC`.
`USREC` is marked `evaluation_only`, so `DataStore` blocks it from any `as_of` query — it can
only ever be an evaluation target, never an input. `RECPROUSM156N` is excluded from scoring for
the same reason: a smoothed recession probability re-estimated after the fact is a label, and
scoring it would make this test close to circular.

Counting `recession` or `recovery` as a downturn call:

| | |
|---|---|
| Months scored | 380 |
| NBER recession months | 28 |
| Recall | **100%** |
| Specificity | 91% |
| Precision | 47% |

All three NBER recessions in the window — 2001, 2007–09 and 2020 — were flagged in full. The
low precision is partly by construction: `recovery` follows the trough by definition, so months
scored as recovery sit outside the official recession and count against precision while being
exactly what the label is meant to mean.

Two caveats worth stating rather than burying:

- **2020 is noisy.** The COVID shock was faster than a classifier built on twenty-year trailing
  z-scores can track, and the regime path oscillates around it. Tuning the thresholds until
  2020 looked clean would be fitting to one observation.
- **`expansion` and `late_cycle` split almost evenly** (161 and 160 months). That is plausible
  for 1995–2026 but the boundary between them is the softest part of the rule set, and it is
  where the LLM layer is most likely to earn its place.

## Revisions: does using final data flatter the classifier?

`--point-in-time` re-queries the lake at every month end so each row sees only what was public
then, rather than scoring the whole history off the latest vintage. Over 2007–2009:

| | |
|---|---|
| Agreement between the two modes | **94%** of 35 months |
| Months that differ | 2008-02, 2009-05 |
| First recession call, point-in-time | 2008-01 |

NBER dates the recession start to December 2007 and did not announce it until December 2008,
so a real-time call in January 2008 is a genuine result rather than hindsight.

The ceiling on that claim: only 8 of the 62 ingested FRED series carry ALFRED revision history,
and their vintages start as late as 2011 for `CFNAI` and 2016 for `GDPNOW`. Everything else
falls back to an estimated release date. `MacroScores.pit_quality` reports per dimension how
many contributing indicators were genuinely point-in-time, so a reader can see how much of any
historical call rests on revised data. Point-in-time scoring costs about 0.2s per month, so a
thirty-year history takes just over a minute.

## Outputs

**`macro-view.json`** — `MacroScores` (the four dimension scores, the indicator detail,
`pit_quality`, `data_end`) plus `MacroJudgment` (regime, qualifier, confidence, recession
probability range, a rationale per dimension, key risks, narrative).

**`regime_history.json`** — the month-by-month label history. `body.labels()` returns the
`{month: regime}` mapping that `skills.historical_analysis.conditional_stats` and §3.3's
regime-adjusted CMA method consume. It comes from the same scorer as the current call, so the
two cannot disagree.

**`macro.md`** — the human-readable half of the contract, per §3.2.

## The ragged edge

Monthly growth releases lag by weeks. Every classification rule tests growth, so a month
without a growth score cannot be classified — it would fall through to the default regime and
look like a real call. Those months are dropped, at both ends: the head needs a warm-up before
the trailing z-scores are defined, the tail is waiting on releases.

`data_end` therefore normally sits a month or two behind `as_of`, and the gap is carried into
the contract and the prompt. A two-month-old reading is not the same as a calm one.

## Known gaps

- **Web search.** §3.2 has the macro agent "search the web for real-time readings of both
  numeric and textual information". Not wired up; the Messages API offers a server-side web
  search tool, which is the natural place to add it.
- **The `expansion` / `late_cycle` boundary** is the softest part of the rule set (see above).
- **Weights are unvalidated.** The indicators, transforms and weights in
  `config/macro_scoring.yaml` are ours; the paper publishes none of them. The NBER test above
  checks the classifier end to end but says nothing about whether any individual weight is
  right.

## Reference

Ang, Andrew, Nazym Azimbayev, and Andrey Kim. 2026. *"The Self-Driving Portfolio: Agentic
Architecture for Institutional Asset Management."* §3.1, §3.2, §3.3, §4.1.

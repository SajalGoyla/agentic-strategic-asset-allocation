# Output Contracts

Ang, Azimbayev & Kim (2026) §3.2 make the output contract one of the four things that define an
agent, alongside its description, its scripts and its skills:

> The output contract specifies the structured files the agent must produce: JSON files
> conforming to defined schemas (for machine consumption by downstream agents) and markdown
> reports (for human review). Every agent produces both quantitative outputs and
> natural-language analysis, ensuring that the pipeline generates audit trails at every step.

`src/saa/contracts/` is that specification. `schemas/` holds the generated JSON Schemas,
committed so a change shows up as a reviewable diff rather than as a downstream agent breaking.

## The registry

`uv run saa-contracts --list`

| Contract | Stage | Produced by | File |
|---|---|---|---|
| `macro_view` | macro | hybrid | `macro-view.json` |
| `historical_stats` | cma | script | `historical_stats.json` |
| `correlation_row` | cma | script | `correlation_row.json` |
| `signals` | cma | script | `signals.json` |
| `cma_methods` | cma | script | `cma_methods.json` |
| `cma` | cma | hybrid | `cma.json` |
| `scenarios` | cma | hybrid | `scenarios.json` |
| `covariance` | pc | script | `covariance.json` |
| `pc_proposal` | pc | hybrid | `pc_proposal.json` |
| `pc_research` | pc | llm | `pc_research.json` |
| `cro_report` | review | hybrid | `cro_report.json` |
| `peer_review` | review | llm | `peer_review.json` |
| `vote` | review | llm | `vote.json` |
| `vote_tally` | review | script | `vote_tally.json` |
| `cio_decision` | cio | hybrid | `cio_decision.json` |

Filenames are the paper's own, from §3.2 and Exhibit 3. Adding a contract means adding one
`Spec` to `registry.py`; schema export, file layout and validation follow from it.

## Three conventions

**The envelope is machine-written, never model-written.** Every file is `AgentOutput` —
a `header` plus a `body`. The harness fills the header: schema version, agent slug, pipeline
run id, `as_of`, dataset provenance from `DataStore.provenance()`, which upstream files were
read, which IPS version governed the run, which model was called and what it cost. The schema
handed to `client.messages.parse(output_format=...)` is the *judgment* model nested inside the
body, so a model cannot fabricate its own provenance or token counts.

**Script output and LLM judgment are separate models.** §3.2: "the LLM handles judgment,
interpretation, and narrative; the scripts handle computation." Where a stage does both, the
body holds a deterministic half and a judgment half:

| Contract | Deterministic | Judgment |
|---|---|---|
| `macro_view` | `MacroScores` — four dimension scores from `DataStore.macro()` | `MacroJudgment` — regime, confidence, recession probability, narrative |
| `cma` | `CmaMethodsBody` — the seven candidates | `CmaJudgment` — selection, method weights, the four Exhibit 4 checks |

§3.3 is explicit that the seven CMA candidates "are written to a `cma_methods.json` file by a
Python script; no LLM judgment is involved up to this point" — so `cma_methods` has no judgment
model at all, and the registry records that.

**Rules the paper states are validated, not just prompted.** Anywhere the paper gives a hard
constraint, it is a `model_validator`:

- The CMA judge's final estimate must lie within `[min_method, max_method]` (Exhibit 4).
- The top-five shortlist must span at least three of the four PC families (§3.5).
- A ballot awards 5/4/3/2/1 and one −2 bottom flag, excluding the voter (§3.5).
- A peer review marked intra-category must actually be intra-category (§3.5).
- The CIO's composite score must match the §4.4 weighted rubric (25/15/15/20/15/10).
- The CIO may not ship an allocation that fails a hard IPS rule — §3.6 calls compliance
  "non-negotiable".
- Portfolio and ensemble weights must be fully invested and non-negative.
- A covariance matrix must be square, symmetric and have positive variances.

## Using them

Writing, from an agent:

```python
from saa.contracts import AgentOutput, Header, MacroViewBody, write

output = AgentOutput[MacroViewBody](header=Header(...), body=MacroViewBody(scores=..., judgment=...))
write(output, run_dir / "macro" / "macro-view.json")
```

Reading, from a downstream agent:

```python
from saa.contracts import read

macro = read("macro_view", run_dir / "macro" / "macro-view.json")
macro.body.judgment.regime          # Regime.LATE_CYCLE
macro.header.provenance             # exactly which lake versions produced it
```

Constraining an LLM:

```python
from saa.contracts import MacroJudgment

response = client.messages.parse(
    model="claude-opus-5",
    max_tokens=16000,
    messages=[...],
    output_format=MacroJudgment,   # validated on the way back
)
```

`json_schema(name, judgment=True)` gives the raw schema if you need `output_config.format`
instead. Judgment schemas carry `additionalProperties: false` and mark every property
`required`, including nullable ones — pydantic leaves fields with defaults out of `required`,
which would let a model silently omit them, so the exporter puts them back. A missing value has
to be an explicit `null`.

## Open: units

`historical_stats` and `correlation_row` use **decimals** (0.05 = 5%), matching
`saa.skills.historical_analysis`, which computes them. Every other contract, and `saa.ips`, uses
**percent** — the paper states its figures that way ("CPI + 3.0–4.0%", "8–12%", "−25%", "6%"),
and the IPS, CRO, CIO and board memo all follow it.

That split is deliberate for now, not accidental: nothing converts silently, and the field
suffix tells you which you have (`max_drawdown` is a decimal, `max_drawdown_pct` is percent).
It still needs settling before the CMA agents land in Week 4, since they read historical stats
and write percent. Standardising on percent means changing one module; standardising on decimals
means changing five.

## Migrating the historical-analysis skill

`saa.skills.historical_analysis.models` still defines its own `WindowStats`,
`AssetHistoricalStats` and `CorrelationRow`, marked "DRAFT ... these move into the shared
output-contract package once the project schemas are agreed". The contract now mirrors them
field for field, and `test_historical_stats_matches_the_skill_that_produces_it` fails if either
side drifts. The remaining step, which belongs in the skill's own PR, is for the skill to emit
`AgentOutput[HistoricalStatsBody]` through `contracts.write()` so its envelope fields become a
`Header`. Two intentional differences to adopt at that point:

- `schema_version`, `as_of` and `provenance` move into `Header`.
- `by_regime` moves from the bundle onto the per-asset file, because §3.3's regime-adjusted CMA
  method is per asset and should not have to open a bundle to find one asset's numbers.

## Run directory layout

```
runs/<pipeline_run_id>/
  macro/macro-view.json
  cma/<asset_id>/{cma_methods,cma,signals,historical_stats,scenarios,correlation_row}.json
  pc/{covariance.json, <agent_id>/pc_proposal.json, pc_research.json}
  review/{<agent_id>/{cro_report,vote}.json, <agent_id>/peer_review-<reviewed>.json,
          vote_tally.json}
  cio/cio_decision.json
  reports/*.md
```

Markdown reports sit alongside and are referenced from `header.report_path`, because §3.2 makes
the narrative half of the contract, not an optional extra.

## Point-in-time quality

`MacroScores.pit_quality` records, per dimension, how many contributing indicators came from a
true ALFRED vintage in force at `as_of` rather than from a release-lag estimate. Only 8 of the
62 ingested FRED series carry revision history, and their vintages start as late as 2011
(`CFNAI`) and 2016 (`GDPNOW`). Carrying the number in the contract is what stops a backtest
quietly overstating its own rigour — a reader can tell whether a 1994 regime call rested on
real-time data or on data revised long afterwards.

## Changing a contract

1. Edit the model.
2. `uv run saa-contracts` to regenerate `schemas/`.
3. `uv run pytest` — `test_committed_schemas_are_current` fails if you skipped step 2.
4. Bump `SCHEMA_VERSION` in `base.py`: minor for additive changes, major for anything that
   breaks a reader.

## Reference

Ang, Andrew, Nazym Azimbayev, and Andrey Kim. 2026. *"The Self-Driving Portfolio: Agentic
Architecture for Institutional Asset Management."* §3.2, §3.3, §3.5, §3.6, §4.4, Exhibits 3, 4,
5, 9, 10, 11.

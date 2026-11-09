# Asset-class report skill

The 13-section investment case for one asset class, assembled from the stage-2 contracts.

Ang, Azimbayev & Kim (2026), Exhibit 3, names this as the asset-class agent's headline
deliverable — *"Produces 13-section investment case and capital market assumptions"* — lists
`asset-class-report` among the agent's required skills, and makes it half of workflow step 8:
*"Scenario analysis (bull/bear from method range) + 13-section report"*. The output is
`analysis.md`.

## The section list is ours

**The paper never publishes the thirteen sections.** It names the report twice and nowhere
enumerates its contents: no exhibit, no appendix, no footnote. So the count is the paper's and
the contents are a reconstruction from Exhibit 3's own workflow, which is the only evidence
available about what the report is for. If the authors' section list ever surfaces, this is the
file to change.

The reconstruction maps each section onto the workflow step that produces it and the contract
that holds the numbers:

| # | Section | Exhibit 3 step | Source |
|---|---|---|---|
| 1 | Recommendation | 7 | `cma.json` |
| 2 | The asset class | — | `universe.yaml`, the asset's description file |
| 3 | Macro view | 1 | `macro-view.json`, `cma.json` judgment |
| 4 | Return and risk history | 2 | `historical_stats.json` |
| 5 | Correlations and portfolio role | 2 | `correlation_row.json` |
| 6 | Valuation and fundamentals | 3 | `signals.json`, `cma.json` judgment |
| 7 | Technical signals | 4 | `signals.json` |
| 8 | Macro sensitivity and regime fit | 1, 3 | `signals.json`, `historical_stats.json` |
| 9 | Capital market assumption: the candidates | 6 | `cma_methods.json` |
| 10 | The judgment | 7 | `cma.json` judgment |
| 11 | Scenarios | 8 | `scenarios.json` |
| 12 | Key risks and what would invalidate the view | — | the description file, `cma.json` notes |
| 13 | Provenance and limitations | — | contract headers |

Step 5 — sentiment and positioning from a runtime web search — has no section, because the
pipeline does not do it (decision 26). Section 13 says so rather than leaving the omission to
be noticed.

## It writes no prose of its own

Every judgement in the report is the CMA judge's, quoted from `cma.json`: `regime_logic`,
`valuation_context`, `signal_alignment`, `rationale` and `notes`. This skill contributes
structure, arithmetic and the sign conventions, which is the division of labour decision 8
requires — skills never call an LLM, and a second narrative layer would be a second opinion
nobody asked for and nobody could audit.

The consequence is worth knowing: **the report is only as good as the judge's narrative
fields.** A thin `rationale` produces a thin section 10, and that is the right failure mode —
visible, and fixed by improving the agent rather than by padding the report.

## It supersedes the historical-analysis stub

`skills/historical_analysis/` also writes `analysis.md`, with return history and sources only.
This skill overwrites it with the full case, which is why it runs last in stage 2. Nothing is
lost: section 4 carries the return and risk history and section 13 carries the sources.

## Usage

```bash
uv run saa-skill asset-class-report --run-id <run>                # all 18
uv run saa-skill asset-class-report --run-id <run> --assets gold
```

Needs `cma_methods.json`, `cma.json`, `signals.json`, `historical_stats.json` and
`correlation_row.json` per asset; `scenarios.json` is used when present and section 11 says so
when it is not. Writes `cma/<asset>/analysis.md` and `reports/asset_class_cases.md`.

## Limitations

- **`by_regime` is often empty.** The historical-analysis skill fills it only when a regime
  history is supplied; without one, section 8 reports the measured dimension alignments and
  says the per-regime table is unavailable rather than inferring one.
- **Section 6 is thin for assets with no valuation signal.** Decision 26 emits an earnings-yield
  signal only for US Large Cap, so most assets reach the judge through `cma_methods.json`
  instead. Section 6 falls back to the candidate components, and says which it used.
- **Gold and commodities have no valuation anchor at all.** Their section 6 reports that
  explicitly; it is a property of the asset, not a gap in the data.

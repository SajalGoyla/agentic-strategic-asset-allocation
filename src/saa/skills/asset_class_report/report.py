"""The 13-section investment case per asset (Exhibit 3), assembled from the stage-2 contracts.

The paper names the report and never lists its sections; SKILL.md records that and maps our
reconstruction onto Exhibit 3's workflow steps. This module writes no prose of its own -- every
judgement in the output is quoted from the CMA judge's narrative fields, because skills never
call an LLM (decision 8).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from saa.config import Config
from saa.contracts.asset_class import (
    CMA_CONTRACT,
    CORRELATION_CONTRACT,
    METHODS_CONTRACT,
    SCENARIOS_CONTRACT,
    SIGNALS_CONTRACT,
    STATS_CONTRACT,
    CmaBody,
    CmaMethodsBody,
    CorrelationRowBody,
    HistoricalStatsBody,
    ScenariosBody,
    SignalsBody,
)
from saa.contracts.registry import read
from saa.run import RunContext

REPORT = "asset_class_cases.md"
ASSET_REPORT = "analysis.md"
N_SECTIONS = 13

# Windows worth tabulating, in the order a reader wants them.
WINDOWS = ("1y", "3y", "5y", "10y", "since_1990")


@dataclass(frozen=True)
class AssetCase:
    asset_id: str
    text: str
    sections: int


@dataclass
class ReportsResult:
    cases: dict[str, AssetCase] = field(default_factory=dict)


# ----------------------------------------------------------------------------------- loading
@dataclass(frozen=True)
class CaseInputs:
    cma: CmaBody
    methods: CmaMethodsBody
    signals: SignalsBody | None
    stats: HistoricalStatsBody | None
    correlations: CorrelationRowBody | None
    scenarios: ScenariosBody | None
    description: str
    macro_line: str


def _optional(run: RunContext, contract: str, asset_id: str):
    path = run.path(contract, asset_id=asset_id)
    return read(contract, path).body if path.exists() else None


def load_case_inputs(run: RunContext, asset_id: str) -> CaseInputs:
    from saa.agents.cma_judge.agent import asset_description

    cma_path = run.path(CMA_CONTRACT, asset_id=asset_id)
    methods_path = run.path(METHODS_CONTRACT, asset_id=asset_id)
    for path in (cma_path, methods_path):
        if not path.exists():
            raise FileNotFoundError(
                f"{asset_id}: the investment case needs {path.name}; run stage 2 first"
            )
    return CaseInputs(
        cma=read(CMA_CONTRACT, cma_path).body,
        methods=read(METHODS_CONTRACT, methods_path).body,
        signals=_optional(run, SIGNALS_CONTRACT, asset_id),
        stats=_optional(run, STATS_CONTRACT, asset_id),
        correlations=_optional(run, CORRELATION_CONTRACT, asset_id),
        scenarios=_optional(run, SCENARIOS_CONTRACT, asset_id),
        description=asset_description(asset_id),
        macro_line=_macro_line(run),
    )


def _macro_line(run: RunContext) -> str:
    from saa.contracts.macro import CONTRACT as MACRO_VIEW_CONTRACT

    path = run.path(MACRO_VIEW_CONTRACT)
    if not path.exists():
        return ""
    body = read(MACRO_VIEW_CONTRACT, path).body
    j = body.judgment
    regime = j.regime.value.replace("_", "-").capitalize()
    # The qualifier often opens by restating the regime ("expansion, stall-speed expansion ...").
    note = (j.regime_qualifier or "").strip()
    if note.lower().startswith(j.regime.value.lower()):
        note = note[len(j.regime.value) :].lstrip(" ,;-")
    qualifier = f" — {note}" if note else ""
    scores = " · ".join(f"{d.dimension} {d.score:+.3f}" for d in body.scores.dimensions)
    return (
        f"**{regime}**{qualifier}. Confidence {j.confidence.value} "
        f"({j.confidence_score:.2f}); recession probability "
        f"{j.recession_probability.low_pct:.0f}–{j.recession_probability.high_pct:.0f}%. "
        f"Dimension scores: {scores}."
    )


def key_considerations(description: str) -> list[str]:
    """The numbered bullets under `## Key considerations` in the asset's description file."""
    match = re.search(r"## Key considerations\n(.*?)(?=\n## |\Z)", description, re.S)
    if not match:
        return []
    block = match.group(1)
    items = re.findall(r"^\d+\.\s+(.*?)(?=\n\d+\.\s|\Z)", block, re.S | re.M)
    return [" ".join(i.split()) for i in items]


def _field(description: str, label: str) -> str:
    match = re.search(rf"\*\*{label}:\*\*\s*(.*)", description)
    return match.group(1).strip() if match else ""


# --------------------------------------------------------------------------------- rendering
def _fmt(value: float | None, places: int = 2, suffix: str = "") -> str:
    return "n/a" if value is None else f"{value:.{places}f}{suffix}"


def _windows_table(stats: HistoricalStatsBody | None) -> str:
    if stats is None:
        return "_`historical_stats.json` is not in this run, so there is no return history._"
    rows = [
        "| Window | Return | Volatility | Sharpe | Sortino | Max drawdown | Worst month | Hit rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in WINDOWS:
        w = stats.windows.get(name)
        if w is None or not w.sufficient:
            continue
        rows.append(
            f"| {w.window} ({w.months}m) | {_fmt(w.annualized_return_pct, 2, '%')} | "
            f"{_fmt(w.annualized_volatility_pct, 2, '%')} | {_fmt(w.sharpe_ratio)} | "
            f"{_fmt(w.sortino_ratio)} | {_fmt(w.max_drawdown_pct, 1, '%')} | "
            f"{_fmt(w.worst_month_pct, 1, '%')} | {_fmt(w.hit_rate_pct, 0, '%')} |"
        )
    return "\n".join(rows) if len(rows) > 2 else "_No window has enough history to report._"


def _methods_table(methods: CmaMethodsBody, cma: CmaBody) -> str:
    weights = {w.method.value: w.weight for w in cma.judgment.method_weights}
    rows = [
        "| Method | Estimate | Confidence | Judge weight | Note |",
        "|---|---:|---:|---:|---|",
    ]
    for m in methods.methods:
        weight = weights.get(m.method.value)
        if m.unavailable_reason is not None:
            rows.append(f"| `{m.method.value}` | — | — | — | unavailable: {m.unavailable_reason} |")
            continue
        rows.append(
            f"| `{m.method.value}` | {_fmt(m.expected_return_pct, 2, '%')} | "
            f"{m.confidence:.2f} | "
            f"{'—' if not weight else f'{weight:.0%}'} | {m.rationale} |"
        )
    return "\n".join(rows)


def _signals_table(signals: SignalsBody | None, category: str) -> str:
    if signals is None:
        return "_`signals.json` is not in this run._"
    rows = [s for s in signals.signals if s.category == category]
    if not rows:
        return f"_No {category} signal was emitted for this asset._"
    out = ["| Signal | Value | Score | Reading |", "|---|---:|---:|---|"]
    for s in rows:
        # `Signal.value` is nullable: a signal may carry only its score.
        raw = "—" if s.value is None else f"{s.value:+.4f}"
        out.append(f"| {s.name} | {raw} | {s.score:+.3f} | {s.rationale} |")
    return "\n".join(out)


def _correlations_block(correlations: CorrelationRowBody | None) -> str:
    if correlations is None:
        return "_`correlation_row.json` is not in this run._"
    window = (
        "10y" if "10y" in correlations.correlations else next(iter(correlations.correlations), None)
    )
    if window is None:
        return "_No correlation window was computed._"
    row = correlations.correlations[window]
    ordered = sorted(row.items(), key=lambda kv: -kv[1])
    top = ordered[:3]
    bottom = ordered[-3:]
    lines = [
        f"Over the {window} window, against the other {len(row)} asset classes:",
        "",
        "| Most correlated | | Least correlated | |",
        "|---|---:|---|---:|",
    ]
    # Both slices are min(3, len(row)) long, so the rows always pair up.
    for (hi_id, hi), (lo_id, lo) in zip(top, reversed(bottom), strict=True):
        lines.append(f"| {hi_id} | {hi:+.2f} | {lo_id} | {lo:+.2f} |")
    return "\n".join(lines)


def _scenarios_block(scenarios: ScenariosBody | None, cma: CmaBody) -> str:
    low, high = cma.method_range
    if scenarios is None:
        return (
            "_`scenarios.json` is not in this run; run `uv run saa-skill scenarios`._ "
            f"The candidate range was {low:.2f}%–{high:.2f}%, a spread of {high - low:.2f}pp."
        )
    order = {"bear": 0, "base": 1, "bull": 2}
    rows = ["| Scenario | Return | Derivation |", "|---|---:|---|"]
    for s in sorted(scenarios.scenarios, key=lambda s: order.get(s.name, 9)):
        rows.append(f"| **{s.name}** | {s.expected_return_pct:.2f}% | {s.narrative} |")
    return "\n".join(rows)


def render_case(asset_id: str, data: CaseInputs, config: Config) -> str:
    """The 13 sections for one asset."""
    cma, judgment = data.cma, data.cma.judgment
    low, high = cma.method_range
    asset = next((a for a in config.universe.assets if a.id == asset_id), None)
    considerations = key_considerations(data.description)
    available = [m for m in data.methods.available if m.expected_return_pct is not None]
    weighted = [f"`{w.method.value}` {w.weight:.0%}" for w in judgment.method_weights if w.weight]

    s = []
    s.append(
        f"# {asset.name if asset else asset_id} — investment case\n\n"
        f"_{N_SECTIONS}-section investment case (Ang, Azimbayev & Kim 2026, Exhibit 3). "
        f"Horizon {cma.horizon_years} years, nominal. Section contents are our reconstruction; "
        f"the paper names the report without listing its sections._"
    )

    s.append(
        "## 1. Recommendation\n\n"
        f"**Expected return {cma.expected_return_pct:.2f}%** over "
        f"{cma.horizon_years} years, nominal, against expected volatility of "
        f"{cma.volatility_pct:.2f}%. Judge confidence **{judgment.confidence.value}**, "
        f"selection by **{judgment.selection.value.replace('_', ' ')}**"
        + (f" ({', '.join(weighted)})" if weighted else "")
        + f". The {len(available)} available candidates span {low:.2f}%–{high:.2f}% "
        f"({high - low:.2f}pp), described as **{judgment.dispersion.value}** dispersion."
    )

    s.append(
        "## 2. The asset class\n\n"
        + (
            f"**{asset.name}** ({asset.group.replace('_', ' ')}), tracked by `{asset.ticker}` "
            f"against {asset.benchmark}.\n\n"
            if asset
            else ""
        )
        + f"- **Macro sensitivity:** {_field(data.description, 'Macro sensitivity') or 'n/a'}\n"
        f"- **Primary valuation lens:** "
        f"{_field(data.description, 'Primary valuation lens') or 'n/a'}\n"
        + (
            f"- **Return history from** {data.stats.history_start} to {data.stats.data_end}"
            if data.stats
            else ""
        ).rstrip()
    )

    s.append(
        "## 3. Macro view\n\n"
        + (data.macro_line or "_No macro view is in this run._")
        + "\n\nThe judge's reading of what that implies for this asset:\n\n"
        f"> {judgment.regime_logic}"
    )

    s.append("## 4. Return and risk history\n\n" + _windows_table(data.stats))

    s.append("## 5. Correlations and portfolio role\n\n" + _correlations_block(data.correlations))

    s.append(
        "## 6. Valuation and fundamentals\n\n"
        + _signals_table(data.signals, "valuation")
        + "\n\nThe judge's valuation assessment:\n\n"
        f"> {judgment.valuation_context}"
    )

    s.append(
        "## 7. Technical signals\n\n"
        + _signals_table(data.signals, "technical")
        + "\n\nThe judge on how the signals line up against the methods:\n\n"
        f"> {judgment.signal_alignment}"
    )

    regime_note = (
        "_`by_regime` is empty in this run: the historical-analysis skill fills it only when a "
        "regime history is supplied, so the measured dimension alignments above are the whole "
        "of the regime evidence for this asset._"
        if not (data.stats and data.stats.by_regime)
        else "\n".join(
            [
                "| Regime | Months | Mean return (ann.) | Volatility |",
                "|---|---:|---:|---:|",
                *(
                    f"| {r.regime} | {r.months} | {_fmt(r.annualized_return_pct, 2, '%')} | "
                    f"{_fmt(r.annualized_volatility_pct, 2, '%')} |"
                    for r in data.stats.by_regime
                ),
            ]
        )
    )
    s.append(
        "## 8. Macro sensitivity and regime fit\n\n"
        + _signals_table(data.signals, "macro")
        + "\n\n"
        + regime_note
    )

    s.append(
        "## 9. Capital market assumption: the candidates\n\n"
        f"Eight candidates are computed by script with no model involved (§3.3). "
        f"Volatility ({data.methods.volatility_pct:.2f}%) comes from the covariance matrix, "
        f"not from a candidate.\n\n" + _methods_table(data.methods, cma)
    )

    s.append(
        "## 10. The judgment\n\n"
        f"Selection: **{judgment.selection.value.replace('_', ' ')}**"
        + (f" — {', '.join(weighted)}" if weighted else "")
        + f". Final estimate {judgment.expected_return_pct:.2f}%, inside the hard "
        f"[{low:.2f}, {high:.2f}] range Exhibit 4 requires.\n\n"
        f"> {judgment.rationale}"
    )

    s.append("## 11. Scenarios\n\n" + _scenarios_block(data.scenarios, cma))

    risks = "\n".join(f"{i}. {c}" for i, c in enumerate(considerations, 1))
    s.append(
        "## 12. Key risks and what would invalidate the view\n\n"
        "From this asset's own description file — the asset-class-specific instructions of "
        "Exhibit 3, which the judge was given before deciding:\n\n"
        + (risks or "_This asset's description file lists no key considerations._")
        + "\n\nThe `cma` contract carries no free-text notes field, so anything the judge "
        "wanted to flag beyond these appears in section 10's rationale."
    )

    sources = (
        "\n".join(
            f"- `{src.source}` ({src.kind}): {src.start} to {src.end}, {src.months} months"
            for src in data.stats.sources
        )
        if data.stats and data.stats.sources
        else "- _No source list in this run._"
    )
    s.append(
        "## 13. Provenance and limitations\n\n"
        "Return history is spliced from the longest-lived proxies backwards from the ETF "
        "(decision 3):\n\n" + sources + "\n\n"
        "**Known limitations of this case.**\n\n"
        "- **No sentiment, flows or positioning.** Exhibit 3 step 5 sources these from a "
        "runtime web search; this pipeline reads data only through `DataStore` (decision 26), "
        "so the category is omitted rather than proxied.\n"
        "- **The scenario range is methodological disagreement, not a stress test.** Tail risk "
        "is computed at the portfolio level by the CRO.\n"
        "- **Expected volatility is the covariance matrix's**, estimated over the full history "
        "with Ledoit–Wolf shrinkage, so it is not conditioned on the current regime.\n"
        f"- **The governing IPS (v{config.ips.version}) is {config.ips.standing}.**"
    )
    return "\n\n".join(s) + "\n"


# ------------------------------------------------------------------------------------ driving
def run_reports(run: RunContext, config: Config, assets: list[str] | None = None) -> ReportsResult:
    result = ReportsResult()
    ids = assets or sorted(p.name for p in (run.root / "cma").iterdir() if p.is_dir())
    for asset_id in ids:
        data = load_case_inputs(run, asset_id)
        text = render_case(asset_id, data, config)
        result.cases[asset_id] = AssetCase(
            asset_id=asset_id, text=text, sections=text.count("\n## ")
        )
    return result


def render_index(result: ReportsResult) -> str:
    lines = [
        "# Asset-class investment cases",
        "",
        f"The {N_SECTIONS}-section case per asset (Exhibit 3). One file each, at "
        "`cma/<asset>/analysis.md`.",
        "",
        "| Asset | Sections | Case |",
        "|---|---:|---|",
    ]
    for asset_id, case in sorted(result.cases.items()):
        lines.append(
            f"| {asset_id} | {case.sections} | [`analysis.md`](../cma/{asset_id}/analysis.md) |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(result: ReportsResult, run: RunContext) -> list[Path]:
    """Write ``cma/<asset>/analysis.md`` per asset and ``reports/asset_class_cases.md``."""
    written = [run.write_report(render_index(result), REPORT)]
    for asset_id, case in result.cases.items():
        written.append(run.write_report(case.text, ASSET_REPORT, asset_id=asset_id))
    return written

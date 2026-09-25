"""The macro regime agent (Ang et al. 2026 §3.1 step 1, §3.2, §4.1).

Runs first in the pipeline and publishes the view every downstream agent conditions on. Its
shape follows the paper's four-component anatomy: a markdown description (``AGENT.md``), a
deterministic skill (``skills.macro_regime``), scripts, and an output contract.

The division of labour is the point. ``skills.macro_regime`` computes the four dimension scores
and a rule-based regime prior with no LLM anywhere near it; the LLM then reads the indicator
table and forms the call, the confidence, the recession probability and the narrative. Running
without an API key still produces the deterministic half, which is what makes the regime
backtest in ``docs/macro_agent.md`` possible at all.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import yaml

from saa.config import PROJECT_ROOT, Config, load_config
from saa.contracts import (
    AgentOutput,
    Header,
    MacroJudgment,
    MacroScores,
    MacroViewBody,
    Producer,
    RegimeHistoryBody,
    RegimeMonth,
    Tier,
    write,
)
from saa.contracts.macro import DIMENSIONS
from saa.data.store import DataStore
from saa.llm import LlmClient
from saa.macro_scoring_config import MacroScoringConfig, cross_validate
from saa.skills.macro_regime import (
    ScorePanel,
    score_history,
    to_dimension_scores,
    to_pit_quality,
)

log = logging.getLogger(__name__)

AGENT = "macro"
AGENT_DIR = Path(__file__).parent
SKILL_PATH = PROJECT_ROOT / "src" / "saa" / "skills" / "macro_regime" / "SKILL.md"
DEFAULT_HISTORY_START = "1995-01-31"


def load_scoring_config(config: Config) -> MacroScoringConfig:
    path = config.config_dir / "macro_scoring.yaml"
    scoring = MacroScoringConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    cross_validate(scoring, config.macro)
    return scoring


@dataclass
class MacroRun:
    """Everything one macro-agent run produced."""

    view: AgentOutput
    history: AgentOutput
    panel: ScorePanel
    report: str
    paths: dict[str, Path]

    @property
    def regime(self) -> str:
        return self.view.body.judgment.regime.value

    @property
    def cost_usd(self) -> float:
        return self.view.header.cost_usd


# ------------------------------------------------------------------------------- prompting
def indicator_table(scores, panel: ScorePanel) -> str:
    """The evidence the LLM reasons over. One row per contributing series."""
    lines = []
    for dimension in scores:
        composite = dimension.score
        lines.append(f"\n### {dimension.dimension} (composite {composite:+.3f})")
        lines.append("| series | name | transform | score | weight | as of | point-in-time |")
        lines.append("|---|---|---|---|---|---|---|")
        for i in sorted(dimension.indicators, key=lambda x: -x.weight):
            lines.append(
                f"| {i.series_id} | {i.name} | {i.transform.value} | {i.score:+.3f} | "
                f"{i.weight:.2f} | {i.observation_date} | {'yes' if i.point_in_time else 'no'} |"
            )
    momentum = panel.momentum.iloc[-1]
    lines.append(
        f"\nGrowth momentum over the last {len(panel.momentum)} scored months "
        f"(change in the growth score): {momentum:+.3f}"
        if pd.notna(momentum)
        else "\nGrowth momentum: not computable (insufficient history)"
    )
    return "\n".join(lines)


def build_prompt(scores, panel: ScorePanel, *, as_of: date, ips_status: str) -> str:
    prior = panel.regimes.iloc[-1]
    confidence = panel.confidence.iloc[-1]
    data_end = panel.as_of.date()
    recent = panel.regimes.tail(13)
    runs = recent.ne(recent.shift()).cumsum()
    streak = int(runs.value_counts().get(runs.iloc[-1], 0))

    staleness = (
        f"The newest scoreable month is {data_end}, {(as_of - data_end).days} days before the "
        f"as-of date of {as_of}."
    )
    return f"""Classify the current US macroeconomic regime.

As-of date: {as_of}
{staleness}
Governing IPS status: {ips_status}

The four dimension scores below were computed deterministically by the macro-regime skill.
Each is in [-1, +1], where +1 is the risk-supportive direction: growth strong, inflation
contained, policy easy, financial conditions loose. Do not recompute them.

## Rule-based prior
The classification rules in config/macro_scoring.yaml give **{prior}** with deterministic
confidence {confidence:.2f}. That label has held for {streak} of the last 13 scored months.
Treat it as a prior, not an instruction. If you depart from it, name the rule you departed
from and why.

## Indicator detail
{indicator_table(scores, panel)}

## Recent regime path
{recent.to_string()}

Now produce your judgment: the regime, an optional qualifier if the four-way label loses
something material, a confidence level and score, a recession probability range, a one-line
rationale for each of the four dimensions, the key risks to monitor, and a narrative of a few
paragraphs a portfolio manager would read.
"""


def system_prompt() -> str:
    """The agent description plus the skill methodology, as the paper's §3.2 intends."""
    parts = [(AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")]
    if SKILL_PATH.exists():
        parts.append("\n\n---\n\n" + SKILL_PATH.read_text(encoding="utf-8"))
    return "".join(parts)


# ----------------------------------------------------------------------------------- report
def render_report(view: AgentOutput, panel: ScorePanel) -> str:
    """The markdown half of the contract (§3.2: JSON for machines, markdown for humans)."""
    body, header = view.body, view.header
    judgment, scores = body.judgment, body.scores
    qualifier = f" {judgment.regime_qualifier}" if judgment.regime_qualifier else ""
    probability = judgment.recession_probability

    lines = [
        "# Macro View",
        "",
        f"**Regime:** {judgment.regime.value}{qualifier}  ",
        f"**Confidence:** {judgment.confidence.value} ({judgment.confidence_score:.2f})  ",
        f"**Recession probability:** {probability.low_pct:.0f}–{probability.high_pct:.0f}%  ",
        f"**As of:** {header.as_of} (data through {scores.data_end})  ",
        f"**IPS:** v{header.ips_version} ({header.ips_status})",
        "",
        "## Dimension scores",
        "",
        "| dimension | score | indicators | point-in-time | rationale |",
        "|---|---|---|---|---|",
    ]
    rationales = {r.dimension: r.rationale for r in judgment.dimension_rationales}
    pit = {p.dimension: p for p in scores.pit_quality}
    for dimension in scores.dimensions:
        quality = pit.get(dimension.dimension)
        share = f"{quality.indicators_point_in_time}/{quality.indicators_total}" if quality else "-"
        lines.append(
            f"| {dimension.dimension} | {dimension.score:+.3f} | "
            f"{len(dimension.indicators)} | {share} | "
            f"{rationales.get(dimension.dimension, '')} |"
        )

    lines += ["", "## Narrative", "", judgment.narrative, "", "## Key risks", ""]
    lines += [f"- {risk}" for risk in judgment.key_risks]
    lines += [
        "",
        "## Provenance",
        "",
        f"- Scored history: {panel.scores.index[0].date()} to {panel.as_of.date()} "
        f"({len(panel.scores)} months)",
        f"- Point-in-time scoring: {'yes' if panel.point_in_time else 'no (latest vintage)'}",
        f"- Datasets: {', '.join(sorted(header.provenance)) or 'none recorded'}",
    ]
    if header.model_calls:
        call = header.model_calls[0]
        lines.append(f"- Model: {call.model} (effort {call.effort}), ${header.cost_usd:.4f}")
    if header.ips_status == "draft":
        lines += [
            "",
            "> The governing IPS has not been ratified. Figures are provisional.",
        ]
    return "\n".join(lines) + "\n"


# -------------------------------------------------------------------------------- the agent
def run(
    *,
    as_of: date | str | None = None,
    config: Config | None = None,
    store: DataStore | None = None,
    llm: LlmClient | None = None,
    out_dir: Path | str | None = None,
    pipeline_run_id: str | None = None,
    history_start: str = DEFAULT_HISTORY_START,
    point_in_time: bool = False,
    seed: int | None = None,
) -> MacroRun:
    """Score the four dimensions, classify the regime, and write the contract files."""
    config = config or load_config()
    store = store or DataStore(config)
    scoring = load_scoring_config(config)
    as_of_date = pd.Timestamp(as_of).date() if as_of else date.today()
    run_id = pipeline_run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    log.info("macro agent: scoring %d series as of %s", len(scoring.series_ids), as_of_date)
    panel = score_history(
        store,
        scoring,
        as_of=as_of_date,
        start=history_start,
        point_in_time=point_in_time,
    )

    dimensions = to_dimension_scores(panel, scoring, store)
    scores = MacroScores(
        dimensions=dimensions,
        pit_quality=to_pit_quality(dimensions),
        lookback_years=scoring.lookback_years,
        data_end=panel.as_of.date(),
        point_in_time=panel.point_in_time,
    )

    client = llm or LlmClient()
    judged = client.judge(
        MacroJudgment,
        system=system_prompt(),
        prompt=build_prompt(dimensions, panel, as_of=as_of_date, ips_status=config.ips.status),
        tier=Tier.FLAGSHIP,
    )
    judgment: MacroJudgment = judged.value

    def header_for(contract: str, produced_by: Producer, calls) -> Header:
        return Header(
            contract=contract,
            agent=AGENT,
            pipeline_run_id=run_id,
            as_of=as_of_date,
            generated_at=datetime.now(UTC),
            produced_by=produced_by,
            provenance=store.provenance(),
            ips_version=config.ips.version,
            ips_status=config.ips.status,
            model_calls=calls,
            seed=seed,
        )

    view = AgentOutput[MacroViewBody](
        header=header_for("macro_view", Producer.HYBRID, [judged.call]),
        body=MacroViewBody(scores=scores, judgment=judgment),
    )
    history = AgentOutput[RegimeHistoryBody](
        header=header_for("regime_history", Producer.SCRIPT, []),
        body=_regime_history(panel, scoring),
    )

    report = render_report(view, panel)
    paths = _write_all(view, history, report, out_dir, run_id)
    view.header.report_path = paths["report"].name

    log.info(
        "macro agent: %s (confidence %.2f), $%.4f",
        judgment.regime.value,
        judgment.confidence_score,
        view.header.cost_usd,
    )
    return MacroRun(view=view, history=history, panel=panel, report=report, paths=paths)


def _regime_history(panel: ScorePanel, scoring: MacroScoringConfig) -> RegimeHistoryBody:
    months = [
        RegimeMonth(
            date=stamp.date(),
            regime=panel.regimes.loc[stamp],
            confidence=float(panel.confidence.loc[stamp]),
            **{d: float(panel.scores.loc[stamp, d]) for d in DIMENSIONS},
        )
        for stamp in panel.scores.index
        if panel.scores.loc[stamp].notna().all()
    ]
    return RegimeHistoryBody(
        months=months,
        point_in_time=panel.point_in_time,
        lookback_years=scoring.lookback_years,
    )


def _write_all(view, history, report: str, out_dir, run_id: str) -> dict[str, Path]:
    root = Path(out_dir) if out_dir else PROJECT_ROOT / "data" / "runs" / run_id / "macro"
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / "macro.md"
    report_path.write_text(report, encoding="utf-8")
    return {
        "view": write(view, root / "macro-view.json"),
        "history": write(history, root / "regime_history.json"),
        "report": report_path,
    }

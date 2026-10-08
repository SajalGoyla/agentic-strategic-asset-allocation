"""The CMA judge: the LLM half of every asset-class agent (Ang et al. 2026 §3.3, Exhibit 4).

Stage 2 runs the eight candidate methods deterministically, then this agent picks among them.
§3.3 is explicit about the split -- the candidates "are written to a cma_methods.json file by a
Python script; no LLM judgment is involved up to this point. The judgment step follows."

One hard rule, from Exhibit 4: "final estimate MUST be within [min_method, max_method]". It is
enforced in three places, deliberately. The prompt states it, the `cma` contract rejects a body
that breaks it, and ``LlmClient.judge`` feeds a rejection back for another attempt. A judge that
drifts outside the candidate range is not expressing a view, it is inventing a number.

The 18 assets are independent, so they run concurrently against one shared system prompt, which
is cached: the agent description and the skill methodology are identical for every asset, and
only the per-asset evidence changes.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from saa.config import PROJECT_ROOT, Config, load_config
from saa.contracts import (
    CmaBody,
    CmaJudgment,
    CmaMethodId,
    CmaMethodsBody,
    Dispersion,
    MacroViewBody,
    ModelCall,
    Producer,
    SignalsBody,
    Tier,
    read,
)
from saa.contracts.asset_class import CMA_CONTRACT, HistoricalStatsBody
from saa.llm import LlmClient
from saa.run import RunContext

log = logging.getLogger(__name__)

AGENT = "cma-judge"
AGENT_DIR = Path(__file__).parent
SKILL_PATH = PROJECT_ROOT / "src" / "saa" / "skills" / "cma_methods" / "SKILL.md"
REPORT = "cma.md"
DEFAULT_WORKERS = 4


@dataclass
class AssetEvidence:
    """Everything the judge reads for one asset."""

    asset_id: str
    methods: CmaMethodsBody
    signals: SignalsBody | None = None
    stats: HistoricalStatsBody | None = None

    @property
    def dispersion(self) -> Dispersion:
        low, high = self.methods.method_range
        return Dispersion.classify(high - low)


@dataclass
class JudgedAsset:
    asset_id: str
    body: CmaBody
    evidence: AssetEvidence
    attempts: int
    call: ModelCall

    @property
    def cost_usd(self) -> float:
        return self.call.cost_usd or 0.0


@dataclass
class CmaJudgeResult:
    as_of: date
    judged: dict[str, JudgedAsset]
    failed: dict[str, str]
    regime: str | None

    @property
    def cost_usd(self) -> float:
        return sum(j.cost_usd for j in self.judged.values())


# ------------------------------------------------------------------------------- prompting
def system_prompt() -> str:
    """The agent description plus the skill methodology, per §3.2."""
    parts = [(AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")]
    if SKILL_PATH.exists():
        parts.append("\n\n---\n\n" + SKILL_PATH.read_text(encoding="utf-8"))
    return "".join(parts)


def _methods_table(methods: CmaMethodsBody) -> str:
    lines = [
        "| method | estimate % | confidence | components | rationale |",
        "|---|---|---|---|---|",
    ]
    for m in methods.methods:
        if m.unavailable_reason is not None:
            lines.append(
                f"| `{m.method.value}` | – | – | – | unavailable: {m.unavailable_reason} |"
            )
            continue
        components = ", ".join(f"{k} {v:+.2f}" for k, v in m.components.items()) or "–"
        lines.append(
            f"| `{m.method.value}` | {m.expected_return_pct:.2f} | {m.confidence:.2f} | "
            f"{components} | {m.rationale} |"
        )
    return "\n".join(lines)


def _signals_table(signals: SignalsBody | None) -> str:
    if signals is None or not signals.signals:
        return "No signals available for this asset."
    lines = [
        f"Composite **{signals.composite_score:+.2f}** (-1 bearish, +1 bullish).",
        "",
        "| signal | category | score | detail |",
        "|---|---|---|---|",
    ]
    for s in sorted(signals.signals, key=lambda x: (x.category.value, x.name)):
        lines.append(f"| {s.name} | {s.category.value} | {s.score:+.2f} | {s.rationale} |")
    return "\n".join(lines)


def _stats_table(stats: HistoricalStatsBody | None) -> str:
    if stats is None or not stats.windows:
        return "No historical statistics available for this asset."
    lines = [
        "| window | return % | volatility % | Sharpe | max drawdown % |",
        "|---|---|---|---|---|",
    ]
    for name, w in stats.windows.items():
        if not w.sufficient:
            continue

        def fmt(value, places=2):
            return "–" if value is None else f"{value:.{places}f}"

        lines.append(
            f"| {name} | {fmt(w.annualized_return)} | {fmt(w.annualized_volatility)} | "
            f"{fmt(w.sharpe_ratio)} | {fmt(w.max_drawdown)} |"
        )
    by_regime = [r for r in (stats.by_regime or []) if r.annualized_mean_return is not None]
    if by_regime:
        lines += ["", "| regime | mean return % | volatility % | months |", "|---|---|---|---|"]
        for r in by_regime:
            vol = "–" if r.annualized_volatility is None else f"{r.annualized_volatility:.2f}"
            lines.append(f"| {r.regime} | {r.annualized_mean_return:.2f} | {vol} | {r.months} |")
    return "\n".join(lines)


def build_prompt(
    evidence: AssetEvidence, macro: MacroViewBody | None, *, as_of: date, ips_status: str
) -> str:
    methods = evidence.methods
    low, high = methods.method_range
    available = [m.method.value for m in methods.available]
    blend = next((m for m in methods.available if m.method is CmaMethodId.AUTO_BLEND), None)
    regime_line = "No macro view available."
    if macro is not None:
        judgment = macro.judgment
        qualifier = f" {judgment.regime_qualifier}" if judgment.regime_qualifier else ""
        scores = ", ".join(f"{d.dimension} {d.score:+.2f}" for d in macro.scores.dimensions)
        regime_line = (
            f"Regime **{judgment.regime.value}{qualifier}**, confidence "
            f"{judgment.confidence.value} ({judgment.confidence_score:.2f}). "
            f"Dimension scores: {scores}. Recession probability "
            f"{judgment.recession_probability.low_pct:.0f}-"
            f"{judgment.recession_probability.high_pct:.0f}%."
        )

    return f"""Select the final capital market assumption for **{evidence.asset_id}**.

As-of date: {as_of}
Horizon: {methods.horizon_years} years, nominal, arithmetic annual return in percent
Volatility (from the covariance matrix): {methods.volatility_pct:.2f}%
Governing IPS status: {ips_status}

## Macro view (stage 1)
{regime_line}

## Candidate methods
Dispersion is **{evidence.dispersion.value}** — the available candidates span
{low:.2f}% to {high:.2f}%, a spread of {high - low:.2f}pp.
The confidence-weighted auto-blend is {"unavailable" if blend is None else f"{blend.expected_return_pct:.2f}%"}.

{_methods_table(methods)}

## Signals
{_signals_table(evidence.signals)}

## Historical statistics
{_stats_table(evidence.stats)}

## Your decision

Weigh the candidates and give the final estimate. You may name one method, set custom weights
across several, or accept the auto-blend.

Hard constraints:
- The final estimate must lie within [{low:.2f}, {high:.2f}]. Anything outside is rejected.
- `method_weights` may only name available methods: {", ".join(f"`{m}`" for m in available)}.
- Weights must be non-negative and sum to 1.0.
- `expected_return_pct` must equal the weighted average of the methods you weight, to within
  rounding.

Fill `regime_logic`, `valuation_context` and `signal_alignment` with reasoning specific to this
asset — not restatements of the tables above — and give an overall `rationale` for the choice.
"""


# ---------------------------------------------------------------------------------- report
def render_report(judged: JudgedAsset, macro: MacroViewBody | None) -> str:
    body, judgment = judged.body, judged.body.judgment
    methods = judged.evidence.methods
    low, high = body.method_range
    blend = next((m for m in methods.available if m.method is CmaMethodId.AUTO_BLEND), None)
    delta = (
        f"{body.expected_return_pct - blend.expected_return_pct:+.2f}pp vs. the auto-blend"
        if blend is not None
        else "no auto-blend to compare against"
    )
    weights = ", ".join(
        f"{m.value} {w:.0%}" for m, w in sorted(judgment.method_weights.items()) if w > 0
    )
    regime = macro.judgment.regime.value if macro is not None else "unknown"

    lines = [
        f"# CMA — {body.asset_id}",
        "",
        f"**Expected return:** {body.expected_return_pct:.2f}% "
        f"({methods.horizon_years}y, nominal, arithmetic)  ",
        f"**Volatility:** {body.volatility_pct:.2f}%  ",
        f"**Confidence:** {judgment.confidence.value}  ",
        f"**Selection:** {judgment.selection.value} — {weights}  ",
        f"**Candidate range:** {low:.2f}% to {high:.2f}% ({judgment.dispersion.value}); {delta}  ",
        f"**Regime:** {regime}",
        "",
        "## Candidates",
        "",
        _methods_table(methods),
        "",
        "## Judgment",
        "",
        f"**Regime logic.** {judgment.regime_logic}",
        "",
        f"**Valuation context.** {judgment.valuation_context}",
        "",
        f"**Signal alignment.** {judgment.signal_alignment}",
        "",
        f"**Rationale.** {judgment.rationale}",
    ]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------- the agent
def load_evidence(run: RunContext, asset_id: str) -> AssetEvidence:
    """Read one asset's stage-2 inputs from the run directory."""
    methods_path = run.path("cma_methods", asset_id=asset_id)
    if not methods_path.exists():
        raise FileNotFoundError(
            f"{asset_id}: {methods_path} not found; run `uv run saa-skill cma-methods` first"
        )
    evidence = AssetEvidence(asset_id=asset_id, methods=read("cma_methods", methods_path).body)

    for contract, attr in (("signals", "signals"), ("historical_stats", "stats")):
        path = run.path(contract, asset_id=asset_id)
        if path.exists():
            setattr(evidence, attr, read(contract, path).body)
        else:
            log.warning("%s: no %s.json in this run; the judge will see less", asset_id, contract)
    return evidence


def _load_macro(run: RunContext) -> MacroViewBody | None:
    path = run.path("macro_view")
    if not path.exists():
        log.warning("no macro-view.json in this run; the judge will see no regime")
        return None
    return read("macro_view", path).body


def judge_asset(
    evidence: AssetEvidence,
    macro: MacroViewBody | None,
    llm: LlmClient,
    *,
    as_of: date,
    ips_status: str,
    system: str,
) -> JudgedAsset:
    """One asset: prompt the judge, validate against the contract, return the body."""
    methods = evidence.methods
    result = llm.judge(
        CmaJudgment,
        system=system,
        prompt=build_prompt(evidence, macro, as_of=as_of, ips_status=ips_status),
        tier=Tier.FLAGSHIP,
    )
    judgment: CmaJudgment = result.value

    unavailable = {m.method for m in methods.methods if m.unavailable_reason is not None}
    named = {m for m, w in judgment.method_weights.items() if w > 0}
    if named & unavailable:
        raise ValueError(
            f"{evidence.asset_id}: judge weighted unavailable methods "
            f"{sorted(m.value for m in named & unavailable)}"
        )

    body = CmaBody(
        asset_id=evidence.asset_id,
        horizon_years=methods.horizon_years,
        expected_return_pct=judgment.expected_return_pct,
        volatility_pct=methods.volatility_pct,
        method_range=methods.method_range,
        judgment=judgment,
    )
    return JudgedAsset(
        asset_id=evidence.asset_id,
        body=body,
        evidence=evidence,
        attempts=result.attempts,
        call=result.call,
    )


def run_cma_judge(
    run: RunContext,
    *,
    config: Config | None = None,
    llm: LlmClient | None = None,
    assets: list[str] | None = None,
    workers: int = DEFAULT_WORKERS,
) -> CmaJudgeResult:
    """Judge every asset's CMA and write ``cma/<asset>/cma.json``.

    Assets are independent, so they run concurrently. One asset failing does not stop the
    others: it is recorded in ``failed`` and the run continues, the same way the ingestion
    pipeline carries on past a flaky source.
    """
    config = config or load_config()
    llm = llm or LlmClient()
    ids = assets or [a.id for a in config.universe.assets]
    macro = _load_macro(run)
    system = system_prompt()

    evidence: dict[str, AssetEvidence] = {}
    failed: dict[str, str] = {}
    for asset_id in ids:
        try:
            evidence[asset_id] = load_evidence(run, asset_id)
        except (FileNotFoundError, ValueError) as exc:
            failed[asset_id] = str(exc)

    judged: dict[str, JudgedAsset] = {}

    def work(asset_id: str) -> tuple[str, JudgedAsset | Exception]:
        try:
            return asset_id, judge_asset(
                evidence[asset_id],
                macro,
                llm,
                as_of=run.as_of,
                ips_status=run.ips_status,
                system=system,
            )
        except Exception as exc:  # one asset must not take down the stage
            return asset_id, exc

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for asset_id, outcome in pool.map(work, list(evidence)):
            if isinstance(outcome, Exception):
                log.error("cma judge: %s failed (%s)", asset_id, outcome)
                failed[asset_id] = repr(outcome)
            else:
                judged[asset_id] = outcome

    for asset_id, item in judged.items():
        report = run.write_report(render_report(item, macro), REPORT, asset_id=asset_id)
        inputs = [
            run.input_ref(contract, run.path(contract, asset_id=asset_id))
            for contract in ("cma_methods", "signals", "historical_stats")
            if run.path(contract, asset_id=asset_id).exists()
        ]
        if macro is not None:
            inputs.append(run.input_ref("macro_view", run.path("macro_view")))
        run.write(
            CMA_CONTRACT,
            AGENT,
            item.body,
            produced_by=Producer.HYBRID,
            asset_id=asset_id,
            inputs=inputs,
            report_path=report,
            model_calls=[item.call],
        )

    log.info(
        "cma judge: %d judged, %d failed, $%.4f",
        len(judged),
        len(failed),
        sum(j.cost_usd for j in judged.values()),
    )
    return CmaJudgeResult(
        as_of=run.as_of,
        judged=judged,
        failed=failed,
        regime=macro.judgment.regime.value if macro is not None else None,
    )


def render_summary(result: CmaJudgeResult) -> str:
    """Exhibit 8's shape: every method, the auto-blend, the judge, and the difference."""
    lines = [
        "# CMA Judge",
        "",
        f"As of {result.as_of}" + (f", regime **{result.regime}**" if result.regime else ""),
        "",
        "Expected returns in percent, nominal, arithmetic annual.",
        "",
        "| asset | range | auto-blend | judge | Δ vs blend | selection | dispersion |",
        "|---|---|---|---|---|---|---|",
    ]
    for asset_id, item in result.judged.items():
        low, high = item.body.method_range
        blend = next(
            (
                m.expected_return_pct
                for m in item.evidence.methods.available
                if m.method is CmaMethodId.AUTO_BLEND
            ),
            None,
        )
        final = item.body.expected_return_pct
        delta = "–" if blend is None else f"{final - blend:+.2f}"
        lines.append(
            f"| {asset_id} | {low:.1f}–{high:.1f} | "
            f"{'–' if blend is None else f'{blend:.2f}'} | {final:.2f} | {delta} | "
            f"{item.body.judgment.selection.value} | {item.body.judgment.dispersion.value} |"
        )
    if result.failed:
        lines += ["", "## Failed", ""]
        lines += [f"- **{asset_id}**: {reason}" for asset_id, reason in result.failed.items()]
    return "\n".join(lines) + "\n"


def write_summary(result: CmaJudgeResult, run: RunContext) -> Path:
    return run.write_report(render_summary(result), "cma_judge.md")


def latest_cmas(run: RunContext, config: Config) -> pd.Series:
    """Judged expected returns by asset, for the portfolio-construction stage."""
    out = {}
    for asset in config.universe.assets:
        path = run.path(CMA_CONTRACT, asset_id=asset.id)
        if path.exists():
            out[asset.id] = read(CMA_CONTRACT, path).body.expected_return_pct
    return pd.Series(out, dtype="float64")

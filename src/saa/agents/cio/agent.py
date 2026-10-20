"""The CIO agent (Ang et al. 2026 §3.6, §4.4, stage 6).

The ensembles are built and profiled by ``skills/ensemble`` over every candidate, with the
shortlisted five's revised proposals in place of their originals. Only IPS-compliant ensembles
reach the model, whose schema offers nothing else; it chooses one and writes the rationale, the
dissenting views, the invalidation conditions and the board memo. ``CioDecisionBody`` refuses a
non-compliant decision, so "non-negotiable" (§3.6) holds even if every other check failed.

``--no-llm`` picks the compliant ensemble with the best blend of backtest Sharpe and
diversification and writes a templated memo from the numbers, so the pipeline runs from data
to a recommended allocation for free.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import create_model

from saa.config import Config, load_config
from saa.contracts import (
    BoardMemo,
    CioDecisionBody,
    CioJudgment,
    CroReportBody,
    EnsembleMethod,
    ModelCall,
    PcProposalBody,
    Producer,
    Tier,
    read,
)
from saa.contracts.cio import DECISION_CONTRACT, MethodScore
from saa.contracts.review import TALLY_CONTRACT, VoteTallyBody
from saa.data.store import DataStore
from saa.ips import real_return_pct
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.ensemble import (
    Ensemble,
    EnsembleInputs,
    build_ensembles,
    default_choice,
    ensemble_score,
)
from saa.skills.method_scoring import (
    load_cro_reports,
    load_proposals,
    load_scoring_settings,
    score_candidates,
)
from saa.skills.portfolio_construction import StageInputs, gather_inputs

log = logging.getLogger(__name__)

AGENT = "cio"
AGENT_DIR = Path(__file__).parent
ENSEMBLE_REPORT = "cio_ensembles.md"
MEMO_REPORT = "board_memo.md"
MIN_RATIONALE_CHARS = 300


@dataclass
class CioResult:
    as_of: date
    body: CioDecisionBody
    ensembles: dict[EnsembleMethod, Ensemble]
    failed: dict[EnsembleMethod, str]
    chosen: EnsembleMethod
    call: ModelCall | None = None

    @property
    def cost_usd(self) -> float:
        return (self.call.cost_usd or 0.0) if self.call else 0.0


def system_prompt() -> str:
    return (AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")


def judgment_model(eligible: list[EnsembleMethod]) -> type[CioJudgment]:
    """``CioJudgment`` narrowed to the ensembles that passed the IPS."""
    choice = StrEnum("EligibleEnsemble", {m.name: m.value for m in eligible})
    return create_model("CioJudgmentFor", __base__=CioJudgment, ensemble_method=(choice, ...))


def load_candidates(run: RunContext, shortlist: list[str]) -> dict[str, PcProposalBody]:
    """Every proposal, with the shortlisted agents' revised versions in place of the originals
    (§3.5: the top five revise before the CIO sees them)."""
    proposals = load_proposals(run)
    for agent_id in shortlist:
        path = run.path("pc_proposal", agent_id=agent_id, revision=True)
        if path.exists():
            proposals[agent_id] = read("pc_proposal", path).body
    return proposals


def _top(weights: pd.Series, n: int = 5) -> list[tuple[str, float]]:
    top = weights[weights > 0.0005].sort_values(ascending=False)[:n]
    return [(a, float(w)) for a, w in top.items()]


def dissent(run: RunContext, tally: VoteTallyBody, share: float = 0.5) -> list[str]:
    """Candidates the vote flagged at the bottom on at least ``share`` of the ballots."""
    flags: Counter[str] = Counter()
    ballots = 0
    for path in sorted((run.root / "review").glob("*/vote.json")):
        ballot = read("vote", path).body
        ballots += 1
        if ballot.bottom_flag:
            flags[ballot.bottom_flag] += 1
    return [
        f"{agent} was bottom-flagged on {n} of {ballots} ballots"
        for agent, n in sorted(flags.items())
        if ballots and n / ballots >= share
    ]


def build_prompt(
    ensembles: dict[EnsembleMethod, Ensemble],
    tally: VoteTallyBody,
    dissents: list[str],
    *,
    regime: str | None,
    n_assets: int,
    ips_status: str,
) -> str:
    rows = [
        "| ensemble | vol % | TE % | backtest DD % | backtest Sharpe | exp. return % | eff. N "
        "| top holdings | note |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for method, e in ensembles.items():
        if not e.compliant:
            continue
        p = e.profile
        top = ", ".join(f"{a} {w:.0%}" for a, w in _top(e.final_weights, 3))
        rows.append(
            f"| {method.value} | {p.ex_ante_volatility_pct:.2f} | "
            f"{p.ex_ante_tracking_error_pct:.2f} | {p.max_drawdown_pct:.1f} | "
            f"{p.backtest_sharpe:.2f} | {e.expected_return_pct:.2f} | {p.effective_n:.1f} | "
            f"{top} | {e.note or '-'} |"
        )
    excluded = [m.value for m, e in ensembles.items() if not e.compliant]
    tally_rows = "\n".join(
        f"| {r.rank} | {r.agent_id} | {r.category.value} | {r.vote_points} | {r.composite:.3f} |"
        for r in tally.rows
    )
    return f"""Choose the recommended allocation and write the board memo.

As-of regime: {regime or "unknown"}
Governing IPS status: {ips_status}
Shortlist after the vote and the revisions: {", ".join(tally.shortlist)}

## The IPS-compliant ensembles (choose one)
{chr(10).join(rows)}

{"Not offered, because no compliant allocation could be found: " + ", ".join(excluded) if excluded else ""}

## The vote (Exhibit 9)
| rank | agent | family | points | composite |
|---|---|---|---|---|
{tally_rows}

## Dissent
{chr(10).join("- " + d for d in dissents) or "None at the threshold."}

## What to write
- `ensemble_method`: one of the ensembles above.
- `rationale`: why this ensemble suits the regime, what you traded away, and the assumptions.
- `dissenting_views`: views that cut against the recommendation, and why you still made it.
- `invalidation_conditions`: specific, checkable conditions under which this stops holding.
- `board_memo`: every section, for non-technical trustees, including the IPS statement.
"""


def fallback_judgment(
    chosen: Ensemble,
    stage: StageInputs,
    config: Config,
    dissents: list[str],
    *,
    regime: str | None,
    ips_status: str,
    n_candidates: int,
) -> CioJudgment:
    """``--no-llm``: the default choice, and a memo written from the numbers alone."""
    p = chosen.profile
    ips = config.ips
    ids = stage.asset_ids
    bench = stage.benchmark.reindex(ids).fillna(0.0)
    sigma = stage.covariance.loc[ids, ids].to_numpy(dtype=float)
    b = bench.to_numpy()
    bench_vol = 100 * float(np.sqrt(max(float(b @ sigma @ b), 0.0)))
    bench_ret = 100 * float(b @ stage.expected_returns.reindex(ids).to_numpy(dtype=float))
    real = (
        real_return_pct(chosen.expected_return_pct, stage.inflation_pct)
        if stage.inflation_pct is not None
        else None
    )
    top = "; ".join(f"{a} {w:.1%}" for a, w in _top(chosen.final_weights))
    projected = (
        f" It was projected into the IPS from {chosen.projected_from.ex_ante_volatility_pct:.2f}% "
        f"volatility and a {chosen.projected_from.max_drawdown_pct:.1f}% drawdown."
        if chosen.policy_adjusted
        else ""
    )
    draft = "a draft, not yet ratified" if ips_status == "draft" else ips_status
    statement = (
        f"Governed by IPS v{ips.version}, which is {draft}. The recommended allocation satisfies "
        f"every hard limit: ex-ante volatility {p.ex_ante_volatility_pct:.2f}% within the "
        f"{ips.objectives.volatility.min_pct:g}-{ips.objectives.volatility.max_pct:g}% band; "
        f"backtest maximum drawdown {p.max_drawdown_pct:.1f}% against a "
        f"{ips.objectives.max_drawdown.limit_pct:g}% limit; ex-ante tracking error "
        f"{p.ex_ante_tracking_error_pct:.2f}% against a "
        f"{ips.active_risk.tracking_error.max_ex_ante_pct:g}% budget"
        + (
            f"; expected real return {real:.2f}% against a CPI + "
            f"{ips.objectives.return_.min_pct:g}% floor."
            if real is not None
            else "."
        )
    )
    return CioJudgment(
        ensemble_method=chosen.method,
        rationale=(
            f"Generated without a model (--no-llm). The {chosen.method.value} ensemble of the "
            f"{n_candidates} candidate portfolios is the IPS-compliant ensemble with the best "
            "blend of backtest Sharpe ratio and diversification, weighted 25:15 as in §4.4 "
            f"(Sharpe {p.backtest_sharpe:.2f}, {p.effective_n:.1f} effective assets).{projected} "
            "No judgment has been applied: the regime, the reviews and the dissents were not "
            "weighed, and the memo is assembled from the figures."
        ),
        dissenting_views=dissents,
        invalidation_conditions=[
            f"the macro regime moves away from {regime or 'the current regime'}",
            f"ex-ante volatility leaves the {ips.objectives.volatility.min_pct:g}-"
            f"{ips.objectives.volatility.max_pct:g}% band at a quarterly review",
            f"realised drawdown passes {ips.objectives.max_drawdown.limit_pct:g}%",
            "a CMA for one of the five largest holdings is revised by more than 1 percentage point",
        ],
        board_memo=BoardMemo(
            recommendation=(
                f"Adopt the {chosen.method.value.replace('_', ' ')} ensemble of the "
                f"{n_candidates} candidate portfolios as the strategic allocation."
            ),
            expected_performance_vs_benchmark=(
                f"Expected return {chosen.expected_return_pct:.2f}% at {p.ex_ante_volatility_pct:.2f}% "
                f"volatility, against {bench_ret:.2f}% at {bench_vol:.2f}% for the 60/30/10 "
                f"benchmark; ex-ante tracking error {p.ex_ante_tracking_error_pct:.2f}%."
            ),
            macro_rationale=f"The macro agent's regime is {regime or 'unknown'}. Not interpreted.",
            largest_positions=top,
            changes_since_last_review="First recommendation: no previous allocation on record.",
            key_risks=[
                f"backtest maximum drawdown {p.max_drawdown_pct:.1f}%",
                f"monthly 95% VaR {p.var_95_pct:.2f}%" if p.var_95_pct is not None else "VaR n/a",
            ],
            rebalancing_plan=(
                f"Rebalance {ips.rebalancing.cadence}, on the calendar, back to these weights."
            ),
            ips_compliance_statement=statement,
        ),
    )


def run_cio(
    run: RunContext,
    store: DataStore | None,
    *,
    config: Config | None = None,
    llm: LlmClient | None = None,
    stage: StageInputs | None = None,
    regime_labels: pd.Series | None = None,
) -> CioResult:
    """Build the ensembles, choose one, and write ``cio/cio_decision.json`` and the memo."""
    config = config or load_config()
    tally_path = run.path(TALLY_CONTRACT)
    if not tally_path.exists():
        raise FileNotFoundError(
            f"{tally_path} not found; run `uv run saa-agent vote` and `saa-agent revise` first"
        )
    tally: VoteTallyBody = read(TALLY_CONTRACT, tally_path).body
    candidates = load_candidates(run, tally.shortlist)
    reports = load_cro_reports(run)
    stage = stage or gather_inputs(run, store, config=config)
    scoring = score_candidates(
        load_proposals(run), reports, stage, load_scoring_settings(config), labels=regime_labels
    )
    x = EnsembleInputs(
        weights=pd.DataFrame(
            {a: pd.Series(p.weights, dtype="float64") for a, p in candidates.items()}
        )
        .reindex(stage.asset_ids)
        .fillna(0.0),
        stage=stage,
        backtest_sharpe={a: _sharpe(reports.get(a)) for a in candidates},
        tally_composite={r.agent_id: r.composite for r in tally.rows},
        regime_fit={a: s.regime_fit for a, s in scoring.scores.items()},
        categories={a: p.category for a, p in candidates.items()},
    )
    compliant = [a for a in candidates if reports.get(a) and reports[a].ips_compliance.compliant]
    ensembles, failed = build_ensembles(x, config, compliant_candidates=compliant)
    eligible = [m for m, e in ensembles.items() if e.compliant]
    if not eligible:
        raise ValueError(
            "no ensemble of the candidates satisfies the IPS; the CIO cannot recommend an "
            "allocation (escalate: config/ips.yaml `hard_violation_unresolved`)"
        )
    dissents = dissent(run, tally)
    n_assets = len(stage.asset_ids)

    call = None
    if llm is None:
        chosen = ensembles[default_choice(ensembles, n_assets)]
        judgment = fallback_judgment(
            chosen,
            stage,
            config,
            dissents,
            regime=scoring.regime,
            ips_status=run.ips_status,
            n_candidates=len(candidates),
        )
    else:

        def check(judgment) -> None:
            if len(judgment.rationale) < MIN_RATIONALE_CHARS:
                raise ValueError(
                    f"CIO rationale is {len(judgment.rationale)} characters, too thin to put "
                    f"before a board (minimum {MIN_RATIONALE_CHARS})"
                )

        result = llm.judge(
            judgment_model(eligible),
            system=system_prompt(),
            prompt=build_prompt(
                ensembles,
                tally,
                dissents,
                regime=scoring.regime,
                n_assets=n_assets,
                ips_status=run.ips_status,
            ),
            tier=Tier.FLAGSHIP,
            check=check,
        )
        judgment, call = result.value, result.call
        chosen = ensembles[EnsembleMethod(str(judgment.ensemble_method))]

    body = decision_body(chosen, judgment, scoring.scores)
    run.write_report(render_ensembles(ensembles, failed, chosen.method, n_assets), ENSEMBLE_REPORT)
    memo = run.write_report(render_memo(body, run), MEMO_REPORT)
    run.write(
        DECISION_CONTRACT,
        AGENT,
        body,
        produced_by=Producer.HYBRID if call else Producer.SCRIPT,
        provenance=stage.provenance,
        inputs=[run.input_ref(TALLY_CONTRACT, tally_path), *stage.inputs],
        report_path=memo,
        model_calls=[call] if call else [],
    )
    log.info(
        "cio: %s ensemble, %d of %d eligible", chosen.method.value, len(eligible), len(ensembles)
    )
    return CioResult(
        as_of=run.as_of,
        body=body,
        ensembles=ensembles,
        failed=failed,
        chosen=chosen.method,
        call=call,
    )


def _sharpe(report: CroReportBody | None) -> float | None:
    return None if report is None else report.backtest_sharpe


def decision_body(
    chosen: Ensemble, judgment: CioJudgment, scores: dict[str, MethodScore]
) -> CioDecisionBody:
    final = chosen.final_weights[chosen.final_weights > 1e-6]
    final = final / final.sum()
    p = chosen.profile
    return CioDecisionBody(
        ensemble_method=chosen.method,
        ensemble_weights=chosen.ensemble_weights,
        final_weights={a: float(w) for a, w in final.items()},
        method_scores=sorted(scores.values(), key=lambda s: (-s.composite, s.agent_id)),
        expected_return_pct=chosen.expected_return_pct,
        expected_volatility_pct=p.ex_ante_volatility_pct,
        sharpe_ratio=chosen.sharpe_ratio,
        effective_n=p.effective_n,
        ex_ante_tracking_error_pct=p.ex_ante_tracking_error_pct,
        ips_compliance=p.compliance,
        dissenting_views=list(judgment.dissenting_views),
        invalidation_conditions=list(judgment.invalidation_conditions),
        rationale=judgment.rationale,
        board_memo=judgment.board_memo,
    )


# -------------------------------------------------------------------------------- reports
def render_ensembles(
    ensembles: dict[EnsembleMethod, Ensemble],
    failed: dict[EnsembleMethod, str],
    chosen: EnsembleMethod,
    n_assets: int,
) -> str:
    lines = [
        "# CIO ensembles",
        "",
        "Every ensemble of the candidate portfolios, profiled as a candidate is (§3.6). Only "
        "IPS-compliant ensembles may be recommended; a projected one breached a limit and was "
        "moved to the nearest compliant allocation.",
        "",
        "| ensemble | IPS | vol % | TE % | DD % | backtest Sharpe | return % | eff. N | score | "
        "chosen | note |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for method, e in ensembles.items():
        p = e.profile
        lines.append(
            f"| {method.value} | {'pass' if e.compliant else 'FAIL'} | "
            f"{p.ex_ante_volatility_pct:.2f} | {p.ex_ante_tracking_error_pct:.2f} | "
            f"{p.max_drawdown_pct:.1f} | {p.backtest_sharpe:.2f} | {e.expected_return_pct:.2f} | "
            f"{p.effective_n:.1f} | {ensemble_score(e, n_assets):.3f} | "
            f"{'yes' if method is chosen else ''} | {e.note or '-'} |"
        )
    if failed:
        lines += ["", "## Could not be built", ""]
        lines += [f"- **{m.value}**: {why}" for m, why in failed.items()]
    return "\n".join(lines) + "\n"


def render_memo(body: CioDecisionBody, run: RunContext) -> str:
    m = body.board_memo
    holdings = "\n".join(
        f"| {a} | {w:.1%} |" for a, w in sorted(body.final_weights.items(), key=lambda x: -x[1])
    )
    return f"""# Board memo — strategic asset allocation

Run `{run.run_id}`, as of {run.as_of}. Recommended by the CIO agent; ensemble
**{body.ensemble_method.value.replace("_", " ")}**.

## Recommendation
{m.recommendation}

## Expected performance against the benchmark
{m.expected_performance_vs_benchmark}

## Macro rationale
{m.macro_rationale}

## Largest positions
{m.largest_positions}

## Changes since the last review
{m.changes_since_last_review}

## Key risks to monitor
{chr(10).join("- " + r for r in m.key_risks)}

## Rebalancing plan
{m.rebalancing_plan}

## IPS compliance
{m.ips_compliance_statement}

## What would make this recommendation wrong
{chr(10).join("- " + c for c in body.invalidation_conditions)}

## Dissenting views
{chr(10).join("- " + d for d in body.dissenting_views) or "None recorded."}

## The allocation
| asset | weight |
|---|---|
{holdings}
"""


def render_summary(result: CioResult) -> str:
    b = result.body
    return (
        f"CIO: {result.chosen.value} ensemble. Expected return {b.expected_return_pct:.2f}%, "
        f"volatility {b.expected_volatility_pct:.2f}%, Sharpe {b.sharpe_ratio:.2f}, effective "
        f"assets {b.effective_n:.1f}, tracking error {b.ex_ante_tracking_error_pct:.2f}%. "
        f"IPS compliant: {b.ips_compliance.compliant}."
    )

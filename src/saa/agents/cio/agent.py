"""The CIO agent (Ang et al. 2026 §3.6, §4.4, stage 6).

The ensembles are built and profiled by ``skills/ensemble`` over every candidate, with the
shortlisted five's revised proposals in place of their originals, and scored on the candidates'
six-dimension rubric. The model sees what §3.6 lists -- the candidates, their peer reviews, CRO
risk reports, vote tallies and metric scores -- as a digest, with the IPS limits and the
compliant ensembles. Only IPS-compliant ensembles reach the model, whose schema offers nothing
else; it chooses one and writes the rationale, the dissenting views, the invalidation conditions
and the board memo. ``CioDecisionBody`` refuses a
non-compliant decision, so "non-negotiable" (§3.6) holds even if every other check failed.

``--no-llm`` picks the compliant ensemble with the best six-dimension composite and writes a templated memo from the numbers, so the pipeline runs from data
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

from saa.agents.vote import load_reviews
from saa.config import Config, load_config
from saa.contracts import (
    BoardMemo,
    CioDecisionBody,
    CioJudgment,
    CroReportBody,
    EnsembleMethod,
    ModelCall,
    PcProposalBody,
    PeerReviewBody,
    Producer,
    read,
)
from saa.contracts.cio import DECISION_CONTRACT, MethodScore
from saa.contracts.review import TALLY_CONTRACT, VoteTallyBody
from saa.data.store import DataStore
from saa.ips import real_return_pct
from saa.llm import LlmClient, tier_for
from saa.run import RunContext
from saa.skills.ensemble import (
    Ensemble,
    EnsembleInputs,
    build_ensembles,
    default_choice,
)
from saa.skills.method_scoring import (
    ScoringResult,
    ScoringSettings,
    load_cro_reports,
    load_proposals,
    load_scoring_settings,
    score_candidates,
    score_mix,
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


def score_ensembles(
    ensembles: dict[EnsembleMethod, Ensemble],
    scoring: ScoringResult,
    stage: StageInputs,
    settings: ScoringSettings,
    labels: pd.Series | None,
) -> dict[EnsembleMethod, MethodScore]:
    """Every ensemble on the six-dimension rubric the candidates are scored on (§3.6, §4.4)."""
    return {
        method: score_mix(
            f"ensemble:{method.value}",
            e.final_weights,
            e.ensemble_weights,
            backtest_sharpe=e.profile.backtest_sharpe,
            effective_n=e.profile.effective_n,
            compliance=e.profile.compliance,
            candidates=scoring,
            stage=stage,
            settings=settings,
            labels=labels,
        )
        for method, e in ensembles.items()
    }


def ips_limits(config: Config) -> str:
    """The IPS's limits as the CIO is held to them, so it can state them without guessing."""
    ips = config.ips
    o = ips.objectives
    bench = ", ".join(f"{a} {w:.0%}" for a, w in ips.active_risk.benchmark.weights.items())
    permitted = ips.universe.permitted
    rows = [
        "| rule | limit | severity |",
        "|---|---|---|",
        f"| expected real return | at least CPI + {o.return_.min_pct:g}% (no ceiling) | "
        f"{o.return_.severity} |",
        f"| ex-ante volatility | between {o.volatility.min_pct:g}% (floor) and "
        f"{o.volatility.max_pct:g}% (ceiling) | {o.volatility.severity} |",
        f"| backtest maximum drawdown | no worse than {o.max_drawdown.limit_pct:g}% | "
        f"{o.max_drawdown.severity} |",
        f"| ex-ante tracking error to the benchmark ({bench}) | at most "
        f"{ips.active_risk.tracking_error.max_ex_ante_pct:g}% | "
        f"{ips.active_risk.tracking_error.severity} |",
        f"| long only, no leverage, no derivatives | "
        f"{'yes' if permitted.long_only and not permitted.leverage else 'see policy'} | hard |",
    ]
    escalation = [
        f"- {e.condition}"
        + (f" (threshold {e.threshold:g})" if e.threshold is not None else "")
        + f": {e.action}"
        + (f". {e.note}" if e.note else "")
        for e in ips.escalation
    ]
    return (
        f"IPS v{ips.version}, {ips.status}. Rebalancing {ips.rebalancing.cadence}; horizon "
        f"{o.cma_horizon_years} years.\n\n"
        + "\n".join(rows)
        + "\n\nEscalation rules:\n"
        + ("\n".join(escalation) or "- none")
    )


def regime_confidence(run: RunContext) -> float | None:
    """The macro agent's confidence score, if this run has a macro view."""
    path = run.path("macro_view")
    if not path.exists():
        return None
    return read("macro_view", path).body.judgment.confidence_score


def escalations(config: Config, *, confidence: float | None, composite: float | None) -> list[str]:
    """The IPS escalation rules a decision triggers. ``composite`` is the chosen ensemble's
    six-dimension score; None before the choice, when only the regime rule can be judged.
    ``hard_violation_unresolved`` is not here: it stops the stage before a choice exists."""
    out = []
    for e in config.ips.escalation:
        if e.threshold is None:
            continue
        if e.condition == "regime_confidence_below" and confidence is not None:
            if confidence < e.threshold:
                out.append(
                    f"{e.condition}: the macro agent's regime confidence is {confidence:.2f}, "
                    f"below {e.threshold:g}; action: {e.action}. {e.note or ''}".rstrip()
                )
        elif e.condition == "cio_selects_below_composite" and composite is not None:
            if composite < e.threshold:
                out.append(
                    f"{e.condition}: the chosen ensemble's composite is {composite:.3f}, below "
                    f"{e.threshold:g}; action: {e.action}. {e.note or ''}".rstrip()
                )
    return out


def _first(items: list[str]) -> str:
    return items[0] if items else "none stated"


def candidate_digest(
    candidates: dict[str, PcProposalBody],
    reports: dict[str, CroReportBody],
    reviews: list[PeerReviewBody],
    tally: VoteTallyBody,
    originals: dict[str, PcProposalBody] | None = None,
) -> str:
    """One block per candidate, in vote order: what §3.6 gives the CIO -- the portfolio, its
    CRO report, its peer reviews, its vote and metric scores -- cut to what bears on a choice."""
    by_reviewed: dict[str, list[PeerReviewBody]] = {}
    for r in reviews:
        by_reviewed.setdefault(r.reviewed_agent_id, []).append(r)
    blocks = []
    for row in tally.rows:
        p = candidates.get(row.agent_id)
        if p is None:
            continue
        report = reports.get(row.agent_id)
        hard = [v.rule for v in p.ips_compliance.violations if v.severity == "hard"]
        ex_ante = "compliant" if not hard else "breaches " + ", ".join(hard)
        original = (originals or {}).get(row.agent_id)
        moved = p.revision_of is not None and (
            original is None
            or any(
                abs(p.weights.get(a, 0.0) - original.weights.get(a, 0.0)) > 1e-9
                for a in set(p.weights) | set(original.weights)
            )
        )
        if moved or report is None:
            # A revision is not re-backtested; its CRO report is on the original.
            ips = f"ex-ante {ex_ante}; backtest drawdown not re-checked after revision"
        else:
            full = [v.rule for v in report.ips_compliance.violations if v.severity == "hard"]
            ips = f"ex-ante {ex_ante}; with the backtest " + (
                "compliant" if not full else "breaches " + ", ".join(full)
            )
        eff = "–" if p.effective_n is None else f"{p.effective_n:.1f}"
        top = ", ".join(f"{a} {w:.0%}" for a, w in _top(pd.Series(p.weights), 3))
        lines = [
            f"### {row.rank}. `{row.agent_id}` — {p.method} ({p.category.value})"
            + (" — revised" if p.revision_of else ""),
            f"- vote {row.vote_points} points, metric score {row.metric_score:.3f}, composite "
            f"{row.composite:.3f}",
            f"- return {p.expected_return_pct:.2f}%, volatility {p.expected_volatility_pct:.2f}%, "
            f"Sharpe {p.sharpe_ratio:.2f}, {eff} effective assets (entropy); top: {top}",
            f"- IPS: {ips}",
        ]
        if report is not None:
            dd = "–" if report.max_drawdown_pct is None else f"{report.max_drawdown_pct:.1f}%"
            bs = "–" if report.backtest_sharpe is None else f"{report.backtest_sharpe:.2f}"
            lines.append(
                f"- CRO{' (on the original)' if moved else ''}: risk score "
                f"{report.risk_score:.2f}, backtest Sharpe {bs}, drawdown {dd}; binding risk: "
                f"{_first(report.judgment.key_risks)}"
            )
        for r in sorted(by_reviewed.get(row.agent_id, []), key=lambda r: r.reviewer_agent_id):
            errors = "; ".join(r.technical_errors)
            lines.append(
                f"- review by `{r.reviewer_agent_id}` ({r.score:.2f}): {_first(r.weaknesses)}"
                + (f" Technical errors: {errors}" if errors else "")
            )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _projection(e: Ensemble) -> str:
    if e.projected_from is None:
        return "none"
    before = e.projected_from
    return (
        f"from {before.ex_ante_volatility_pct:.2f}% vol, {before.max_drawdown_pct:.1f}% DD; "
        f"{e.projection_turnover:.1%} of the portfolio moved"
    )


def build_prompt(
    ensembles: dict[EnsembleMethod, Ensemble],
    scores: dict[EnsembleMethod, MethodScore],
    tally: VoteTallyBody,
    dissents: list[str],
    digest: str,
    *,
    config: Config,
    regime: str | None,
    ips_status: str,
    confidence: float | None = None,
) -> str:
    triggered = escalations(config, confidence=confidence, composite=None)
    below = [
        f"{m.value} ({s.composite:.3f})"
        for m, s in scores.items()
        if ensembles[m].compliant
        and any(
            e.condition == "cio_selects_below_composite"
            and e.threshold is not None
            and s.composite < e.threshold
            for e in config.ips.escalation
        )
    ]
    escalation_block = "\n".join(f"- TRIGGERED: {t}" for t in triggered) or "- none triggered"
    escalation_block += (
        "\n- cio_selects_below_composite would trigger if you chose: " + ", ".join(below)
        if below
        else "\n- cio_selects_below_composite: no offered ensemble is below its threshold"
    )
    rows = [
        "| ensemble | composite | vol % | TE % | backtest DD % | backtest Sharpe | exp. return % "
        "| Sharpe | eff. N assets | candidates held | largest share | eff. N candidates "
        "| projection | top holdings |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    dims = [
        "| ensemble | Sharpe 25% | IPS 15% | divers. 15% | regime 20% | robust. 15% | CMA 10% "
        "| composite |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for method, e in ensembles.items():
        if not e.compliant:
            continue
        p, s = e.profile, scores[method]
        top = ", ".join(f"{a} {w:.0%}" for a, w in _top(e.final_weights, 3))
        lead, share = e.largest_share
        rows.append(
            f"| {method.value} | {s.composite:.3f} | {p.ex_ante_volatility_pct:.2f} | "
            f"{p.ex_ante_tracking_error_pct:.2f} | {p.max_drawdown_pct:.1f} | "
            f"{p.backtest_sharpe:.2f} | {e.expected_return_pct:.2f} | {e.sharpe_ratio:.2f} | "
            f"{p.effective_n:.1f} | {e.candidates_held} | {lead} {share:.0%} | "
            f"{e.effective_candidates:.1f} | {_projection(e)} | {top} |"
        )
        dims.append(
            f"| {method.value} | {s.backtest_sharpe:.2f} | {s.ips_compliance:.2f} | "
            f"{s.diversification:.2f} | {s.regime_fit:.2f} | {s.estimation_robustness:.2f} | "
            f"{s.cma_utilization:.2f} | {s.composite:.3f} |"
        )
    excluded = [m.value for m, e in ensembles.items() if not e.compliant]
    tally_rows = "\n".join(
        f"| {r.rank} | {r.agent_id} | {r.category.value} | {r.vote_points} | {r.composite:.3f} |"
        for r in tally.rows
    )
    return f"""Choose the recommended allocation and write the board memo.

As-of regime: {regime or "unknown"} (macro agent's confidence: {"unknown" if confidence is None else f"{confidence:.2f}"})
Governing IPS status: {ips_status}

## IPS escalation rules in this run
Evaluated by the script; the memo's IPS statement must report any that are triggered.
{escalation_block}
Shortlist after the vote and the revisions: {", ".join(tally.shortlist)}

## The IPS limits your recommendation is held to
{ips_limits(config)}

## The IPS-compliant ensembles (choose one)
{chr(10).join(rows)}

"Candidates held" counts candidates with at least 1% of the ensemble; "eff. N candidates" is
the entropy-based effective number of them. "Projection" is how far the ensemble had to be moved
to comply with the IPS, from the figures it had before.

{"Not offered, because no compliant allocation could be found: " + ", ".join(excluded) if excluded else ""}

### The same six-dimension score as the candidates (§4.4)
What the allocation has is measured on it: backtest Sharpe, IPS compliance, diversification,
and its Sharpe ratio in the current regime placed on the candidates' range. Estimation
robustness and CMA use are the mix of its candidates'. The scores inform your judgment; they
do not make it.

{chr(10).join(dims)}

## The vote (Exhibit 9)
| rank | agent | family | points | composite |
|---|---|---|---|---|
{tally_rows}

## The candidates: portfolio, CRO report, peer reviews, scores
The shortlisted five are shown as revised; their CRO reports are on the originals.

{digest}

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
    score: float,
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
        f"volatility and a {chosen.projected_from.max_drawdown_pct:.1f}% drawdown, moving "
        f"{chosen.projection_turnover:.1%} of the portfolio."
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
            f"six-dimension composite of §4.4, {score:.3f} (backtest Sharpe "
            f"{p.backtest_sharpe:.2f}, {p.effective_n:.1f} effective assets).{projected} "
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
    settings = load_scoring_settings(config)
    scoring = score_candidates(load_proposals(run), reports, stage, settings, labels=regime_labels)
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
    confidence = regime_confidence(run)
    scores = score_ensembles(ensembles, scoring, stage, settings, regime_labels)
    composites = {m: s.composite for m, s in scores.items()}

    call = None
    if llm is None:
        chosen = ensembles[default_choice(ensembles, composites)]
        judgment = fallback_judgment(
            chosen,
            stage,
            config,
            dissents,
            regime=scoring.regime,
            ips_status=run.ips_status,
            n_candidates=len(candidates),
            score=composites[chosen.method],
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
                scores,
                tally,
                dissents,
                candidate_digest(
                    candidates, reports, load_reviews(run), tally, load_proposals(run)
                ),
                config=config,
                regime=scoring.regime,
                ips_status=run.ips_status,
                confidence=confidence,
            ),
            tier=tier_for("cio"),
            check=check,
        )
        judgment, call = result.value, result.call
        chosen = ensembles[EnsembleMethod(str(judgment.ensemble_method))]

    body = decision_body(chosen, judgment, scoring.scores).model_copy(
        update={
            "escalations": escalations(
                config, confidence=confidence, composite=composites[chosen.method]
            )
        }
    )
    run.write_report(render_ensembles(ensembles, failed, chosen.method, scores), ENSEMBLE_REPORT)
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
    scores: dict[EnsembleMethod, MethodScore],
) -> str:
    lines = [
        "# CIO ensembles",
        "",
        "Every ensemble of the candidate portfolios, profiled as a candidate is (§3.6). Only "
        "IPS-compliant ensembles may be recommended; a projected one breached a limit and was "
        "moved to the nearest compliant allocation. The score is the candidates' six-dimension "
        "composite (§4.4).",
        "",
        "| ensemble | IPS | vol % | TE % | DD % | backtest Sharpe | return % | eff. N | "
        "candidates held | largest share | projection moved | score | chosen | note |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for method, e in ensembles.items():
        p = e.profile
        lead, share = e.largest_share
        moved = f"{e.projection_turnover:.1%}" if e.policy_adjusted else "-"
        lines.append(
            f"| {method.value} | {'pass' if e.compliant else 'FAIL'} | "
            f"{p.ex_ante_volatility_pct:.2f} | {p.ex_ante_tracking_error_pct:.2f} | "
            f"{p.max_drawdown_pct:.1f} | {p.backtest_sharpe:.2f} | {e.expected_return_pct:.2f} | "
            f"{p.effective_n:.1f} | {e.candidates_held} | {lead} {share:.0%} | {moved} | "
            f"{scores[method].composite:.3f} | {'yes' if method is chosen else ''} | "
            f"{e.note or '-'} |"
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

## Escalations under the IPS
{chr(10).join("- " + e for e in body.escalations) or "None triggered."}

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

"""The Chief Risk Officer agent (Ang et al. 2026 §3.5, stage 5).

"A Chief Risk Officer (CRO) agent produces a standardized risk report for each candidate
portfolio ... The CRO-agent is a neutral assessor: it scores risk and produces commentary, but
does not vote."

The metrics and the composite risk score come from ``skills/risk``; the model reads them and
writes the assessment. It sees one portfolio at a time and has no ballot, which is how
"neutral assessor" and "does not vote" are enforced rather than asked for in a prompt.

``--no-llm`` produces every metric and every score with no API key and no spend, which is how
the risk layer gets checked for free.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from saa.agents.pc.agent import agent_slug
from saa.config import Config, load_config
from saa.contracts import (
    CroJudgment,
    CroReportBody,
    ModelCall,
    PcCategory,
    PcProposalBody,
    Producer,
    Tier,
    read,
)
from saa.contracts.portfolio import PROPOSAL_CONTRACT, PROPOSAL_FILENAME
from saa.contracts.review import CRO_CONTRACT
from saa.data.store import DataStore
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.portfolio_construction import StageInputs, gather_inputs
from saa.skills.risk import RiskProfile, profile_portfolio

log = logging.getLogger(__name__)

AGENT = "cro"
AGENT_DIR = Path(__file__).parent
SKILL_PATH = Path(__file__).resolve().parents[3] / "saa" / "skills" / "risk" / "SKILL.md"
SUMMARY_REPORT = "cro_reports.md"
DEFAULT_WORKERS = 4

# Commentary shorter than this is a restatement of the table, not an assessment.
MIN_COMMENTARY_CHARS = 250


@dataclass
class Report:
    profile: RiskProfile
    body: CroReportBody
    call: ModelCall | None = None

    @property
    def agent_id(self) -> str:
        return self.profile.agent_id

    @property
    def cost_usd(self) -> float:
        return (self.call.cost_usd or 0.0) if self.call else 0.0


@dataclass
class CroResult:
    as_of: date
    reports: dict[str, Report]
    skipped: dict[str, str]
    stage: StageInputs

    @property
    def cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.reports.values())


def system_prompt() -> str:
    parts = [(AGENT_DIR / "AGENT.md").read_text(encoding="utf-8")]
    if SKILL_PATH.exists():
        parts.append("\n\n---\n\n" + SKILL_PATH.read_text(encoding="utf-8"))
    return "".join(parts)


# -------------------------------------------------------------------------------- proposals
def load_proposals(run: RunContext) -> dict[str, PcProposalBody]:
    """Every ``pc_proposal.json`` in the run, keyed by the agent id inside it.

    The directory name is the header slug (``pc-max-sharpe``); the body carries the canonical
    agent id (``max_sharpe``), which is what the vote and the CIO will key on.
    """
    proposals: dict[str, PcProposalBody] = {}
    for path in sorted((run.root / "pc").glob(f"*/{PROPOSAL_FILENAME}")):
        body: PcProposalBody = read(PROPOSAL_CONTRACT, path).body
        proposals[body.agent_id] = body
    return proposals


# ----------------------------------------------------------------------------------- prompt
def _metrics_table(profile: RiskProfile) -> str:
    def pct(value: float | None) -> str:
        return "not available" if value is None else f"{value:.2f}%"

    rows = [
        ("ex-ante volatility", pct(profile.ex_ante_volatility_pct)),
        ("ex-ante tracking error vs. the IPS benchmark", pct(profile.ex_ante_tracking_error_pct)),
        ("backtest volatility", pct(profile.backtest_volatility_pct)),
        (
            "backtest Sharpe",
            "not available"
            if profile.backtest_sharpe is None
            else f"{profile.backtest_sharpe:.2f}",
        ),
        ("monthly 95% VaR (loss)", pct(profile.var_95_pct)),
        ("monthly 95% CVaR (loss)", pct(profile.cvar_95_pct)),
        ("maximum drawdown", pct(profile.max_drawdown_pct)),
        ("effective number of assets", f"{profile.effective_n:.1f}"),
        ("concentration (Herfindahl)", f"{profile.concentration_hhi:.3f}"),
        (
            "months of backtest history",
            "none" if profile.backtest_months is None else str(profile.backtest_months),
        ),
    ]
    return "\n".join(["| metric | value |", "|---|---|", *(f"| {k} | {v} |" for k, v in rows)])


def _weights_table(weights: dict[str, float], asset_ids: list[str], benchmark: pd.Series) -> str:
    lines = ["| asset | weight | vs benchmark |", "|---|---|---|"]
    for asset_id in asset_ids:
        w = weights.get(asset_id, 0.0)
        if w <= 0.0005:
            continue
        lines.append(f"| {asset_id} | {w:.1%} | {w - float(benchmark.get(asset_id, 0.0)):+.1%} |")
    held = sum(1 for w in weights.values() if w > 0.0005)
    lines.append(f"\n{held} of {len(asset_ids)} assets held.")
    return "\n".join(lines)


def build_prompt(
    profile: RiskProfile, proposal: PcProposalBody, stage: StageInputs, *, ips_status: str
) -> str:
    violations = (
        "\n".join(f"- [{v.severity}] {v.rule}: {v.message}" for v in profile.compliance.violations)
        or "None."
    )
    not_evaluated = ", ".join(profile.compliance.not_evaluated) or "none"
    components = "\n".join(
        f"- {name}: {value:.2f}" for name, value in sorted(profile.risk_score_components.items())
    )
    tilts = "\n".join(
        f"- {name}: {value:+.1%}" if name.startswith("active_") else f"- {name}: {value:.2f}"
        for name, value in sorted(profile.factor_tilts.items())
    )
    return f"""Assess the risk of one candidate portfolio.

Portfolio: **{profile.method}** ({profile.category.value}), proposed by agent
`{profile.agent_id}`
As-of date: {stage.as_of}
Macro regime: {stage.regime or "unknown"}
Governing IPS status: {ips_status}

## Computed metrics
{_metrics_table(profile)}

## Weights
{_weights_table(proposal.weights, stage.asset_ids, stage.benchmark)}

## Factor tilts
{tilts}

## IPS compliance
Compliant (no hard violation): **{profile.compliance.compliant}**
{violations}

Not evaluated: {not_evaluated}

## Risk score
Composite: **{profile.risk_score:.2f}** of 1.00 (higher is riskier). Components:
{components}

## The proposing agent's own case

{proposal.rationale}

{("Its notes: " + proposal.notes) if proposal.notes else ""}

## What to write

- `key_risks`: the concrete risks in this portfolio, most binding first. Name exposures and
  assets, not categories of risk.
- `concentration_assessment`: is the concentration the method working or failing? Say which.
- `tail_risk_assessment`: what the tail looks like, and whether the backtest's tail is credible
  for these assets given the panel starts in 1993.
- `ips_assessment`: what each violation above means for this candidate — not whether it is
  allowed. Breaches do not disqualify a candidate; the hard limits bind on the CIO's final
  portfolio.
- `commentary`: the assessment a reviewer and the CIO will read, a few paragraphs. Say which
  risk binds and whether the ex-ante or the backtest figure is the one to trust here.

You are a neutral assessor. Do not rank this portfolio, recommend it, or compare it with the
other candidates — you are seeing one of fifteen. Do not restate the metrics as prose.
"""


def _fallback_judgment(profile: RiskProfile) -> CroJudgment:
    """Used by ``--no-llm``. Deterministic, and honest about being written without a model."""
    hard = [v for v in profile.compliance.violations if v.severity == "hard"]
    soft = [v for v in profile.compliance.violations if v.severity == "soft"]
    risks = [f"{v.rule}: {v.message}" for v in hard] or [
        f"ex-ante volatility {profile.ex_ante_volatility_pct:.2f}% with "
        f"{profile.effective_n:.1f} effective assets; no hard IPS violation"
    ]
    drawdown = (
        f"maximum drawdown {profile.max_drawdown_pct:.2f}%"
        if profile.max_drawdown_pct is not None
        else "no backtest history, so drawdown and VaR were not evaluated"
    )
    return CroJudgment(
        key_risks=risks,
        concentration_assessment=(
            f"Herfindahl {profile.concentration_hhi:.3f}, effective assets "
            f"{profile.effective_n:.1f}. Not assessed against the method's intent."
        ),
        tail_risk_assessment=drawdown + ". No judgment applied.",
        ips_assessment=(
            f"{len(hard)} hard and {len(soft)} soft violations recorded, and "
            f"{len(profile.compliance.not_evaluated)} rules not evaluated. Not interpreted."
        ),
        commentary=(
            f"Risk report for {profile.method} ({profile.category.value}) generated without a "
            f"model (--no-llm). Ex-ante volatility {profile.ex_ante_volatility_pct:.2f}%, "
            f"ex-ante tracking error {profile.ex_ante_tracking_error_pct:.2f}%, composite risk "
            f"score {profile.risk_score:.2f}. {drawdown.capitalize()}. The metrics and the score "
            "are computed and final; no interpretation has been applied to them."
        ),
    )


def body_from(profile: RiskProfile, judgment: CroJudgment) -> CroReportBody:
    return CroReportBody(
        portfolio_agent_id=profile.agent_id,
        method=profile.method,
        category=profile.category,
        ex_ante_volatility_pct=profile.ex_ante_volatility_pct,
        backtest_volatility_pct=profile.backtest_volatility_pct,
        var_95_pct=profile.var_95_pct,
        cvar_95_pct=profile.cvar_95_pct,
        max_drawdown_pct=profile.max_drawdown_pct,
        backtest_sharpe=profile.backtest_sharpe,
        ex_ante_tracking_error_pct=profile.ex_ante_tracking_error_pct,
        backtest_months=profile.backtest_months,
        effective_n=profile.effective_n,
        concentration_hhi=profile.concentration_hhi,
        factor_tilts=profile.factor_tilts,
        ips_compliance=profile.compliance,
        risk_score=profile.risk_score,
        risk_score_components=profile.risk_score_components,
        judgment=judgment,
    )


def assess(
    profile: RiskProfile,
    proposal: PcProposalBody,
    stage: StageInputs,
    llm: LlmClient | None,
    *,
    ips_status: str,
    system: str,
) -> Report:
    """One portfolio: computed metrics in, risk report out."""
    if llm is None:
        return Report(profile=profile, body=body_from(profile, _fallback_judgment(profile)))

    def check(judgment: CroJudgment) -> None:
        if len(judgment.commentary) < MIN_COMMENTARY_CHARS:
            raise ValueError(
                f"{profile.agent_id}: commentary is {len(judgment.commentary)} characters, too "
                f"thin for a risk report (minimum {MIN_COMMENTARY_CHARS})"
            )

    result = llm.judge(
        CroJudgment,
        system=system,
        prompt=build_prompt(profile, proposal, stage, ips_status=ips_status),
        tier=Tier.FLAGSHIP,
        check=check,
    )
    judgment: CroJudgment = result.value
    return Report(profile=profile, body=body_from(profile, judgment), call=result.call)


# -------------------------------------------------------------------------------------- run
def _risk_free_series(stage: StageInputs) -> pd.Series | float:
    """Realised cash returns where the universe has a cash asset, else the current T-bill rate.

    A backtest Sharpe measured against today's rate over thirty years would be meaningless, so
    the cash asset's own return path is the right risk-free series when it is available.
    """
    panel = stage.scenario_returns
    if panel is not None and stage.cash_id and stage.cash_id in panel.columns:
        return panel[stage.cash_id]
    return stage.risk_free


def profile_proposal(proposal: PcProposalBody, stage: StageInputs, config: Config) -> RiskProfile:
    return profile_portfolio(
        proposal.agent_id,
        proposal.method,
        PcCategory(proposal.category),
        pd.Series(proposal.weights, dtype="float64"),
        config=config,
        covariance=stage.covariance,
        benchmark=stage.benchmark,
        inflation_pct=stage.inflation_pct,
        expected_return_pct=proposal.expected_return_pct,
        scenario_returns=stage.scenario_returns,
        risk_free_series=_risk_free_series(stage),
    )


def run_cro(
    run: RunContext,
    store: DataStore,
    *,
    config: Config | None = None,
    llm: LlmClient | None = None,
    agents: list[str] | None = None,
    workers: int = DEFAULT_WORKERS,
    stage: StageInputs | None = None,
) -> CroResult:
    """Write ``review/<agent_id>/cro_report.json`` for every candidate portfolio in the run.

    ``llm=None`` writes the computed metrics with a deterministic placeholder assessment, so
    the risk layer can be checked without an API key. ``stage`` overrides reading the stage
    inputs off disk, which is what a caller already holding them (or a test) passes.
    """
    config = config or load_config()
    # Checked before the stage inputs: a run with no proposals is the likelier mistake, and its
    # message is the more useful one.
    proposals = load_proposals(run)
    if not proposals:
        raise FileNotFoundError(
            f"no pc_proposal.json found under {run.root / 'pc'}; run "
            f"`uv run saa-agent pc --run-id {run.run_id}` first"
        )
    if stage is None:
        stage = gather_inputs(run, store, config=config)
    available = sorted(proposals)
    unknown: list[str] = []
    if agents:
        unknown = sorted(set(agents) - set(proposals))
        proposals = {k: v for k, v in proposals.items() if k in agents}

    system = system_prompt() if llm is not None else ""
    skipped: dict[str, str] = {
        agent_id: f"no proposal in this run; found {available}" for agent_id in unknown
    }
    reports: dict[str, Report] = {}

    def work(agent_id: str):
        try:
            profile = profile_proposal(proposals[agent_id], stage, config)
            return agent_id, assess(
                profile,
                proposals[agent_id],
                stage,
                llm,
                ips_status=run.ips_status,
                system=system,
            )
        except Exception as exc:
            return agent_id, exc

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for agent_id, outcome in pool.map(work, list(proposals)):
            if isinstance(outcome, Exception):
                log.error("cro report for %s failed (%s)", agent_id, outcome)
                skipped[agent_id] = repr(outcome)
            else:
                reports[agent_id] = outcome

    for agent_id, report in reports.items():
        # The proposal this report assesses belongs in the run DAG alongside the stage inputs.
        inputs = list(stage.inputs)
        proposal_path = run.path(PROPOSAL_CONTRACT, agent_id=agent_slug(agent_id))
        if proposal_path.exists():
            inputs.append(run.input_ref(PROPOSAL_CONTRACT, proposal_path))
        run.write(
            CRO_CONTRACT,
            AGENT,
            report.body,
            produced_by=Producer.HYBRID if report.call else Producer.SCRIPT,
            agent_id=agent_id,
            provenance=stage.provenance,
            inputs=inputs,
            model_calls=[report.call] if report.call else [],
        )

    log.info(
        "cro: %d reports, %d skipped, $%.4f",
        len(reports),
        len(skipped),
        sum(r.cost_usd for r in reports.values()),
    )
    return CroResult(as_of=run.as_of, reports=reports, skipped=skipped, stage=stage)


# ----------------------------------------------------------------------------------- report
def render_summary(result: CroResult) -> str:
    stage = result.stage
    lines = [
        "# CRO Risk Reports",
        "",
        f"As of {result.as_of}" + (f", regime **{stage.regime}**" if stage.regime else ""),
        "",
        "The CRO scores risk and comments; it does not vote (§3.5).",
        "",
        "| agent | category | ex-ante vol % | backtest vol % | VaR 95 % | max DD % | "
        "Sharpe | eff. N | TE % | risk score | IPS |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    def num(value: float | None, places: int = 2) -> str:
        return "–" if value is None else f"{value:.{places}f}"

    for agent_id, report in sorted(result.reports.items(), key=lambda kv: -kv[1].body.risk_score):
        b = report.body
        lines.append(
            f"| {agent_id} | {b.category.value} | {num(b.ex_ante_volatility_pct)} | "
            f"{num(b.backtest_volatility_pct)} | {num(b.var_95_pct)} | "
            f"{num(b.max_drawdown_pct)} | {num(b.backtest_sharpe)} | {num(b.effective_n, 1)} | "
            f"{num(b.ex_ante_tracking_error_pct)} | {num(b.risk_score)} | "
            f"{'pass' if b.ips_compliance.compliant else 'FAIL'} |"
        )
    if result.skipped:
        lines += ["", "## Skipped", ""]
        lines += [f"- **{k}**: {v}" for k, v in result.skipped.items()]

    lines += ["", "## Key risks", ""]
    for agent_id, report in sorted(result.reports.items()):
        risks = "; ".join(report.body.judgment.key_risks)
        lines.append(f"- **{agent_id}** (score {report.body.risk_score:.2f}): {risks}")
    return "\n".join(lines) + "\n"


def write_summary(result: CroResult, run: RunContext) -> Path:
    return run.write_report(render_summary(result), SUMMARY_REPORT)

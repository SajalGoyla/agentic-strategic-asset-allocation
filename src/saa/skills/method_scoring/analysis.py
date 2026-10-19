"""Scoring a run's candidates: read the proposals and CRO reports, score, report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from saa.config import Config
from saa.contracts import read
from saa.contracts.portfolio import PROPOSAL_CONTRACT, PROPOSAL_FILENAME, PcProposalBody
from saa.contracts.review import CRO_CONTRACT, CRO_FILENAME, CroReportBody
from saa.data.store import DataStore
from saa.run import RunContext
from saa.skills.method_scoring.scoring import (
    ScoringResult,
    ScoringSettings,
    load_scoring_settings,
    render_report,
    score_candidates,
)
from saa.skills.portfolio_construction import StageInputs, gather_inputs

REPORT = "method_scores.md"


def load_proposals(run: RunContext) -> dict[str, PcProposalBody]:
    """Every proposal in the run, keyed by the canonical agent id in its body."""
    out: dict[str, PcProposalBody] = {}
    for path in sorted((run.root / "pc").glob(f"*/{PROPOSAL_FILENAME}")):
        body: PcProposalBody = read(PROPOSAL_CONTRACT, path).body
        out[body.agent_id] = body
    return out


def load_cro_reports(run: RunContext) -> dict[str, CroReportBody]:
    """Every CRO report in the run, keyed by the agent id of the portfolio it assesses."""
    out: dict[str, CroReportBody] = {}
    for path in sorted((run.root / "review").glob(f"*/{CRO_FILENAME}")):
        body: CroReportBody = read(CRO_CONTRACT, path).body
        out[body.portfolio_agent_id] = body
    return out


def run_method_scoring(
    run: RunContext,
    store: DataStore,
    *,
    config: Config,
    settings: ScoringSettings | None = None,
    regime_labels: pd.Series | None = None,
    stage: StageInputs | None = None,
) -> ScoringResult:
    proposals = load_proposals(run)
    if not proposals:
        raise FileNotFoundError(
            f"no pc_proposal.json under {run.root / 'pc'}; run `uv run saa-agent pc` first"
        )
    reports = load_cro_reports(run)
    if not reports:
        raise FileNotFoundError(
            f"no cro_report.json under {run.root / 'review'}; run `uv run saa-agent cro` first"
        )
    stage = stage or gather_inputs(run, store, config=config)
    return score_candidates(
        proposals,
        reports,
        stage,
        settings or load_scoring_settings(config),
        labels=regime_labels,
    )


def write_report(result: ScoringResult, run: RunContext) -> Path:
    return run.write_report(render_report(result), REPORT)

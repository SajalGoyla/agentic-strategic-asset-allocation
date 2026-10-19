"""The six-dimension metric score of each candidate portfolio (Ang et al. 2026 §3.5, §4.4).

One rubric, two users. §3.5 blends the vote with "a quantitative metric score (a weighted
composite of backtest Sharpe, IPS compliance, diversification, regime fit, estimation risk, and
CMA utilization)"; §4.4 has the CIO score "each of the 21 PC methods on six dimensions --
backtest Sharpe (25%), IPS compliance (15%), diversification (15%), regime fit (20%),
estimation robustness (15%), and CMA utilization (10%)". Computing it once, here, keeps the
vote and the CIO on the same ruler. Deterministic: every dimension is a number from the run.

The weights are ``saa.contracts.cio.SCORE_WEIGHTS``, which ``MethodScore`` validates against;
how each dimension is measured is ``config/method_scoring.yaml``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field

from saa.config import Config
from saa.contracts.cio import SCORE_WEIGHTS, MethodScore
from saa.contracts.portfolio import PcProposalBody
from saa.contracts.review import CroReportBody
from saa.skills.portfolio_construction import ADVERSARIAL, METHODS, RESEARCH_LIBRARY, StageInputs
from saa.skills.risk.analysis import backtest_returns

log = logging.getLogger(__name__)

MONTHS_PER_YEAR = 12
NEUTRAL = 0.5  # a dimension that cannot be measured counts as neither good nor bad
DIMENSIONS = tuple(SCORE_WEIGHTS)


# ------------------------------------------------------------------------------- settings
class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IpsComplianceSettings(_Model):
    hard_min: float = Field(ge=0.0, le=1.0)
    hard_max: float = Field(ge=0.0, le=1.0)
    tolerance_fraction: float = Field(gt=0.0)
    soft: float = Field(ge=0.0, le=1.0)


class RegimeFitSettings(_Model):
    min_months: int = Field(gt=0)
    prior: dict[str, dict[str, float]]


class RobustnessSettings(_Model):
    by_method: dict[str, float]
    default: float = Field(ge=0.0, le=1.0)


class CmaUtilizationSettings(_Model):
    uses_cmas_share: float = Field(ge=0.0, le=1.0)


class ScoringSettings(_Model):
    sharpe_anchors: tuple[float, float]
    ips_compliance: IpsComplianceSettings
    regime_fit: RegimeFitSettings
    estimation_robustness: RobustnessSettings
    cma_utilization: CmaUtilizationSettings


def load_scoring_settings(config: Config, path: Path | str | None = None) -> ScoringSettings:
    path = Path(path) if path is not None else config.config_dir / "method_scoring.yaml"
    settings = ScoringSettings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    known = set(METHODS) | set(RESEARCH_LIBRARY) | {ADVERSARIAL.id}
    unknown = sorted(set(settings.estimation_robustness.by_method) - known)
    if unknown:
        raise ValueError(f"method_scoring.yaml scores unknown methods {unknown}")
    lo, hi = settings.sharpe_anchors
    if not lo < hi:
        raise ValueError(f"sharpe_anchors {settings.sharpe_anchors} must be increasing")
    return settings


# ------------------------------------------------------------------------------ dimensions
def sharpe_to_score(sharpe: float | None, anchors: tuple[float, float]) -> float | None:
    if sharpe is None or not np.isfinite(sharpe):
        return None
    lo, hi = anchors
    return float(np.clip((sharpe - lo) / (hi - lo), 0.0, 1.0))


def ips_compliance_score(report: CroReportBody, s: IpsComplianceSettings) -> float:
    """1.0 for a compliant portfolio; each breach costs by its kind and, for a hard one, by how
    far past the limit it is. A rule never evaluated costs nothing here -- the CRO lists it."""
    score = 1.0
    for v in report.ips_compliance.violations:
        if v.severity != "hard":
            score -= s.soft
            continue
        magnitude = 1.0
        if v.observed is not None and v.limit not in (None, 0):
            overshoot = abs(v.observed - v.limit) / (s.tolerance_fraction * abs(v.limit))
            magnitude = float(np.clip(overshoot, 0.0, 1.0))
        score -= s.hard_min + (s.hard_max - s.hard_min) * magnitude
    return float(np.clip(score, 0.0, 1.0))


def diversification_score(report: CroReportBody, n_assets: int, weights: pd.Series) -> float:
    """Meucci (2009) effective number of assets over the number available: 1/N scores 1."""
    effective_n = report.effective_n
    if effective_n is None:
        w = weights[weights > 0]
        effective_n = float(np.exp(-(w * np.log(w)).sum())) if len(w) else 0.0
    return float(np.clip(effective_n / n_assets, 0.0, 1.0))


@dataclass(frozen=True)
class RegimeFit:
    score: float
    source: str  # "measured" or "prior"
    months: int
    sharpe: float | None


def regime_fit(
    weights: pd.Series,
    category: str,
    stage: StageInputs,
    regime: str | None,
    labels: pd.Series | None,
    settings: ScoringSettings,
) -> RegimeFit:
    """How the portfolio did in the months labelled like today: its backtest Sharpe ratio over
    the past months in the current regime -- quarterly-rebalanced, as the CRO backtests it,
    against cash's own returns. ``score`` here is provisional; ``relative_regime_fit`` turns the
    measured Sharpe ratios into scores across the roster.

    Falls back to the per-family prior from ``method_scoring.yaml`` where the history in this
    regime is too thin, which encodes §4.3's finding that covariance-based methods are
    preferred late in the cycle.
    """
    s = settings.regime_fit
    prior = s.prior.get(regime or "", {}).get(category, NEUTRAL)
    panel = stage.scenario_returns
    if regime is None or labels is None or panel is None or panel.empty:
        return RegimeFit(prior, "prior", 0, None)

    returns = backtest_returns(weights, panel[stage.asset_ids])
    month = pd.DatetimeIndex(labels.index).to_period("M")
    by_month = pd.Series(labels.to_numpy(), index=month)
    in_regime = returns.index.to_period("M").map(by_month.to_dict()) == regime
    sample = returns[np.asarray(in_regime, dtype=bool)]
    if len(sample) < s.min_months:
        return RegimeFit(prior, "prior", len(sample), None)

    if stage.cash_id and stage.cash_id in panel.columns:
        rf = panel[stage.cash_id].reindex(sample.index).fillna(0.0)
    else:
        rf = pd.Series(stage.risk_free / MONTHS_PER_YEAR, index=sample.index)
    excess = sample - rf
    vol = float(excess.std(ddof=1))
    sharpe = float(excess.mean() / vol * np.sqrt(MONTHS_PER_YEAR)) if vol > 0 else None
    if sharpe is None or not np.isfinite(sharpe):
        return RegimeFit(prior, "prior", len(sample), None)
    return RegimeFit(NEUTRAL, "measured", len(sample), sharpe)


def relative_regime_fit(fits: dict[str, RegimeFit]) -> dict[str, RegimeFit]:
    """Score the measured fits relative to each other: the lowest in-regime Sharpe ratio of the
    roster maps to 0, the highest to 1.

    Relative, unlike ``backtest_sharpe``, because the regime moves every portfolio together:
    in the expansion months since 1993 every candidate's Sharpe ratio is above 0.8, so an
    absolute scale saturates and cannot tell them apart. What "fit" asks is which portfolios do
    better than their peers in this regime. With one measured fit, or all equal, it is neutral.
    """
    measured = {k: f.sharpe for k, f in fits.items() if f.source == "measured"}
    if not measured:
        return dict(fits)
    lo, hi = min(measured.values()), max(measured.values())
    out = dict(fits)
    for agent_id, sharpe in measured.items():
        score = NEUTRAL if hi - lo < 1e-12 else (sharpe - lo) / (hi - lo)
        f = fits[agent_id]
        out[agent_id] = RegimeFit(float(score), f.source, f.months, f.sharpe)
    return out


def method_id_of(proposal: PcProposalBody) -> str:
    """The method behind a proposal: the agent id for the registry, the method the researcher
    actually ran (by name) for the researcher."""
    if proposal.agent_id in METHODS or proposal.agent_id == ADVERSARIAL.id:
        return proposal.agent_id
    for method in RESEARCH_LIBRARY.values():
        if method.name == proposal.method:
            return method.id
    return proposal.agent_id


def uses_cmas(method_id: str) -> bool:
    method = METHODS.get(method_id) or RESEARCH_LIBRARY.get(method_id)
    if method is None:
        return method_id == ADVERSARIAL.id and ADVERSARIAL.uses_cmas
    return method.uses_cmas


def cma_alignment(weights: pd.Series, stage: StageInputs) -> float:
    """How far the weights lean toward the assets the CMAs favour, in [0, 1].

    The rank correlation between active weights against equal weight and each asset's CMA
    Sharpe ratio, mapped from [-1, 1]. Equal weight has no active weights and scores 0.5:
    it leans neither way.
    """
    ids = stage.asset_ids
    active = weights.reindex(ids).fillna(0.0) - 1.0 / len(ids)
    if float(active.abs().max()) < 1e-9:
        return NEUTRAL
    vols = np.sqrt(np.diag(stage.covariance.loc[ids, ids].to_numpy(dtype=float)))
    excess = stage.expected_returns.reindex(ids).to_numpy(dtype=float) - stage.risk_free
    attractiveness = pd.Series(excess / np.where(vols > 0, vols, np.nan), index=ids)
    rho = active.rank().corr(attractiveness.rank())
    if rho is None or not np.isfinite(rho):
        return NEUTRAL
    return float((rho + 1.0) / 2.0)


# ---------------------------------------------------------------------------------- score
@dataclass
class ScoreDetail:
    """The raw inputs behind one candidate's six scores, for the report."""

    method_id: str
    category: str
    backtest_sharpe: float | None
    effective_n: float | None
    violations: list[str]
    regime: RegimeFit
    uses_cmas: bool
    cma_alignment: float
    unmeasured: list[str] = field(default_factory=list)


@dataclass
class ScoringResult:
    scores: dict[str, MethodScore]
    details: dict[str, ScoreDetail]
    regime: str | None

    def ranked(self) -> list[MethodScore]:
        return sorted(self.scores.values(), key=lambda s: (-s.composite, s.agent_id))


def score_candidate(
    proposal: PcProposalBody,
    report: CroReportBody,
    stage: StageInputs,
    settings: ScoringSettings,
    *,
    fit: RegimeFit,
) -> tuple[MethodScore, ScoreDetail]:
    """One candidate's six scores. ``fit`` comes from ``relative_regime_fit``, because regime
    fit is scored against the rest of the roster."""
    weights = pd.Series(proposal.weights, dtype="float64")
    method_id = method_id_of(proposal)
    category = proposal.category.value
    unmeasured: list[str] = []

    sharpe = sharpe_to_score(report.backtest_sharpe, settings.sharpe_anchors)
    if sharpe is None:
        sharpe = NEUTRAL
        unmeasured.append("backtest_sharpe")
    if fit.source != "measured":
        unmeasured.append("regime_fit")
    robustness = settings.estimation_robustness
    reads_cmas = uses_cmas(method_id)
    alignment = cma_alignment(weights, stage)
    share = settings.cma_utilization.uses_cmas_share

    dims = {
        "backtest_sharpe": sharpe,
        "ips_compliance": ips_compliance_score(report, settings.ips_compliance),
        "diversification": diversification_score(report, len(stage.asset_ids), weights),
        "regime_fit": fit.score,
        "estimation_robustness": robustness.by_method.get(method_id, robustness.default),
        "cma_utilization": share * float(reads_cmas) + (1.0 - share) * alignment,
    }
    dims = {k: round(float(v), 6) for k, v in dims.items()}
    composite = round(sum(dims[k] * w for k, w in SCORE_WEIGHTS.items()), 6)
    score = MethodScore(agent_id=proposal.agent_id, composite=composite, **dims)
    detail = ScoreDetail(
        method_id=method_id,
        category=category,
        backtest_sharpe=report.backtest_sharpe,
        effective_n=report.effective_n,
        violations=[f"{v.severity}: {v.rule}" for v in report.ips_compliance.violations],
        regime=fit,
        uses_cmas=reads_cmas,
        cma_alignment=alignment,
        unmeasured=unmeasured,
    )
    return score, detail


def score_candidates(
    proposals: dict[str, PcProposalBody],
    reports: dict[str, CroReportBody],
    stage: StageInputs,
    settings: ScoringSettings,
    *,
    regime: str | None = None,
    labels: pd.Series | None = None,
) -> ScoringResult:
    """Score every candidate that has both a proposal and a CRO report.

    ``regime`` defaults to the stage's (the macro view's), then to the last label.
    """
    missing = sorted(set(proposals) - set(reports))
    if missing:
        raise ValueError(
            f"{len(missing)} candidates have no CRO report ({', '.join(missing)}); run "
            "`uv run saa-agent cro --run-id <run>` first"
        )
    if regime is None:
        regime = stage.regime
    if regime is None and labels is not None and len(labels.dropna()):
        regime = str(labels.dropna().iloc[-1])

    fits = relative_regime_fit(
        {
            agent_id: regime_fit(
                pd.Series(p.weights, dtype="float64"),
                p.category.value,
                stage,
                regime,
                labels,
                settings,
            )
            for agent_id, p in proposals.items()
        }
    )
    scores: dict[str, MethodScore] = {}
    details: dict[str, ScoreDetail] = {}
    for agent_id in sorted(proposals):
        scores[agent_id], details[agent_id] = score_candidate(
            proposals[agent_id], reports[agent_id], stage, settings, fit=fits[agent_id]
        )
    return ScoringResult(scores=scores, details=details, regime=regime)


# --------------------------------------------------------------------------------- report
def render_report(result: ScoringResult) -> str:
    lines = [
        "# Method scores",
        "",
        "The six-dimension metric score (§4.4) the vote blends with its Borda points (§3.5) and "
        "the CIO scores candidates on. Each dimension is 0-1; the composite uses the paper's "
        "weights. Definitions: `config/method_scoring.yaml`.",
        "",
        f"Regime: **{result.regime or 'unknown'}**.",
        "",
        "| rank | agent | family | composite | Sharpe 25% | IPS 15% | divers. 15% | regime 20% "
        "| robust. 15% | CMA 10% |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for rank, s in enumerate(result.ranked(), start=1):
        d = result.details[s.agent_id]
        fit = f"{s.regime_fit:.2f}" + ("" if d.regime.source == "measured" else "*")
        lines.append(
            f"| {rank} | {s.agent_id} | {d.category} | **{s.composite:.3f}** | "
            f"{s.backtest_sharpe:.2f} | {s.ips_compliance:.2f} | {s.diversification:.2f} | {fit} | "
            f"{s.estimation_robustness:.2f} | {s.cma_utilization:.2f} |"
        )
    lines += [
        "",
        "Regime fit is relative: the roster's lowest Sharpe ratio in this regime scores 0, the "
        "highest 1. \\* from the per-family prior instead: too little history to measure.",
        "",
        "## Inputs",
        "",
        "| agent | method | backtest Sharpe | eff. N | regime months | regime Sharpe | uses CMAs "
        "| CMA lean | IPS breaches |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for agent_id, d in result.details.items():
        sharpe = "–" if d.backtest_sharpe is None else f"{d.backtest_sharpe:.2f}"
        eff = "–" if d.effective_n is None else f"{d.effective_n:.1f}"
        rs = "–" if d.regime.sharpe is None else f"{d.regime.sharpe:.2f}"
        lines.append(
            f"| {agent_id} | {d.method_id} | {sharpe} | {eff} | {d.regime.months} | {rs} | "
            f"{'yes' if d.uses_cmas else 'no'} | {d.cma_alignment:.2f} | "
            f"{'; '.join(d.violations) or '-'} |"
        )
    return "\n".join(lines) + "\n"

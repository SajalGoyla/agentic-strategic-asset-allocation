"""The CIO's ensemble techniques, and the diagnostics each ensemble is judged on (§3.6, §4.4).

"In addition to being able to choose a given portfolio method, it has access to several
ensemble techniques: simple average, inverse tracking-error weighting, backtest-Sharpe
weighting, meta-optimization that treats PC portfolios as 'assets' in a second-level
optimization, regime-conditional weighting (which varies method weights by macro regime),
composite-score weighting, and a trimmed mean that excludes statistical outliers. The CIO-agent
evaluates each ensemble on the same diagnostic suite used for individual portfolios --
performance statistics and checking IPS compliance (which is non-negotiable)."

Every ensemble is a set of weights over the candidate portfolios. The final allocation is their
weighted sum, and it is profiled by the CRO's own risk skill -- ex-ante volatility and tracking
error, the quarterly-rebalanced backtest and its drawdown, and the full IPS check -- so an
ensemble and a candidate are measured on one ruler. Only a fully compliant ensemble is eligible.
Deterministic; the choice among eligible ensembles is the CIO agent's.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from saa.config import Config
from saa.contracts.cio import EnsembleMethod
from saa.contracts.portfolio import PcCategory
from saa.skills.portfolio_construction import StageInputs
from saa.skills.risk import RiskProfile, profile_portfolio

log = logging.getLogger(__name__)

MONTHS_PER_YEAR = 12
TRIM_SHARE = 0.1  # share of candidates the trimmed mean drops as outliers, at least one
# The meta-optimisation's drawdown constraint is fitted on a monthly-rebalanced approximation
# of the backtest; the CRO's quarterly backtest then verifies it. A margin keeps the two from
# disagreeing at the boundary.
DRAWDOWN_MARGIN_PCT = 0.5


@dataclass(frozen=True)
class EnsembleInputs:
    """The candidates as columns of one matrix, and what each ensemble weights them by."""

    weights: pd.DataFrame  # assets x candidates; each column sums to 1
    stage: StageInputs
    backtest_sharpe: dict[str, float | None]
    tally_composite: dict[str, float]  # Exhibit 9 composite, 0-1
    regime_fit: dict[str, float]  # the six-dimension score's regime-fit dimension
    categories: dict[str, PcCategory]

    @property
    def candidates(self) -> list[str]:
        return list(self.weights.columns)

    @property
    def matrix(self) -> np.ndarray:
        return self.weights.reindex(self.stage.asset_ids).fillna(0.0).to_numpy(dtype=float)


@dataclass
class Ensemble:
    method: EnsembleMethod
    ensemble_weights: dict[str, float]
    final_weights: pd.Series
    profile: RiskProfile
    expected_return_pct: float
    sharpe_ratio: float
    note: str = ""
    # Set when the ensemble breached the IPS and its allocation was projected to the nearest
    # compliant one; this is the profile it had before.
    projected_from: RiskProfile | None = None

    @property
    def policy_adjusted(self) -> bool:
        return self.projected_from is not None

    @property
    def compliant(self) -> bool:
        return self.profile.compliance.compliant and not self.profile.compliance.not_evaluated


def _normalised(raw: dict[str, float]) -> dict[str, float]:
    clean = {k: max(float(v), 0.0) for k, v in raw.items()}
    total = sum(clean.values())
    if total <= 0:
        raise ValueError("ensemble weights are all zero")
    return {k: v / total for k, v in clean.items() if v / total > 1e-9}


def _distances(x: EnsembleInputs) -> dict[str, float]:
    """Each candidate's tracking error to the centroid of all of them."""
    sigma = x.stage.covariance.loc[x.stage.asset_ids, x.stage.asset_ids].to_numpy(dtype=float)
    P = x.matrix
    center = P.mean(axis=1)
    return {
        c: float(np.sqrt(max(float((P[:, i] - center) @ sigma @ (P[:, i] - center)), 0.0)))
        for i, c in enumerate(x.candidates)
    }


# ------------------------------------------------------------------------------- techniques
def simple_average(x: EnsembleInputs) -> dict[str, float]:
    return _normalised(dict.fromkeys(x.candidates, 1.0))


def inverse_tracking_error(x: EnsembleInputs) -> dict[str, float]:
    """§4.4: "assigns higher weight to methods whose portfolios are closer to the ensemble
    centroid" -- the paper's CIO's choice in March 2026."""
    distance = _distances(x)
    floor = max(min(d for d in distance.values() if d > 0), 1e-6) if any(distance.values()) else 1.0
    return _normalised({c: 1.0 / max(d, floor) for c, d in distance.items()})


def backtest_sharpe_weighted(x: EnsembleInputs) -> dict[str, float]:
    """In proportion to each candidate's backtest Sharpe ratio; a negative one gets nothing."""
    return _normalised({c: x.backtest_sharpe.get(c) or 0.0 for c in x.candidates})


def composite_score_weighted(x: EnsembleInputs) -> dict[str, float]:
    """In proportion to the Exhibit 9 composite: the vote blended with the metric score."""
    return _normalised({c: x.tally_composite.get(c, 0.0) for c in x.candidates})


def regime_conditional(x: EnsembleInputs) -> dict[str, float]:
    """In proportion to how each portfolio did in the current regime's past months (the
    regime-fit dimension), so the method weights vary with the macro regime."""
    return _normalised({c: x.regime_fit.get(c, 0.0) for c in x.candidates})


def trimmed_mean(x: EnsembleInputs) -> dict[str, float]:
    """Equal weight after dropping the candidates furthest from the centroid -- "a trimmed mean
    that excludes statistical outliers"."""
    distance = _distances(x)
    drop = max(1, round(TRIM_SHARE * len(distance)))
    kept = sorted(distance, key=lambda c: (distance[c], c))[: len(distance) - drop]
    return _normalised(dict.fromkeys(kept, 1.0))


def single_method(x: EnsembleInputs, eligible: list[str]) -> dict[str, float]:
    """The top-ranked candidate in the vote that the IPS permits on its own."""
    ranked = sorted(eligible, key=lambda c: (-x.tally_composite.get(c, 0.0), c))
    if not ranked:
        raise ValueError("no candidate is IPS-compliant on its own")
    return {ranked[0]: 1.0}


def _monthly_drawdown_pct(returns: np.ndarray) -> float:
    wealth = np.cumprod(1.0 + returns)
    peak = np.maximum.accumulate(wealth)
    return 100 * float((wealth / peak - 1.0).min())


def _ips_terms(x: EnsembleInputs, config: Config):
    """What every IPS-constrained second-level problem needs: a volatility function and a
    builder for the band, tracking-error and drawdown constraints. Decimals, except drawdown."""
    stage = x.stage
    ids = stage.asset_ids
    sigma = stage.covariance.loc[ids, ids].to_numpy(dtype=float)
    bench = stage.benchmark.reindex(ids).fillna(0.0).to_numpy(dtype=float)
    ips = config.ips
    floor = ips.objectives.volatility.min_pct / 100.0
    cap = ips.objectives.volatility.max_pct / 100.0
    te_cap = ips.active_risk.tracking_error.max_ex_ante_pct / 100.0
    dd_limit = ips.objectives.max_drawdown.limit_pct + DRAWDOWN_MARGIN_PCT
    panel = None
    if stage.scenario_returns is not None and not stage.scenario_returns.empty:
        panel = stage.scenario_returns.reindex(columns=ids).dropna(how="any").to_numpy(dtype=float)

    def vol(w):
        return float(np.sqrt(max(float(w @ sigma @ w), 0.0)))

    def constraints(final):
        """IPS constraints on the allocation ``final(z)`` for decision variables ``z``."""
        cons = [
            {"type": "ineq", "fun": lambda z: vol(final(z)) - floor},
            {"type": "ineq", "fun": lambda z: cap - vol(final(z))},
            {"type": "ineq", "fun": lambda z: te_cap - vol(final(z) - bench)},
        ]
        if panel is not None:
            cons.append(
                {
                    "type": "ineq",
                    "fun": lambda z: _monthly_drawdown_pct(panel @ final(z)) - dd_limit,
                }
            )
        return cons

    return vol, constraints


def _solve(objective, starts, n, cons) -> np.ndarray | None:
    """Minimise over long-only weights summing to 1 from several starts; keep the best feasible."""
    best, best_value = None, np.inf
    for start in starts:
        result = minimize(
            objective,
            start,
            method="SLSQP",
            bounds=[(0.0, 1.0)] * n,
            constraints=[{"type": "eq", "fun": lambda z: z.sum() - 1.0}, *cons],
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        z = np.clip(result.x, 0.0, None)
        if z.sum() <= 0:
            continue
        z = z / z.sum()
        if any(c["fun"](z) < -1e-6 for c in cons):
            continue
        value = objective(z)
        if value < best_value:
            best, best_value = z, value
    return best


def project_to_policy(target: pd.Series, x: EnsembleInputs, config: Config) -> pd.Series:
    """The nearest allocation to ``target`` (squared weight distance) that satisfies the IPS's
    volatility band, tracking-error budget and drawdown limit.

    For an ensemble that breaches the IPS by a little -- the averaging ensembles land a point or
    so past the drawdown limit, as the paper's own did -- this keeps its character rather than
    forcing the CIO onto the few concentrated mixes that comply outright. It is decision 37's
    treatment of a candidate, applied once more to the recommendation.
    """
    ids = x.stage.asset_ids
    t = target.reindex(ids).fillna(0.0).to_numpy(dtype=float)
    _, constraints = _ips_terms(x, config)
    bench = x.stage.benchmark.reindex(ids).fillna(0.0).to_numpy(dtype=float)
    starts = [t, 0.5 * t + 0.5 * bench / max(bench.sum(), 1e-12)]
    best = _solve(lambda w: float(((w - t) ** 2).sum()), starts, len(ids), constraints(lambda w: w))
    if best is None:
        raise ValueError("no allocation near this ensemble satisfies the IPS")
    return pd.Series(best, index=ids, dtype="float64")


def meta_optimization(x: EnsembleInputs, config: Config) -> dict[str, float]:
    """The candidate portfolios as assets of a second-level optimisation: the highest ex-ante
    Sharpe ratio over their weighted sums, subject to the IPS's volatility band, tracking-error
    budget and drawdown limit.

    This is where the drawdown limit binds (decisions 32, 37): fitting a *realised* drawdown is
    in-sample, so it is done once, here, on the recommendation, rather than fifteen times on the
    candidates. Inside the optimiser the backtest is approximated by a monthly-rebalanced one,
    which is vectorised; the CRO's quarterly-rebalanced backtest then verifies the result.
    """
    stage = x.stage
    mu = stage.expected_returns.reindex(stage.asset_ids).to_numpy(dtype=float)
    P = x.matrix
    k = P.shape[1]
    vol, constraints = _ips_terms(x, config)

    def neg_sharpe(a):
        w = P @ a
        v = vol(w)
        return -float(w @ mu - stage.risk_free) / v if v > 0 else 0.0

    best = _solve(neg_sharpe, [np.ones(k) / k, *np.eye(k)], k, constraints(lambda a: P @ a))
    if best is None:
        raise ValueError("no mix of the candidates satisfies the IPS's ex-ante and drawdown limits")
    return _normalised(dict(zip(x.candidates, best, strict=True)))


# ------------------------------------------------------------------------------ evaluation
def evaluate(
    method: EnsembleMethod,
    ensemble_weights: dict[str, float],
    x: EnsembleInputs,
    config: Config,
    *,
    note: str = "",
    final_weights: pd.Series | None = None,
    projected_from: RiskProfile | None = None,
) -> Ensemble:
    """The final allocation an ensemble implies, profiled exactly as a candidate is.
    ``final_weights`` overrides the weighted sum, for a policy-projected ensemble."""
    stage = x.stage
    ids = stage.asset_ids
    a = np.array([ensemble_weights.get(c, 0.0) for c in x.candidates])
    final = (
        final_weights.reindex(ids).fillna(0.0)
        if final_weights is not None
        else pd.Series(x.matrix @ a, index=ids, dtype="float64")
    )
    final = final.where(final > 1e-9, 0.0)
    final = final / final.sum()
    sigma = stage.covariance.loc[ids, ids].to_numpy(dtype=float)
    w = final.to_numpy()
    volatility = float(np.sqrt(max(float(w @ sigma @ w), 0.0)))
    expected = float(w @ stage.expected_returns.reindex(ids).to_numpy(dtype=float))
    rf_series = (
        stage.scenario_returns[stage.cash_id]
        if stage.scenario_returns is not None and stage.cash_id in stage.scenario_returns
        else stage.risk_free
    )
    profile = profile_portfolio(
        f"ensemble:{method.value}",
        method.value,
        PcCategory.HEURISTIC,  # unused for an ensemble; the profile needs a family label
        final,
        config=config,
        covariance=stage.covariance,
        benchmark=stage.benchmark,
        inflation_pct=stage.inflation_pct,
        expected_return_pct=100 * expected,
        scenario_returns=stage.scenario_returns,
        risk_free_series=rf_series,
    )
    return Ensemble(
        method=method,
        ensemble_weights=ensemble_weights,
        final_weights=final,
        profile=profile,
        expected_return_pct=100 * expected,
        sharpe_ratio=(expected - stage.risk_free) / volatility if volatility > 0 else float("nan"),
        note=note,
        projected_from=projected_from,
    )


def build_ensembles(
    x: EnsembleInputs, config: Config, *, compliant_candidates: list[str]
) -> tuple[dict[EnsembleMethod, Ensemble], dict[EnsembleMethod, str]]:
    """Every technique, evaluated. A technique that cannot produce weights is reported."""
    techniques = {
        EnsembleMethod.SIMPLE_AVERAGE: lambda: simple_average(x),
        EnsembleMethod.INVERSE_TRACKING_ERROR: lambda: inverse_tracking_error(x),
        EnsembleMethod.BACKTEST_SHARPE_WEIGHTED: lambda: backtest_sharpe_weighted(x),
        EnsembleMethod.META_OPTIMIZATION: lambda: meta_optimization(x, config),
        EnsembleMethod.REGIME_CONDITIONAL: lambda: regime_conditional(x),
        EnsembleMethod.COMPOSITE_SCORE: lambda: composite_score_weighted(x),
        EnsembleMethod.TRIMMED_MEAN: lambda: trimmed_mean(x),
        EnsembleMethod.SINGLE_METHOD: lambda: single_method(x, compliant_candidates),
    }
    ensembles: dict[EnsembleMethod, Ensemble] = {}
    failed: dict[EnsembleMethod, str] = {}
    for method, build in techniques.items():
        try:
            ensemble = evaluate(method, build(), x, config)
        except Exception as exc:
            log.warning("ensemble %s failed (%s)", method.value, exc)
            failed[method] = str(exc)
            continue
        if not ensemble.compliant:
            ensemble = _projected(ensemble, x, config)
        ensembles[method] = ensemble
    return ensembles, failed


def _projected(ensemble: Ensemble, x: EnsembleInputs, config: Config) -> Ensemble:
    """The ensemble projected into the IPS, if a verified compliant projection exists."""
    breaches = (
        ", ".join(v.rule for v in ensemble.profile.compliance.violations if v.severity == "hard")
        or "a rule not evaluated"
    )
    try:
        projected = project_to_policy(ensemble.final_weights, x, config)
    except ValueError as exc:
        ensemble.note = f"breaches {breaches}; no compliant projection ({exc})"
        return ensemble
    adjusted = evaluate(
        ensemble.method,
        ensemble.ensemble_weights,
        x,
        config,
        final_weights=projected,
        projected_from=ensemble.profile,
        note=f"projected into the IPS; it breached {breaches}",
    )
    if adjusted.compliant:
        return adjusted
    ensemble.note = f"breaches {breaches}; its projection did not verify on the backtest"
    return ensemble


def ensemble_score(ensemble: Ensemble, n_assets: int) -> float:
    """What the free run ranks compliant ensembles by: backtest Sharpe and diversification, the
    two of §4.4's six dimensions an ensemble has (the other four describe a method), in the
    paper's own 25:15 ratio. Sharpe uses the method score's scale (0 -> 0, 0.8 -> 1)."""
    sharpe = ensemble.profile.backtest_sharpe
    sharpe_score = 0.0 if sharpe is None else float(np.clip(sharpe / 0.8, 0.0, 1.0))
    diversification = float(np.clip(ensemble.profile.effective_n / n_assets, 0.0, 1.0))
    return (25 * sharpe_score + 15 * diversification) / 40


def default_choice(ensembles: dict[EnsembleMethod, Ensemble], n_assets: int) -> EnsembleMethod:
    """The deterministic choice among compliant ensembles, by ``ensemble_score``."""
    eligible = [e for e in ensembles.values() if e.compliant]
    if not eligible:
        raise ValueError("no ensemble is IPS-compliant; the CIO cannot recommend an allocation")
    return max(eligible, key=lambda e: (ensemble_score(e, n_assets), e.method.value)).method

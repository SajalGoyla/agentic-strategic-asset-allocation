"""Turning weights into a candidate portfolio: metrics, IPS compliance, contract bodies.

The optimisers live in ``methods.py``. This module gathers their inputs from the run, computes
the risk and return statistics every downstream stage needs, and checks the result against the
IPS using ``saa.ips.check_compliance`` -- the same function the CRO and CIO will call, so a
proposal and its later risk report cannot disagree about what the policy says.

**Units.** This is the boundary. ``covariance.json`` stores the matrix in decimal-squared and
the judged CMAs are percent; ``methods.py`` works in decimals throughout. So returns and the
risk-free rate are divided by 100 on the way in, and every statistic is multiplied by 100 on
the way out, because every ``_pct`` field the pipeline writes is percent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from saa.config import Config
from saa.contracts import (
    CovarianceBody,
    InputRef,
    IpsCompliance,
    PcCategory,
    PcProposalBody,
    read,
)
from saa.data.store import DataStore
from saa.ips import PortfolioMetrics, check_compliance
from saa.run import RunContext
from saa.skills.portfolio_construction.methods import (
    METHODS,
    ExAnteLimits,
    Method,
    PortfolioInputs,
    enforce_ex_ante_limits,
)

log = logging.getLogger(__name__)

AGENT = "portfolio-construction"
REPORT = "portfolio_construction.md"


@dataclass(frozen=True)
class PortfolioStats:
    """Ex-ante statistics for one candidate portfolio, in percent except the ratios."""

    expected_return_pct: float
    expected_volatility_pct: float
    sharpe_ratio: float
    effective_n: float
    tracking_error_pct: float | None
    concentration_hhi: float

    def metrics(self, inflation_pct: float | None) -> PortfolioMetrics:
        return PortfolioMetrics(
            expected_return_pct=self.expected_return_pct,
            expected_inflation_pct=inflation_pct,
            expected_volatility_pct=self.expected_volatility_pct,
            ex_ante_tracking_error_pct=self.tracking_error_pct,
        )


def effective_number_of_assets(weights: pd.Series) -> float:
    """Meucci (2009), as reported for the ensemble in §4.4: the exponential of the entropy of
    the weights. 18 equally weighted assets give 18; one asset gives 1."""
    w = weights[weights > 0]
    if w.empty:
        return 0.0
    return float(np.exp(-(w * np.log(w)).sum()))


def portfolio_stats(
    weights: pd.Series,
    covariance: pd.DataFrame,
    expected_returns: pd.Series | None,
    *,
    risk_free: float,
    benchmark: pd.Series | None = None,
) -> PortfolioStats:
    """Ex-ante statistics. Inputs are decimals; the returned statistics are percent."""
    ids = list(weights.index)
    sigma = covariance.loc[ids, ids].to_numpy(dtype=float)
    w = weights.to_numpy(dtype=float)

    variance = float(w @ sigma @ w)
    volatility = float(np.sqrt(max(variance, 0.0)))
    if expected_returns is None:
        expected = float("nan")
        sharpe = float("nan")
    else:
        expected = float(w @ expected_returns.reindex(ids).to_numpy(dtype=float))
        sharpe = (expected - risk_free) / volatility if volatility > 0 else float("nan")

    tracking_error = None
    if benchmark is not None:
        active = w - benchmark.reindex(ids).fillna(0.0).to_numpy(dtype=float)
        tracking_error = 100 * float(np.sqrt(max(float(active @ sigma @ active), 0.0)))

    return PortfolioStats(
        expected_return_pct=100 * expected,
        expected_volatility_pct=100 * volatility,
        sharpe_ratio=sharpe,
        effective_n=effective_number_of_assets(weights),
        tracking_error_pct=tracking_error,
        concentration_hhi=float((w**2).sum()),
    )


# --------------------------------------------------------------------------------- inputs
@dataclass(frozen=True)
class StageInputs:
    """Everything the PC stage reads from the run and the lake."""

    as_of: date
    asset_ids: list[str]
    covariance: pd.DataFrame  # decimal-squared, as covariance.json stores it
    expected_returns: pd.Series  # decimal
    risk_free: float  # decimal
    inflation_pct: float | None  # percent, for the IPS real-return check
    market_weights: pd.Series | None
    benchmark: pd.Series
    regime: str | None
    provenance: dict[str, dict]
    inputs: list[InputRef]
    # Monthly decimal returns over every month all assets share (from 1993-06): the scenarios
    # the non-traditional methods optimise over. None skips those methods, with a reason.
    scenario_returns: pd.DataFrame | None = None
    cash_id: str | None = None
    target_volatility: float = 0.10  # decimal: the IPS volatility band's midpoint


def expected_inflation_pct(store: DataStore, config: Config, as_of: pd.Timestamp) -> float | None:
    """Inflation over the CMA horizon, for the IPS real-return test (decision 38).

    The CMAs are nominal forecasts over `objectives.cma_horizon_years`, so the deflator has to
    be *expected* inflation over that horizon -- which is what the field in `PortfolioMetrics`
    has always been called. A market breakeven rate is the direct observation of it;
    `expected_inflation_series` in the IPS names which one. Trailing realised CPI is the
    fallback, and only the fallback: it is a different quantity, it was 1.3pp away from the
    breakeven on 2026-10-06, and the gap decides compliance.
    """
    objective = config.ips.objectives.return_
    series = objective.expected_inflation_series
    if series:
        breakeven = store.macro(series, as_of=as_of).dropna()
        if len(breakeven):
            return float(breakeven.iloc[-1, 0])
        log.warning(
            "%s has no observation on %s; falling back to trailing %s",
            series,
            as_of.date(),
            objective.inflation_series,
        )
    # Before TIPS breakevens exist (they start in 2003) a backtest has only realised CPI.
    cpi = store.macro(objective.inflation_series, as_of=as_of).dropna()
    if len(cpi) > 12:
        return float(cpi.iloc[-1, 0] / cpi.iloc[-13, 0] - 1) * 100
    return None


def benchmark_weights(config: Config) -> pd.Series:
    """The IPS benchmark, as a weight per asset (zero where it does not hold the asset)."""
    weights = config.ips.active_risk.benchmark.weights
    return pd.Series(
        {a.id: float(weights.get(a.id, 0.0)) for a in config.universe.assets}, dtype="float64"
    )


def gather_inputs(
    run: RunContext,
    store: DataStore,
    *,
    config: Config,
    risk_free_series: str = "DTB3",
) -> StageInputs:
    """Read `pc/covariance.json` and the judged CMAs, plus the market data the methods need."""
    covariance_path = run.path("covariance")
    if not covariance_path.exists():
        raise FileNotFoundError(
            f"{covariance_path} not found; run `uv run saa-skill covariance` first"
        )
    body: CovarianceBody = read("covariance", covariance_path).body
    asset_ids = list(body.asset_ids)
    covariance = pd.DataFrame(body.matrix, index=asset_ids, columns=asset_ids)
    refs = [run.input_ref("covariance", covariance_path)]

    # §3.1 step 4: the PC agents "take the CMAs from step (2) and the covariance matrix from
    # step (3)". Even a method that ignores expected returns when choosing weights still has to
    # report an expected return and a Sharpe ratio, which the CRO and the CIO both read. So the
    # CMAs are a stage input, not an optional extra -- without them there is nothing honest to
    # put in those fields.
    cmas: dict[str, float] = {}
    for asset_id in asset_ids:
        path = run.path("cma", asset_id=asset_id)
        if path.exists():
            cmas[asset_id] = read("cma", path).body.expected_return_pct
            refs.append(run.input_ref("cma", path))
    missing = [a for a in asset_ids if a not in cmas]
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} of {len(asset_ids)} assets have no judged CMA "
            f"({', '.join(missing[:4])}{'...' if len(missing) > 4 else ''}); run "
            "`uv run saa-agent cma-judge --run-id <run>` first"
        )
    # The judge writes percent; the optimisers work in decimals.
    expected_returns = pd.Series(cmas, dtype="float64") / 100.0

    as_of = pd.Timestamp(run.as_of)
    cash_id = next((a.id for a in config.universe.assets if a.group == "cash"), None)

    # The risk-free rate is the cash asset's own CMA, not today's T-bill rate (decision 38).
    # Cash *is* the risk-free asset in this universe, and every Sharpe ratio here is over the
    # CMA horizon, so a spot 3-month yield is the wrong number and -- being a different number
    # from cash's own forecast -- gave cash a negative Sharpe ratio while every risk-based
    # method was piling into it. `risk_free_series` remains the fallback.
    if cash_id is not None and cash_id in cmas:
        risk_free = cmas[cash_id] / 100.0
    else:
        rates = store.macro(risk_free_series, as_of=as_of).dropna()
        risk_free = (float(rates.iloc[-1, 0]) if len(rates) else 0.0) / 100.0

    inflation_pct = expected_inflation_pct(store, config, as_of)

    market_weights = _market_weights(store, asset_ids, as_of)
    scenarios = store.asset_returns(asset_ids, as_of=as_of).dropna(how="any")

    regime = None
    macro_path = run.path("macro_view")
    if macro_path.exists():
        regime = read("macro_view", macro_path).body.judgment.regime.value
        refs.append(run.input_ref("macro_view", macro_path))

    return StageInputs(
        as_of=run.as_of,
        asset_ids=asset_ids,
        covariance=covariance,
        expected_returns=expected_returns,
        risk_free=risk_free,
        inflation_pct=inflation_pct,
        market_weights=market_weights,
        benchmark=benchmark_weights(config),
        regime=regime,
        provenance=store.provenance(),
        inputs=refs,
        scenario_returns=scenarios if len(scenarios) else None,
        cash_id=cash_id,
        target_volatility=(
            config.ips.objectives.volatility.min_pct + config.ips.objectives.volatility.max_pct
        )
        / 200.0,
    )


def _market_weights(
    store: DataStore, asset_ids: list[str], as_of: pd.Timestamp
) -> pd.Series | None:
    """ETF market values as the proxy for the market portfolio, for Black-Litterman.

    Two sources, the more recent one on ``as_of`` wins -- the same rule as the CMA methods'
    Black-Litterman candidate (decision 22): CRSP's monthly market values (licensed, history to
    2010, a date x ticker frame) and the fund snapshot's AUM (public, only the days it was
    taken, indexed by ticker).
    """
    tickers = {store.universe.get(a).ticker: a for a in asset_ids}
    candidates: list[tuple[pd.Timestamp, pd.Series]] = []
    try:
        caps = store.etf_market_caps(as_of=as_of)
    except FileNotFoundError:
        caps = pd.DataFrame()
    if not caps.empty and set(tickers) <= set(caps.columns):
        complete = caps[list(tickers)].dropna()
        complete = complete[(complete > 0).all(axis=1)]
        if not complete.empty:
            row = complete.iloc[-1].rename(index=tickers)
            candidates.append((pd.Timestamp(complete.index[-1]), row))
    try:
        snapshot = store.fund_snapshot(list(tickers), as_of=as_of)
    except FileNotFoundError:
        snapshot = pd.DataFrame()
    if not snapshot.empty and set(tickers) <= set(snapshot.index):
        aum = snapshot.loc[list(tickers), "total_assets"]
        if aum.notna().all() and (aum > 0).all():
            when = pd.Timestamp(snapshot.loc[list(tickers), "snapshot_date"].min())
            candidates.append((when, aum.rename(index=tickers)))
    if not candidates:
        log.warning("no ETF market values available; Black-Litterman will be skipped")
        return None
    _, values = max(candidates, key=lambda c: c[0])
    return values.astype("float64").reindex(asset_ids)


# -------------------------------------------------------------------------------- proposal
@dataclass
class Candidate:
    """One method's portfolio, before the agent writes its rationale."""

    method: Method
    weights: pd.Series
    stats: PortfolioStats
    compliance: IpsCompliance
    # Set when the agent is not named after its method: the PC-researcher runs whichever
    # library method it proposed, under its own id.
    agent: str | None = None
    # The volatility the method produced before the IPS band was imposed, in percent; None when
    # the method reached the band on its own and nothing was changed (decision 37).
    unconstrained_volatility_pct: float | None = None

    @property
    def agent_id(self) -> str:
        return self.agent or self.method.id

    @property
    def policy_adjusted(self) -> bool:
        return self.unconstrained_volatility_pct is not None

    def body(self, rationale: str, *, notes: str | None = None) -> PcProposalBody:
        return PcProposalBody(
            agent_id=self.agent_id,
            method=self.method.name,
            category=PcCategory(self.method.category),
            weights={k: float(v) for k, v in self.weights.items() if v > 0},
            expected_return_pct=self.stats.expected_return_pct,
            expected_volatility_pct=self.stats.expected_volatility_pct,
            sharpe_ratio=self.stats.sharpe_ratio,
            effective_n=self.stats.effective_n,
            ex_ante_tracking_error_pct=self.stats.tracking_error_pct,
            ips_compliance=self.compliance,
            rationale=rationale,
            notes=notes,
            policy_adjusted=self.policy_adjusted,
            unconstrained_volatility_pct=self.unconstrained_volatility_pct,
        )


def portfolio_inputs(stage: StageInputs) -> PortfolioInputs:
    return PortfolioInputs(
        asset_ids=stage.asset_ids,
        covariance=stage.covariance,
        expected_returns=stage.expected_returns,
        risk_free=stage.risk_free,
        market_weights=stage.market_weights,
        scenarios=stage.scenario_returns,
        cash_id=stage.cash_id,
        target_volatility=stage.target_volatility,
    )


def build_candidate(
    method: Method,
    stage: StageInputs,
    config: Config,
    *,
    build=None,
    objective=None,
    agent: str | None = None,
) -> Candidate:
    """Run one method, impose the IPS volatility band, and work out everything about the result.

    ``build`` overrides ``method.build`` when the method needs more than the stage inputs --
    the adversarial diversifier needs the centroid of the other proposals -- and ``objective``
    overrides ``method.objective`` for the same reason.

    The band is imposed here rather than inside each method because it is *policy*, not a
    property of the method (decision 37): §3.1 makes the IPS the governing document every agent
    reads, and a method left below the volatility floor cannot be peer-reviewed or voted on as a
    real candidate. A method already inside the band is returned untouched.
    """
    inputs = portfolio_inputs(stage)
    weights = (build or method.build)(inputs)  # type: ignore[operator]
    band = config.ips.objectives.volatility
    limits = ex_ante_limits(stage, config)
    weights, unconstrained = enforce_ex_ante_limits(
        weights,
        inputs,
        limits,
        objective=objective or method.objective,
        constraints=(method.band_constraints(inputs, limits) if method.band_constraints else ()),
    )
    if unconstrained is not None:
        log.info(
            "%s: %.2f%% volatility outside the %.1f-%.1f%% IPS band; re-solved inside it at %.2f%%",
            method.id,
            unconstrained,
            band.min_pct,
            band.max_pct,
            100 * float(np.sqrt(weights.to_numpy() @ inputs.sigma @ weights.to_numpy())),
        )
    return candidate_from_weights(
        method, weights, stage, config, agent=agent, unconstrained_volatility_pct=unconstrained
    )


def ex_ante_limits(stage: StageInputs, config: Config) -> ExAnteLimits:
    """The IPS limits imposed on every candidate (decision 37), in decimals."""
    band = config.ips.objectives.volatility
    return ExAnteLimits(
        floor=band.min_pct / 100.0,
        cap=band.max_pct / 100.0,
        benchmark=stage.benchmark,
        tracking_error_cap=config.ips.active_risk.tracking_error.max_ex_ante_pct / 100.0,
    )


def candidate_from_weights(
    method: Method,
    weights: pd.Series,
    stage: StageInputs,
    config: Config,
    *,
    agent: str | None = None,
    unconstrained_volatility_pct: float | None = None,
) -> Candidate:
    """Everything about a portfolio once its weights are fixed: statistics and IPS compliance.

    Shared by ``build_candidate`` and the revision step, so a revised proposal is measured and
    checked exactly as its original was.
    """
    stats = portfolio_stats(
        weights,
        stage.covariance,
        stage.expected_returns,
        risk_free=stage.risk_free,
        benchmark=stage.benchmark,
    )
    report = check_compliance(
        {k: float(v) for k, v in weights.items()},
        stats.metrics(stage.inflation_pct),
        config.ips,
        config.universe,
    )
    return Candidate(
        method=method,
        weights=weights,
        stats=stats,
        compliance=IpsCompliance.from_report(report),
        agent=agent,
        unconstrained_volatility_pct=unconstrained_volatility_pct,
    )


def build_candidates(
    stage: StageInputs, config: Config, *, method_ids: list[str] | None = None
) -> tuple[dict[str, Candidate], dict[str, str]]:
    """Run every requested method. A method that cannot run is reported, not silently dropped."""
    ids = method_ids or list(METHODS)
    candidates: dict[str, Candidate] = {}
    skipped: dict[str, str] = {}

    for method_id in ids:
        method = METHODS.get(method_id)
        if method is None:
            skipped[method_id] = f"unknown method; known: {sorted(METHODS)}"
            continue
        if method.uses_cmas and stage.expected_returns is None:
            skipped[method_id] = "needs judged CMAs for every asset; run the CMA judge first"
            continue
        if method.needs_scenarios and stage.scenario_returns is None:
            skipped[method_id] = "needs historical return scenarios; none in the lake"
            continue
        try:
            candidates[method_id] = build_candidate(method, stage, config)
        except Exception as exc:
            log.warning("portfolio construction: %s skipped (%s)", method_id, exc)
            skipped[method_id] = str(exc)
    return candidates, skipped


def render_report(
    candidates: dict[str, Candidate], skipped: dict[str, str], stage: StageInputs
) -> str:
    lines = [
        "# Portfolio Construction",
        "",
        f"As of {stage.as_of}" + (f", regime **{stage.regime}**" if stage.regime else ""),
        "",
        "| method | category | return % | vol % | Sharpe | eff. N | TE % | IPS |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for candidate in candidates.values():
        s = candidate.stats
        te = "–" if s.tracking_error_pct is None else f"{s.tracking_error_pct:.2f}"
        ips = "pass" if candidate.compliance.compliant else "FAIL"
        lines.append(
            f"| {candidate.method.name} | {candidate.method.category} | "
            f"{s.expected_return_pct:.2f} | {s.expected_volatility_pct:.2f} | "
            f"{s.sharpe_ratio:.2f} | {s.effective_n:.1f} | {te} | {ips} |"
        )
    if skipped:
        lines += ["", "## Skipped", ""]
        lines += [f"- **{k}**: {v}" for k, v in skipped.items()]

    lines += ["", "## Weights", "", "| asset | " + " | ".join(candidates) + " |"]
    lines.append("|---" * (len(candidates) + 1) + "|")
    for asset_id in stage.asset_ids:
        cells = [f"{c.weights.get(asset_id, 0.0):.1%}" for c in candidates.values()]
        lines.append(f"| {asset_id} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_report(
    candidates: dict[str, Candidate], skipped: dict[str, str], stage: StageInputs, run: RunContext
) -> Path:
    return run.write_report(render_report(candidates, skipped, stage), REPORT)

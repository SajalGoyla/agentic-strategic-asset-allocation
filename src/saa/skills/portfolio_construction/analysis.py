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
from saa.skills.portfolio_construction.methods import METHODS, Method, PortfolioInputs

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
    rates = store.macro(risk_free_series, as_of=as_of).dropna()
    risk_free = (float(rates.iloc[-1, 0]) if len(rates) else 0.0) / 100.0

    inflation_pct = None
    inflation_series = config.ips.objectives.return_.inflation_series
    cpi = store.macro(inflation_series, as_of=as_of).dropna()
    if len(cpi) > 12:
        inflation_pct = float(cpi.iloc[-1, 0] / cpi.iloc[-13, 0] - 1) * 100

    market_weights = _market_weights(store, asset_ids, as_of)

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
    )


def _market_weights(
    store: DataStore, asset_ids: list[str], as_of: pd.Timestamp
) -> pd.Series | None:
    """ETF market values as the proxy for the market portfolio, for Black-Litterman."""
    for loader in (store.etf_market_caps, store.fund_snapshot):
        try:
            frame = loader(as_of=as_of)
        except (FileNotFoundError, KeyError, AttributeError):
            continue
        if frame is None or frame.empty:
            continue
        column = next(
            (c for c in ("market_value", "total_assets", "market_cap") if c in frame.columns),
            None,
        )
        if column is None:
            continue
        tickers = {store.universe.get(a).ticker: a for a in asset_ids}
        values = {}
        for ticker, asset_id in tickers.items():
            if ticker in frame.index:
                value = frame.loc[ticker, column]
                if pd.notna(value) and float(value) > 0:
                    values[asset_id] = float(value)
        if len(values) >= len(asset_ids) // 2:
            return pd.Series(values, dtype="float64").reindex(asset_ids).fillna(0.0)
    log.warning("no ETF market values available; Black-Litterman will be skipped")
    return None


# -------------------------------------------------------------------------------- proposal
@dataclass
class Candidate:
    """One method's portfolio, before the agent writes its rationale."""

    method: Method
    weights: pd.Series
    stats: PortfolioStats
    compliance: IpsCompliance

    @property
    def agent_id(self) -> str:
        return self.method.id

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
        )


def build_candidate(method: Method, stage: StageInputs, config: Config) -> Candidate:
    """Run one method and work out everything about the portfolio it produced."""
    inputs = PortfolioInputs(
        asset_ids=stage.asset_ids,
        covariance=stage.covariance,
        expected_returns=stage.expected_returns,
        risk_free=stage.risk_free,
        market_weights=stage.market_weights,
    )
    weights = method.build(inputs)  # type: ignore[operator]
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

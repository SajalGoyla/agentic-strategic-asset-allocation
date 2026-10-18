"""Risk analytics for one candidate portfolio: the deterministic half of the CRO agent.

Ang, Azimbayev & Kim (2026) §3.5 lists what the report has to cover -- "ex-ante and back-test
volatility, value-at-risk, maximum drawdown, concentration metrics, factor tilts, and IPS
compliance" -- and this module computes all of it, plus the composite ``risk_score`` the CIO
later blends with the vote.

Three things worth knowing before reading the code:

* **The ex-ante and the backtest numbers come from different places and can disagree.** Ex-ante
  volatility is the weights against the covariance matrix the PC agents optimised over; the
  backtest holds the same weights through history and rebalances them on the IPS cadence. A
  large gap between the two is itself a finding, which is why both are reported rather than
  reconciled.
* **The score is computed, not judged.** Each component measures the portfolio against the
  limit the IPS actually sets, so a score is comparable across candidates and reproducible from
  the run inputs (decision 34). A component with no data is dropped and the rest renormalise,
  the same rule the signals composite uses -- a missing backtest must not read as low risk.
* **Units.** Weights, returns and the covariance matrix arrive in decimals, as the PC stage
  holds them; every figure this module returns is percent, except the ratios and the scores.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from saa.config import Config
from saa.contracts import IpsCompliance, PcCategory
from saa.ips import IPS, PortfolioMetrics, check_compliance
from saa.skills.historical_analysis.metrics import (
    MONTHS_PER_YEAR,
    annualized_volatility,
    conditional_value_at_risk,
    max_drawdown,
    value_at_risk,
)
from saa.skills.portfolio_construction import effective_number_of_assets

log = logging.getLogger(__name__)

SKILL = "risk"

# §3.5's report is a point-in-time risk assessment, so the backtest holds the proposed weights
# and rebalances them on the IPS cadence rather than re-optimising. Quarterly, per the IPS.
REBALANCE_MONTHS = 3
# Below this there is no distribution to speak of: VaR and drawdown would be noise.
MIN_BACKTEST_MONTHS = 36

# The composite risk score. Weights are here rather than in a config file because they are a
# definition of "riskier", not a tunable: changing them changes what the CRO means.
RISK_SCORE_WEIGHTS = {
    "volatility": 0.30,
    "drawdown": 0.25,
    "tail": 0.15,
    "tracking_error": 0.15,
    "concentration": 0.15,
}
# The 95% normal quantile, for scaling monthly VaR against the IPS volatility ceiling.
_Z95 = 1.6448536269514722


@dataclass(frozen=True)
class RiskProfile:
    """Everything the CRO reports about one portfolio, in percent except the ratios."""

    agent_id: str
    method: str
    category: PcCategory

    ex_ante_volatility_pct: float
    ex_ante_tracking_error_pct: float | None
    backtest_volatility_pct: float | None
    backtest_sharpe: float | None
    var_95_pct: float | None
    cvar_95_pct: float | None
    max_drawdown_pct: float | None
    backtest_months: int | None

    effective_n: float
    concentration_hhi: float
    factor_tilts: dict[str, float]

    compliance: IpsCompliance
    risk_score: float
    risk_score_components: dict[str, float] = field(default_factory=dict)

    @property
    def has_backtest(self) -> bool:
        return self.backtest_months is not None


# --------------------------------------------------------------------------------- backtest
def backtest_returns(
    weights: pd.Series, returns: pd.DataFrame, *, rebalance_months: int = REBALANCE_MONTHS
) -> pd.Series:
    """Monthly returns of a fixed-weight portfolio, rebalanced every ``rebalance_months``.

    Between rebalances the weights drift with the assets, which is what a quarterly-rebalanced
    portfolio actually holds. ``rebalance_months=0`` never rebalances (buy and hold).
    """
    if returns.empty:
        return pd.Series(dtype="float64")
    target = weights.reindex(returns.columns).fillna(0.0).to_numpy(dtype=float)
    if target.sum() <= 0:
        raise ValueError("portfolio has no weight on any asset in the return panel")
    target = target / target.sum()

    held = target.copy()
    out: list[float] = []
    for i, (_, row) in enumerate(returns.iterrows()):
        r = row.to_numpy(dtype=float)
        out.append(float(held @ r))
        grown = held * (1.0 + r)
        total = grown.sum()
        held = grown / total if total > 0 else target.copy()
        if rebalance_months and (i + 1) % rebalance_months == 0:
            held = target.copy()
    return pd.Series(out, index=returns.index, dtype="float64")


@dataclass(frozen=True)
class BacktestStats:
    """Realised statistics of a held portfolio. Percent, except the ratio."""

    months: int
    volatility_pct: float
    sharpe: float | None
    var_95_pct: float
    cvar_95_pct: float
    max_drawdown_pct: float
    beta: float | None


def backtest_stats(
    portfolio: pd.Series, *, risk_free: pd.Series | float = 0.0, benchmark: pd.Series | None = None
) -> BacktestStats | None:
    """Realised risk of a monthly return series, or None when there is too little of it."""
    series = portfolio.dropna()
    if len(series) < MIN_BACKTEST_MONTHS:
        return None

    if isinstance(risk_free, pd.Series):
        rf = risk_free.reindex(series.index).fillna(0.0)
    else:
        rf = pd.Series(float(risk_free) / MONTHS_PER_YEAR, index=series.index)
    excess = series - rf
    volatility = annualized_volatility(excess)
    sharpe = (
        float(excess.mean() * MONTHS_PER_YEAR / volatility)
        if volatility and not math.isnan(volatility) and volatility > 0
        else None
    )

    beta = None
    if benchmark is not None:
        both = pd.concat([series, benchmark], axis=1, keys=["p", "b"]).dropna()
        if len(both) >= MIN_BACKTEST_MONTHS and both["b"].var(ddof=1) > 0:
            beta = float(both["p"].cov(both["b"]) / both["b"].var(ddof=1))

    return BacktestStats(
        months=len(series),
        volatility_pct=100 * annualized_volatility(series),
        sharpe=sharpe,
        var_95_pct=100 * value_at_risk(series),
        cvar_95_pct=100 * conditional_value_at_risk(series),
        max_drawdown_pct=100 * max_drawdown(series).depth,
        beta=beta,
    )


# ---------------------------------------------------------------------------- factor tilts
def factor_tilts(
    weights: pd.Series, benchmark: pd.Series, config: Config, *, beta: float | None = None
) -> dict[str, float]:
    """Active exposure by asset-class group, plus realised beta to the IPS benchmark.

    The paper reports "factor tilts" without defining them, and the universe is asset classes
    rather than factor sleeves, so the honest reading is exposure against the benchmark: how
    much more equity, duration or real-asset risk this portfolio carries than the 60/40 it is
    measured against. Values are decimals of portfolio weight and sum to zero by construction;
    ``benchmark_beta`` is a ratio and is omitted when there is no backtest.
    """
    groups = {asset.id: asset.group for asset in config.universe.assets}
    tilts: dict[str, float] = {}
    for group in sorted(set(groups.values())):
        members = [a for a, g in groups.items() if g == group]
        held = float(weights.reindex(members).fillna(0.0).sum())
        bench = float(benchmark.reindex(members).fillna(0.0).sum())
        tilts[f"active_{group}"] = held - bench
    if beta is not None:
        tilts["benchmark_beta"] = beta
    return tilts


# ----------------------------------------------------------------------------- risk score
def _unit(value: float) -> float:
    return float(min(1.0, max(0.0, value)))


def risk_score(
    ips: IPS,
    *,
    ex_ante_volatility_pct: float,
    max_drawdown_pct: float | None,
    var_95_pct: float | None,
    tracking_error_pct: float | None,
    concentration_hhi: float,
    n_assets: int,
) -> tuple[float, dict[str, float]]:
    """Composite risk score in [0, 1], higher is riskier, with its components.

    Every component is the portfolio measured against the limit the IPS sets, so a score of 1
    means "at or past every limit the policy states" rather than an abstract maximum. A
    portfolio *below* the volatility floor scores 0 on that component: it is non-compliant, but
    it is not risky, and conflating the two would let the CIO read a cash-heavy portfolio as
    dangerous.

    A component with no input is dropped and the remaining weights renormalise, so a candidate
    with no backtest is scored on what it has rather than credited with zero risk.
    """
    band = ips.objectives.volatility
    components: dict[str, float] = {
        "volatility": _unit(
            (ex_ante_volatility_pct - band.min_pct) / max(band.max_pct - band.min_pct, 1e-9)
        ),
        "concentration": _unit(
            (concentration_hhi - 1.0 / n_assets) / max(1.0 - 1.0 / n_assets, 1e-9)
        ),
    }
    if max_drawdown_pct is not None:
        limit = abs(ips.objectives.max_drawdown.limit_pct)
        components["drawdown"] = _unit(abs(max_drawdown_pct) / max(limit, 1e-9))
    if var_95_pct is not None:
        # The monthly VaR a portfolio sitting exactly at the IPS ceiling would show if its
        # returns were normal. Scaling to the policy keeps the component comparable with the
        # others rather than fixing an arbitrary loss threshold.
        reference = _Z95 * band.max_pct / math.sqrt(MONTHS_PER_YEAR)
        components["tail"] = _unit(var_95_pct / max(reference, 1e-9))
    if tracking_error_pct is not None:
        budget = ips.active_risk.tracking_error.max_ex_ante_pct
        components["tracking_error"] = _unit(tracking_error_pct / max(budget, 1e-9))

    total_weight = sum(RISK_SCORE_WEIGHTS[name] for name in components)
    score = (
        sum(RISK_SCORE_WEIGHTS[name] * value for name, value in components.items()) / total_weight
        if total_weight > 0
        else 0.0
    )
    return _unit(score), components


# -------------------------------------------------------------------------------- profile
def profile_portfolio(
    agent_id: str,
    method: str,
    category: PcCategory,
    weights: pd.Series,
    *,
    config: Config,
    covariance: pd.DataFrame,
    benchmark: pd.Series,
    inflation_pct: float | None = None,
    expected_return_pct: float | None = None,
    scenario_returns: pd.DataFrame | None = None,
    risk_free_series: pd.Series | float = 0.0,
    rebalance_months: int = REBALANCE_MONTHS,
) -> RiskProfile:
    """The whole report for one portfolio: ex-ante risk, realised risk, concentration, IPS.

    ``weights`` and ``covariance`` are decimals. ``scenario_returns`` is the monthly return
    panel the PC stage already reads; without it the backtest figures are None and the risk
    score is computed from what remains.
    """
    asset_ids = list(covariance.index)
    w = weights.reindex(asset_ids).fillna(0.0)
    sigma = covariance.loc[asset_ids, asset_ids].to_numpy(dtype=float)
    vector = w.to_numpy(dtype=float)

    ex_ante_volatility_pct = 100 * float(np.sqrt(max(float(vector @ sigma @ vector), 0.0)))
    active = vector - benchmark.reindex(asset_ids).fillna(0.0).to_numpy(dtype=float)
    tracking_error_pct = 100 * float(np.sqrt(max(float(active @ sigma @ active), 0.0)))

    stats = None
    if scenario_returns is not None and not scenario_returns.empty:
        panel = scenario_returns.reindex(columns=asset_ids).dropna(how="any")
        if not panel.empty:
            bench_series = backtest_returns(benchmark, panel, rebalance_months=rebalance_months)
            stats = backtest_stats(
                backtest_returns(w, panel, rebalance_months=rebalance_months),
                risk_free=risk_free_series,
                benchmark=bench_series,
            )

    hhi = float((vector**2).sum())
    score, components = risk_score(
        config.ips,
        ex_ante_volatility_pct=ex_ante_volatility_pct,
        max_drawdown_pct=stats.max_drawdown_pct if stats else None,
        var_95_pct=stats.var_95_pct if stats else None,
        tracking_error_pct=tracking_error_pct,
        concentration_hhi=hhi,
        n_assets=len(asset_ids),
    )

    # The CRO checks the same rules the proposal did, now with the realised drawdown the PC
    # stage could not supply -- which is the one hard limit a candidate cannot be judged on
    # before its portfolio has been held through history.
    report = check_compliance(
        {k: float(v) for k, v in w.items()},
        PortfolioMetrics(
            expected_return_pct=expected_return_pct,
            expected_inflation_pct=inflation_pct,
            expected_volatility_pct=ex_ante_volatility_pct,
            max_drawdown_pct=stats.max_drawdown_pct if stats else None,
            ex_ante_tracking_error_pct=tracking_error_pct,
        ),
        config.ips,
        config.universe,
    )

    return RiskProfile(
        agent_id=agent_id,
        method=method,
        category=category,
        ex_ante_volatility_pct=ex_ante_volatility_pct,
        ex_ante_tracking_error_pct=tracking_error_pct,
        backtest_volatility_pct=stats.volatility_pct if stats else None,
        backtest_sharpe=stats.sharpe if stats else None,
        var_95_pct=stats.var_95_pct if stats else None,
        cvar_95_pct=stats.cvar_95_pct if stats else None,
        max_drawdown_pct=stats.max_drawdown_pct if stats else None,
        backtest_months=stats.months if stats else None,
        effective_n=effective_number_of_assets(w[w > 0]),
        concentration_hhi=hhi,
        factor_tilts=factor_tilts(w, benchmark, config, beta=stats.beta if stats else None),
        compliance=IpsCompliance.from_report(report),
        risk_score=score,
        risk_score_components=components,
    )

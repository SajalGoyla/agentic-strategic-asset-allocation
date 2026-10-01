"""Asset-level signals: the other deterministic input to the CMA judge.

Ang, Azimbayev & Kim (2026) Exhibit 3 steps 3-5; Exhibit 4 lists ``signals.json`` among the
judge's inputs as "asset-level macro, technical, valuation signals". No LLM is involved here.

Every signal is scored to [-1, +1] where **+1 is bullish for that asset's forward return**,
against the signal's own trailing history. Reading the sign consistently matters more than any
individual definition: a high earnings yield is cheap and therefore bullish, a wide credit
spread compensates more and is therefore bullish, and a stretched three-year return enters
negatively because it mean-reverts.

A signal with too little history is omitted rather than defaulted, and the category composite
renormalises over whatever is present -- the same rule the macro skill uses for a thin
dimension.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from saa.contracts import InputRef, Producer, Signal, SignalCategory, SignalsBody
from saa.contracts.asset_class import SIGNALS_CONTRACT
from saa.data.store import DataStore
from saa.run import RunContext
from saa.skills.signals.settings import SignalSettings, load_signal_settings

log = logging.getLogger(__name__)

AGENT = "signals"
REPORT = "signals.md"

# Shared with the macro skill: z-score against the signal's own history, then squash. tanh
# keeps an extreme reading influential without letting it own the category.
SQUASH = 2.0


def score_against_history(
    series: pd.Series, *, lookback_years: int, min_months: int
) -> float | None:
    """Latest value of ``series`` as a score in [-1, +1] against its own trailing history."""
    series = series.dropna()
    if len(series) < min_months:
        return None
    window = series.iloc[-(lookback_years * 12) :]
    mean, std = window.mean(), window.std()
    if not np.isfinite(std) or std == 0:
        return None
    return float(np.clip(np.tanh((series.iloc[-1] - mean) / std / SQUASH), -1.0, 1.0))


def _history_of(series: pd.Series, fn, window: int) -> pd.Series:
    """Roll ``fn`` over ``series`` so a signal can be scored against its own past values."""
    return series.rolling(window, min_periods=window).apply(fn, raw=True)


@dataclass
class AssetSignals:
    asset_id: str
    signals: list[Signal] = field(default_factory=list)

    def add(
        self,
        name: str,
        category: SignalCategory,
        score: float | None,
        rationale: str,
        *,
        value: float | None = None,
        source: str | None = None,
    ) -> None:
        if score is None:
            return
        self.signals.append(
            Signal(
                name=name,
                category=category,
                value=None if value is None or not np.isfinite(value) else float(value),
                score=float(np.clip(score, -1.0, 1.0)),
                rationale=rationale,
                source=source,
            )
        )


@dataclass(frozen=True)
class SignalsResult:
    as_of: date
    bodies: dict[str, SignalsBody]
    regime: str | None
    provenance: dict[str, dict]
    inputs: list[InputRef]


# ------------------------------------------------------------------------------- technical
def _technical(
    asset_id: str,
    returns: pd.Series,
    universe_momentum: pd.Series,
    settings: SignalSettings,
    out: AssetSignals,
) -> None:
    cfg = settings.technical
    kw = {"lookback_years": settings.lookback_years, "min_months": settings.min_months}
    growth = (1 + returns / 100).cumprod()

    mom = cfg.momentum
    span = mom.lookback_months - mom.skip_months
    if len(returns) > mom.lookback_months:
        skipped = growth.shift(mom.skip_months)
        momentum = (skipped / skipped.shift(span) - 1) * 100
        out.add(
            "momentum_12_1",
            SignalCategory.TECHNICAL,
            score_against_history(momentum, **kw),
            f"{span}-month return skipping the last {mom.skip_months}, vs. its own history",
            value=momentum.iloc[-1] if momentum.notna().any() else None,
            source="market/asset_returns_monthly",
        )

    window = cfg.trend.window_months
    if len(growth) > window:
        gap = (growth / growth.rolling(window).mean() - 1) * 100
        out.add(
            "trend",
            SignalCategory.TECHNICAL,
            score_against_history(gap, **kw),
            f"price against its {window}-month moving average",
            value=gap.iloc[-1] if gap.notna().any() else None,
            source="market/asset_returns_monthly",
        )

    lookback = cfg.mean_reversion.lookback_months
    if len(growth) > lookback:
        trailing = (growth / growth.shift(lookback) - 1) * 100
        score = score_against_history(trailing, **kw)
        out.add(
            "mean_reversion",
            SignalCategory.TECHNICAL,
            None if score is None else -score,
            f"{lookback}-month return, inverted: a stretched run tends to revert",
            value=trailing.iloc[-1] if trailing.notna().any() else None,
            source="market/asset_returns_monthly",
        )

    if asset_id in universe_momentum.index and len(universe_momentum) > 2:
        rank = universe_momentum.rank(pct=True)[asset_id]
        out.add(
            "relative_momentum",
            SignalCategory.TECHNICAL,
            rank * 2 - 1,
            "momentum rank against the other 17 asset classes",
            value=float(universe_momentum[asset_id]),
            source="market/asset_returns_monthly",
        )


# ------------------------------------------------------------------------------ valuation
def _valuation(
    asset_id: str,
    group: str,
    settings: SignalSettings,
    store: DataStore,
    as_of: pd.Timestamp,
    macro: pd.DataFrame,
    out: AssetSignals,
) -> None:
    kw = {"lookback_years": settings.lookback_years, "min_months": settings.min_months}

    if asset_id == "us_large_cap":
        try:
            shiller = store.shiller(as_of=as_of)
        except (FileNotFoundError, KeyError):
            shiller = pd.DataFrame()
        if "cape" in shiller and shiller["cape"].notna().any():
            cape = shiller["cape"].dropna()
            score = score_against_history(cape, **kw)
            out.add(
                "cape",
                SignalCategory.VALUATION,
                None if score is None else -score,
                "Shiller CAPE, inverted: expensive is bearish for forward return",
                value=float(cape.iloc[-1]),
                source="valuation/shiller_us_equity",
            )
            # No separate earnings-yield signal here: 1/CAPE is the same number, and emitting
            # both would weight one piece of evidence twice.
    elif group in {"equity", "real_assets"}:
        _snapshot_earnings_yield(asset_id, store, as_of, out)

    for signal_name, mapping, rationale, sign in (
        (
            "yield_level",
            settings.yield_levels,
            "starting yield against its own history: the dominant predictor of bond return",
            +1,
        ),
        (
            "credit_spread",
            settings.credit_spreads,
            "credit spread against its own history: wide compensates more",
            +1,
        ),
    ):
        series_id = mapping.get(asset_id)
        if series_id is None or series_id not in macro.columns:
            continue
        series = macro[series_id].dropna()
        score = score_against_history(series, **kw)
        out.add(
            signal_name,
            SignalCategory.VALUATION,
            None if score is None else sign * score,
            f"{series_id}: {rationale}",
            value=float(series.iloc[-1]) if len(series) else None,
            source="macro/fred_observations",
        )


def _snapshot_earnings_yield(
    asset_id: str, store: DataStore, as_of: pd.Timestamp, out: AssetSignals
) -> None:
    """ETF earnings yield, for equity and real-asset classes outside US Large Cap.

    `market/fund_snapshot` only accumulates from the first ingest, so in practice there is not
    yet enough history to say whether today's reading is cheap or expensive. A signal scored
    0.0 is not neutral evidence -- it would pull the valuation category toward zero and take
    weight from the signals that do carry information -- so nothing is emitted until the
    snapshot has `min_months` of history. The judge still sees these valuations through
    `cma_methods.json`, where `inverse_gordon` and `implied_erp_cape` use them directly.
    """
    asset = store.universe.get(asset_id)
    try:
        snapshot = store.fund_snapshot(asset.ticker, as_of=as_of)
    except (FileNotFoundError, KeyError):
        return
    if snapshot.empty or asset.ticker not in snapshot.index:
        return
    log.debug("signals: %s earnings yield has too little snapshot history to score", asset_id)


# ---------------------------------------------------------------------------------- macro
def _macro(
    asset_id: str,
    returns: pd.Series,
    regime_labels: pd.Series | None,
    regime: str | None,
    dimension_scores: pd.DataFrame | None,
    settings: SignalSettings,
    out: AssetSignals,
) -> None:
    cfg = settings.macro

    if regime_labels is not None and regime is not None:
        aligned = returns.reindex(regime_labels.index).dropna()
        labels = regime_labels.reindex(aligned.index)
        in_regime = aligned[labels == regime]
        if len(in_regime) >= cfg.regime_fit.min_months and aligned.std() > 0:
            # How far this regime's mean monthly return sits from the asset's unconditional
            # mean, in units of its own monthly volatility.
            edge = (in_regime.mean() - aligned.mean()) / aligned.std()
            out.add(
                "regime_fit",
                SignalCategory.MACRO,
                float(np.tanh(edge * 2)),
                f"mean return in {len(in_regime)} past '{regime}' months vs. its "
                "unconditional mean",
                value=float(in_regime.mean() - aligned.mean()),
                source="macro/regime_history",
            )

    if dimension_scores is None or dimension_scores.empty:
        return
    window = cfg.dimension_alignment.window_months
    for dimension in cfg.dimension_alignment.dimensions:
        if dimension not in dimension_scores.columns:
            continue
        scores = dimension_scores[dimension].dropna()
        pair = pd.concat([returns, scores], axis=1, join="inner").dropna().tail(window)
        if len(pair) < settings.min_months:
            continue
        beta = pair.iloc[:, 0].corr(pair.iloc[:, 1])
        if not np.isfinite(beta):
            continue
        today = float(scores.iloc[-1])
        out.add(
            f"{dimension}_alignment",
            SignalCategory.MACRO,
            float(np.clip(beta * today, -1.0, 1.0)),
            f"correlation with the {dimension} score ({beta:+.2f}) times its level "
            f"today ({today:+.2f})",
            value=beta,
            source="macro/regime_history",
        )


# -------------------------------------------------------------------------------- compose
def composite(signals: list[Signal], settings: SignalSettings) -> float:
    """Weighted mean of category composites, renormalised over the categories present."""
    if not signals:
        return 0.0
    weights = {
        "technical": {
            "momentum_12_1": settings.technical.momentum.weight,
            "trend": settings.technical.trend.weight,
            "mean_reversion": settings.technical.mean_reversion.weight,
            "relative_momentum": settings.technical.relative_momentum.weight,
        },
        "valuation": {
            "earnings_yield": settings.valuation.earnings_yield.weight,
            "cape": settings.valuation.cape.weight,
            "yield_level": settings.valuation.yield_level.weight,
            "credit_spread": settings.valuation.credit_spread.weight,
        },
        "macro": {"regime_fit": settings.macro.regime_fit.weight},
    }
    alignment = settings.macro.dimension_alignment
    for dimension in alignment.dimensions:
        weights["macro"][f"{dimension}_alignment"] = alignment.weight / len(alignment.dimensions)

    by_category: dict[str, float] = {}
    for category, table in weights.items():
        members = [s for s in signals if s.category.value == category]
        if not members:
            continue
        total = sum(table.get(s.name, 1.0) for s in members)
        by_category[category] = sum(s.score * table.get(s.name, 1.0) for s in members) / total

    live = {c: w for c, w in settings.category_weights.items() if c in by_category}
    if not live:
        return 0.0
    denominator = sum(live.values())
    return float(np.clip(sum(by_category[c] * w for c, w in live.items()) / denominator, -1.0, 1.0))


def run_signals(
    store: DataStore,
    *,
    as_of: str | date | None = None,
    settings: SignalSettings | None = None,
    regime_labels: pd.Series | None = None,
    dimension_scores: pd.DataFrame | None = None,
    regime: str | None = None,
    assets: list[str] | None = None,
    inputs: list[InputRef] | None = None,
) -> SignalsResult:
    """Score every signal for each asset (default: all 18), from data known on ``as_of``.

    ``regime_labels`` are the macro skill's month-end labels and ``dimension_scores`` its
    dimension panel; without them the macro category is skipped rather than guessed.
    """
    settings = settings or load_signal_settings(store.config)
    as_of_ts = pd.Timestamp(as_of if as_of is not None else date.today()).normalize()
    ids = assets or [a.id for a in store.universe.assets]

    returns = store.asset_returns(as_of=as_of_ts)
    if returns.empty:
        raise ValueError("no asset returns available; run `uv run saa-data ingest` first")
    macro = store.macro(settings.series_ids, as_of=as_of_ts, freq="M")

    mom = settings.technical.relative_momentum
    span = mom.lookback_months - mom.skip_months
    growth_all = (1 + returns / 100).cumprod()
    skipped = growth_all.shift(mom.skip_months)
    universe_momentum = ((skipped / skipped.shift(span) - 1) * 100).iloc[-1].dropna()

    if regime is None and regime_labels is not None and len(regime_labels):
        regime = str(regime_labels.iloc[-1])

    bodies: dict[str, SignalsBody] = {}
    for asset_id in ids:
        asset = store.universe.get(asset_id)
        out = AssetSignals(asset_id)
        series = (
            returns[asset_id].dropna() if asset_id in returns.columns else pd.Series(dtype=float)
        )
        if len(series):
            _technical(asset_id, series, universe_momentum, settings, out)
            _macro(asset_id, series, regime_labels, regime, dimension_scores, settings, out)
        _valuation(asset_id, asset.group, settings, store, as_of_ts, macro, out)

        if not out.signals:
            log.warning("signals: no signal could be computed for %s", asset_id)
        bodies[asset_id] = SignalsBody(
            asset_id=asset_id,
            signals=out.signals,
            composite_score=composite(out.signals, settings),
        )

    return SignalsResult(
        as_of=as_of_ts.date(),
        bodies=bodies,
        regime=regime,
        provenance=store.provenance(),
        inputs=list(inputs or []),
    )


def render_report(result: SignalsResult) -> str:
    lines = [
        "# Asset Signals",
        "",
        f"As of {result.as_of}" + (f", regime **{result.regime}**" if result.regime else ""),
        "",
        "Scores run -1 (bearish) to +1 (bullish) for that asset's forward return.",
        "",
        "| asset | composite | technical | valuation | macro | signals |",
        "|---|---|---|---|---|---|",
    ]
    for asset_id, body in result.bodies.items():
        cells = []
        for category in ("technical", "valuation", "macro"):
            members = [s.score for s in body.signals if s.category.value == category]
            cells.append(f"{np.mean(members):+.2f}" if members else "–")
        lines.append(
            f"| {asset_id} | {body.composite_score:+.2f} | "
            + " | ".join(cells)
            + f" | {len(body.signals)} |"
        )
    return "\n".join(lines) + "\n"


def write_outputs(result: SignalsResult, run: RunContext) -> list[Path]:
    """Write ``cma/<asset>/signals.json`` per asset and ``reports/signals.md``."""
    report = run.write_report(render_report(result), REPORT)
    written = [report]
    for asset_id, body in result.bodies.items():
        written.append(
            run.write(
                SIGNALS_CONTRACT,
                asset_id.replace("_", "-"),
                body,
                produced_by=Producer.SCRIPT,
                asset_id=asset_id,
                provenance=result.provenance,
                inputs=result.inputs,
                report_path=report,
            )
        )
    return written

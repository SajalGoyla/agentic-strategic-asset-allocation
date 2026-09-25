"""Deterministic macro regime scoring. No LLM involved.

Ang, Azimbayev & Kim (2026) §3.2: the macro agent "scores four dimensions -- growth, inflation,
monetary policy, and financial conditions -- using a weighted scoring framework to classify the
current regime". The paper does not publish the framework, so the indicators, transforms,
weights and classification rules live in ``config/macro_scoring.yaml``.

The whole module is a function of ``as_of``. ``score_history`` walks month-ends and returns a
dimension-score panel plus a regime label per month, which serves two purposes: the last row is
the current regime call, and the whole column is the label history the regime-adjusted CMA
method (§3.3 method 2) and ``skills.historical_analysis.conditional_stats`` need.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from saa.contracts.macro import DIMENSIONS, DimensionScore, IndicatorScore, PitQuality, Transform
from saa.data.store import DataStore
from saa.macro_scoring_config import Indicator, MacroScoringConfig

log = logging.getLogger(__name__)

MONTH_END = "ME"


# --------------------------------------------------------------------------------- transforms
def apply_transform(series: pd.Series, indicator: Indicator) -> pd.Series:
    """Turn a raw monthly series into the quantity that gets scored."""
    series = series.dropna()
    if series.empty:
        return series
    match indicator.transform:
        case Transform.LEVEL:
            return series
        case Transform.YOY:
            return series.pct_change(12, fill_method=None) * 100
        case Transform.MOM_ANNUALISED:
            return ((1 + series.pct_change(fill_method=None)) ** 12 - 1) * 100
        case Transform.DIFF:
            return series.diff(indicator.diff_months)
        case Transform.ZSCORE:
            return series
        case Transform.PERCENTILE:
            return series
    raise ValueError(f"unhandled transform {indicator.transform}")


def to_score(transformed: pd.Series, indicator: Indicator, lookback_years: int) -> pd.Series:
    """Map a transformed series onto [-1, +1] against its own trailing history.

    ``percentile`` maps the trailing rank directly; everything else is z-scored over the
    lookback and squashed with ``tanh`` so a single extreme print moves the dimension without
    dominating it. The z-score uses only data up to each point, so the mapping is causal --
    a score for March 2008 never sees 2009.
    """
    transformed = transformed.dropna()
    if transformed.empty:
        return transformed

    window = max(lookback_years * 12, 24)
    minimum = 24

    if indicator.transform is Transform.PERCENTILE:
        ranks = transformed.rolling(window, min_periods=minimum).rank(pct=True)
        scores = ranks * 2 - 1
    else:
        rolling = transformed.rolling(window, min_periods=minimum)
        mean, std = rolling.mean(), rolling.std()
        z = (transformed - mean) / std.replace(0.0, np.nan)
        scores = np.tanh(z / 2.0)

    return (scores * indicator.sign).clip(-1.0, 1.0).dropna()


# ----------------------------------------------------------------------------------- scoring
@dataclass(frozen=True)
class ScorePanel:
    """Monthly dimension scores, the regime label per month, and coverage diagnostics."""

    scores: pd.DataFrame  # index: month end, columns: the four dimensions
    momentum: pd.Series  # change in the growth score over `momentum_months`
    regimes: pd.Series  # regime label per month
    confidence: pd.Series  # deterministic confidence per month, in [0, 1]
    indicators: dict[str, pd.DataFrame]  # dimension -> per-indicator score panel
    used: dict[str, list[Indicator]]  # dimension -> indicators that had data
    point_in_time: bool

    @property
    def as_of(self) -> pd.Timestamp:
        return self.scores.index[-1]

    def latest(self) -> dict[str, float]:
        return self.scores.iloc[-1].to_dict()


def _indicator_panel(
    store: DataStore,
    indicators: list[Indicator],
    *,
    as_of: date | str | None,
    lookback_years: int,
) -> tuple[pd.DataFrame, list[Indicator], dict[str, pd.Series]]:
    """Score every indicator of one dimension. Returns the score panel, which indicators had
    usable data, and the transformed (pre-score) series for reporting."""
    scored: dict[str, pd.Series] = {}
    transformed: dict[str, pd.Series] = {}
    used: list[Indicator] = []

    for indicator in indicators:
        try:
            wide = store.macro(indicator.series, as_of=as_of, freq="M")
        except Exception as exc:  # a series absent from the lake must not kill the run
            log.warning("macro scoring: %s unavailable (%s)", indicator.series, exc)
            continue
        if wide.empty or indicator.series not in wide.columns:
            continue

        values = apply_transform(wide[indicator.series], indicator)
        scores = to_score(values, indicator, lookback_years)
        if scores.empty:
            continue

        scored[indicator.series] = scores
        transformed[indicator.series] = values
        used.append(indicator)

    panel = pd.DataFrame(scored).sort_index() if scored else pd.DataFrame()
    return panel, used, transformed


def _weighted(panel: pd.DataFrame, used: list[Indicator], min_indicators: int) -> pd.Series:
    """Weighted mean across indicators, renormalised row by row over whichever are present."""
    if panel.empty:
        return pd.Series(dtype="float64")
    weights = pd.Series({i.series: i.weight for i in used}).reindex(panel.columns)
    present = panel.notna()
    live = present.sum(axis=1)
    denominator = present.mul(weights, axis=1).sum(axis=1).replace(0.0, np.nan)
    combined = panel.mul(weights, axis=1).sum(axis=1, min_count=1) / denominator
    return combined.where(live >= min_indicators).clip(-1.0, 1.0)


def classify(scores: dict[str, float], momentum: float, config: MacroScoringConfig) -> str:
    """Apply the classification rules in order; the first whose conditions all hold wins."""
    values = dict(scores)
    values["momentum"] = momentum

    for rule in config.classification.rules:
        satisfied = True
        for field, threshold in rule.when.items():
            key, _, comparison = field.rpartition("_")
            if comparison == "least":  # "<dim>_at_least"
                key = key.removesuffix("_at")
            value = values.get(key)
            if value is None or pd.isna(value):
                satisfied = False
                break
            if comparison == "below" and not value < threshold:
                satisfied = False
                break
            if comparison == "least" and not value >= threshold:
                satisfied = False
                break
        if satisfied:
            return rule.regime
    return config.classification.default


def _confidence(
    scores: pd.DataFrame,
    momentum: pd.Series,
    regimes: pd.Series,
    coverage: float,
    config: MacroScoringConfig,
) -> pd.Series:
    """How clear-cut the deterministic call is, in [0, 1].

    Three things reduce it: dimension scores sitting close to the thresholds that decided the
    regime, the four dimensions disagreeing with one another, and configured indicators having
    no data at this date.
    """
    settings = config.confidence

    thresholds = sorted(
        {t for rule in config.classification.rules for t in rule.when.values()} | {0.0}
    )
    growth = scores["growth"]
    distance = pd.Series(
        [min(abs(g - t) for t in thresholds) if pd.notna(g) else np.nan for g in growth],
        index=growth.index,
    )
    margin = (distance / settings.margin_full).clip(0.0, 1.0)

    dispersion = scores.std(axis=1).fillna(0.0)
    agreement = 1.0 - (dispersion / dispersion.max() if dispersion.max() else 0.0)

    base = 0.5 * margin.fillna(0.0) + 0.5 * agreement.clip(0.0, 1.0)
    penalty = settings.coverage_penalty * (1.0 - coverage)
    confidence = (base * (1.0 - penalty)).clip(0.0, 1.0)

    # A regime that just changed is less certain than one that has held for months.
    just_changed = regimes != regimes.shift(1)
    confidence = confidence.where(~just_changed, confidence * 0.85)
    _ = momentum  # retained for signature symmetry; momentum enters through the rules
    return confidence.clip(0.0, 1.0)


def score_history(
    store: DataStore,
    config: MacroScoringConfig,
    *,
    as_of: date | str | None = None,
    start: date | str | None = None,
    point_in_time: bool = False,
) -> ScorePanel:
    """Score every month up to ``as_of`` and classify each one.

    ``point_in_time=False`` (the default) scores the whole history from the latest vintage of
    each series: correct for a live run, but each historical month is scored with data revised
    after the fact. ``point_in_time=True`` re-queries the lake at every month end so each row
    sees only what was public then -- much slower, and what a backtest needs. Either way the
    choice is recorded on the panel and surfaced in the contract.
    """
    if point_in_time:
        return _score_history_pit(store, config, as_of=as_of, start=start)

    panels: dict[str, pd.DataFrame] = {}
    combined: dict[str, pd.Series] = {}
    used: dict[str, list[Indicator]] = {}
    configured = live = 0

    for dimension in DIMENSIONS:
        indicators = config.indicators(dimension)
        panel, dimension_used, _ = _indicator_panel(
            store, indicators, as_of=as_of, lookback_years=config.lookback_years
        )
        panels[dimension] = panel
        used[dimension] = dimension_used
        combined[dimension] = _weighted(panel, dimension_used, config.min_indicators)
        configured += len(indicators)
        live += len(dimension_used)

    scores = pd.DataFrame(combined).sort_index()
    if start is not None:
        scores = scores[scores.index >= pd.Timestamp(start)]
    scores = scores.dropna(how="all")
    if scores.empty:
        raise ValueError(
            "no macro dimension could be scored; has `uv run saa-data ingest` been run?"
        )

    # Every classification rule tests growth, so a month without a growth score cannot be
    # classified -- it would fall through to the default regime and look like a real call.
    # Drop those months outright. In practice they sit at both ends: the head needs a warm-up
    # before the trailing z-scores are defined, and the tail is the ragged edge, where monthly
    # growth releases have not landed yet. The caller sees the result as `data_end` coming in
    # behind the as-of date.
    scoreable = scores["growth"].notna()
    if not scoreable.any():
        raise ValueError(
            "growth could not be scored for any month; the lake may be stale or "
            f"fewer than {config.min_indicators} growth indicators are available"
        )
    scores = scores[scoreable]

    momentum = scores["growth"].diff(config.momentum_months)
    regimes = pd.Series(
        [
            classify(scores.loc[stamp].to_dict(), momentum.get(stamp, np.nan), config)
            for stamp in scores.index
        ],
        index=scores.index,
        name="regime",
    )
    coverage = live / configured if configured else 0.0
    confidence = _confidence(scores, momentum, regimes, coverage, config)

    return ScorePanel(
        scores=scores,
        momentum=momentum,
        regimes=regimes,
        confidence=confidence,
        indicators=panels,
        used=used,
        point_in_time=False,
    )


def _score_history_pit(
    store: DataStore,
    config: MacroScoringConfig,
    *,
    as_of: date | str | None,
    start: date | str | None,
) -> ScorePanel:
    """Point-in-time variant: one scoring pass per month end, each seeing only public data."""
    end = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.today().normalize()
    begin = pd.Timestamp(start) if start is not None else end - pd.DateOffset(years=10)
    month_ends = pd.date_range(begin, end, freq=MONTH_END)
    if not len(month_ends):
        raise ValueError(f"no month ends between {begin.date()} and {end.date()}")

    rows, regimes, confidences = {}, {}, {}
    last: ScorePanel | None = None
    for stamp in month_ends:
        try:
            panel = score_history(store, config, as_of=stamp, point_in_time=False)
        except ValueError:
            continue
        rows[stamp] = panel.scores.iloc[-1]
        regimes[stamp] = panel.regimes.iloc[-1]
        confidences[stamp] = panel.confidence.iloc[-1]
        last = panel

    if last is None:
        raise ValueError("point-in-time scoring produced no rows")

    scores = pd.DataFrame(rows).T.sort_index()
    return ScorePanel(
        scores=scores,
        momentum=scores["growth"].diff(config.momentum_months),
        regimes=pd.Series(regimes, name="regime").sort_index(),
        confidence=pd.Series(confidences).sort_index(),
        indicators=last.indicators,
        used=last.used,
        point_in_time=True,
    )


# ------------------------------------------------------------------------- contract building
def to_dimension_scores(
    panel: ScorePanel, config: MacroScoringConfig, store: DataStore
) -> list[DimensionScore]:
    """Build the contract's ``DimensionScore`` list for the latest month of the panel."""
    stamp = panel.as_of
    catalog = {s.id: s for s in store.config.macro.series}
    out: list[DimensionScore] = []

    for dimension in DIMENSIONS:
        indicator_panel = panel.indicators[dimension]
        rows: list[IndicatorScore] = []
        for indicator in panel.used[dimension]:
            column = indicator_panel.get(indicator.series)
            if column is None:
                continue
            visible = column.loc[:stamp].dropna()
            if visible.empty:
                continue
            observed = visible.index[-1]
            meta = catalog[indicator.series]
            rows.append(
                IndicatorScore(
                    series_id=indicator.series,
                    name=meta.name,
                    value=float(visible.iloc[-1]),
                    transform=indicator.transform,
                    score=float(visible.iloc[-1]),
                    weight=float(indicator.weight),
                    observation_date=observed.date(),
                    available_from=(
                        observed + pd.Timedelta(days=max(meta.release_lag_days, 0))
                    ).date(),
                    point_in_time=bool(meta.vintages and panel.point_in_time),
                )
            )
        score = panel.scores.loc[stamp, dimension]
        out.append(
            DimensionScore(
                dimension=dimension,
                score=float(score) if pd.notna(score) else 0.0,
                indicators=rows,
            )
        )
    return out


def to_pit_quality(scores: list[DimensionScore]) -> list[PitQuality]:
    return [
        PitQuality(
            dimension=d.dimension,
            indicators_total=len(d.indicators),
            indicators_point_in_time=sum(1 for i in d.indicators if i.point_in_time),
        )
        for d in scores
    ]

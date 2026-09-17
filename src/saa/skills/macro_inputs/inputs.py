"""Point-in-time macro indicator values for the macro agent's scoring script.

This skill stops one step short of scoring: it returns, for each FRED series, the transformed
value the dimension is scored on, the raw value behind it, the dates involved, and whether the
number came from a true ALFRED vintage or from a release-lag estimate. The macro agent turns
those into ``IndicatorScore`` by adding its score and weight, which are its judgement, not data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from saa.config import Config, load_config
from saa.contracts.macro import IndicatorScore, PitQuality, Transform
from saa.data.store import DataStore
from saa.skills.macro_inputs import transforms

DEFAULT_LOOKBACK_YEARS = transforms.DEFAULT_LOOKBACK_YEARS


@dataclass(frozen=True)
class IndicatorRequest:
    """Which series to read and how to make it comparable."""

    series_id: str
    transform: Transform | str = Transform.LEVEL
    lookback_years: int = DEFAULT_LOOKBACK_YEARS
    diff_months: int = transforms.DEFAULT_DIFF_MONTHS


@dataclass(frozen=True)
class MacroIndicator:
    """One series as of one date, ready to be scored."""

    series_id: str
    name: str
    dimension: str
    transform: Transform
    value: float
    raw_value: float
    observation_date: date
    available_from: date
    # True when the value came from an ALFRED vintage in force at as_of, rather than from a
    # release-lag estimate. Only 8 of the 62 FRED series carry vintages, and they start as late
    # as 2011 (CFNAI) and 2016 (GDPNOW), so a backtest should report this, not assume it.
    point_in_time: bool
    history: pd.Series  # the transformed series up to as_of, for context and charts

    def to_score(self, score: float, weight: float) -> IndicatorScore:
        """Complete this into the contract model once the agent has judged score and weight."""
        return IndicatorScore(
            series_id=self.series_id,
            name=self.name,
            value=self.value,
            raw_value=self.raw_value,
            transform=self.transform,
            score=score,
            weight=weight,
            observation_date=self.observation_date,
            available_from=self.available_from,
            point_in_time=self.point_in_time,
        )


def indicator(
    store: DataStore,
    request: IndicatorRequest | str,
    *,
    as_of: str | date | pd.Timestamp | None = None,
    config: Config | None = None,
) -> MacroIndicator:
    """One indicator as of ``as_of``, using only observations published by then."""
    if isinstance(request, str):
        request = IndicatorRequest(series_id=request)
    config = config or store.config
    as_of_ts = pd.Timestamp(as_of if as_of is not None else date.today()).normalize()

    catalog = {s.id: s for s in config.macro.series}
    if request.series_id not in catalog:
        raise KeyError(f"{request.series_id} is not in config/macro_series.yaml")
    meta = catalog[request.series_id]

    long = store.macro_long(request.series_id, as_of=as_of_ts)
    if long.empty:
        raise ValueError(f"{request.series_id} has no observations available on {as_of_ts.date()}")
    long = long.sort_values("date")
    raw = long.set_index("date")["value"].astype(float)

    transformed = transforms.apply(
        raw,
        request.transform,
        lookback_years=request.lookback_years,
        diff_months=request.diff_months,
    ).dropna()
    if transformed.empty:
        raise ValueError(
            f"{request.series_id}: no {Transform(request.transform).value} value on "
            f"{as_of_ts.date()} -- too little history, or the transform does not suit this "
            f"series (proportional change needs a positive base; use diff or level)"
        )

    observation_date = transformed.index[-1]
    latest = long[long["date"] == observation_date].iloc[-1]
    return MacroIndicator(
        series_id=request.series_id,
        name=meta.name,
        dimension=meta.dimension,
        transform=Transform(request.transform),
        value=float(transformed.iloc[-1]),
        raw_value=float(latest["value"]),
        observation_date=observation_date.date(),
        available_from=pd.Timestamp(latest["available_from"]).date(),
        point_in_time=bool(pd.notna(latest["realtime_start"])),
        history=transformed,
    )


def indicators(
    store: DataStore,
    requests: list[IndicatorRequest | str],
    *,
    as_of: str | date | pd.Timestamp | None = None,
    config: Config | None = None,
) -> list[MacroIndicator]:
    """Several indicators; a series with too little history at ``as_of`` is skipped rather than
    failing the whole dimension."""
    out = []
    for request in requests:
        try:
            out.append(indicator(store, request, as_of=as_of, config=config))
        except ValueError:
            continue
    return out


def dimension_requests(
    config: Config, dimension: str, *, transform: Transform | str = Transform.LEVEL
) -> list[IndicatorRequest]:
    """Every series a macro dimension declares in config/macro_series.yaml, with one transform.
    The macro agent will normally pass a per-series transform instead."""
    series = config.macro.by_dimension(dimension)
    if not series:
        raise KeyError(f"no macro series declared for dimension {dimension!r}")
    return [
        IndicatorRequest(series_id=s.id, transform=transform)
        for s in series
        if not s.evaluation_only
    ]


def pit_quality(found: list[MacroIndicator]) -> list[PitQuality]:
    """Per dimension, how many indicators came from a true vintage (``MacroScores.pit_quality``)."""
    by_dimension: dict[str, list[MacroIndicator]] = {}
    for item in found:
        by_dimension.setdefault(item.dimension, []).append(item)
    return [
        PitQuality(
            dimension=dimension,
            indicators_total=len(items),
            indicators_point_in_time=sum(1 for i in items if i.point_in_time),
        )
        for dimension, items in sorted(by_dimension.items())
    ]


def to_frame(found: list[MacroIndicator]) -> pd.DataFrame:
    """Tabular view for eyeballing a dimension."""
    return pd.DataFrame(
        [
            {
                "series_id": i.series_id,
                "dimension": i.dimension,
                "transform": i.transform.value,
                "value": i.value,
                "raw_value": i.raw_value,
                "observation_date": i.observation_date,
                "available_from": i.available_from,
                "point_in_time": i.point_in_time,
                "name": i.name,
            }
            for i in found
        ]
    )


def load_store(config: Config | None = None) -> DataStore:
    return DataStore(config or load_config())

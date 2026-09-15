"""Run the historical-analysis skill over the 18 asset classes."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from saa.data.store import DataStore
from saa.skills.historical_analysis import metrics as m
from saa.skills.historical_analysis.models import (
    AssetHistoricalStats,
    CorrelationRow,
    HistoricalAnalysis,
    RegimeStats,
    SourceSpan,
    StockBondCorrelation,
    WindowStats,
)

EQUITY_ANCHOR = "us_large_cap"
BOND_ANCHOR = "intermediate_treasuries"
MIN_MONTHS_OPEN_WINDOW = 36  # 'since_1990' / 'full' windows need at least 3 years

DEFAULT_WINDOWS: dict[str, int | str] = {
    "1y": 12,
    "3y": 36,
    "5y": 60,
    "10y": 120,
    "since_1990": "1990-01-31",
    "full": "full",
}


@dataclass(frozen=True)
class AnalysisSettings:
    # int = trailing months; date string = from that month-end; "full" = all history
    windows: dict[str, int | str] = field(default_factory=lambda: dict(DEFAULT_WINDOWS))
    correlation_windows: tuple[str, ...] = ("3y", "5y", "10y", "since_1990")
    rolling_correlation_months: int = 36
    risk_free_series: str = "DTB3"


# --------------------------------------------------------------------------- helpers
def _num(value) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _day(value) -> date | None:
    return None if value is None or pd.isna(value) else pd.Timestamp(value).date()


def window_slice(returns: pd.Series, spec: int | str, end: pd.Timestamp) -> pd.Series:
    r = returns.loc[:end].dropna()
    if spec == "full":
        return r
    if isinstance(spec, int):
        return r.iloc[-spec:]
    return r.loc[pd.Timestamp(spec) :]


def is_sufficient(window: pd.Series, spec: int | str) -> bool:
    if isinstance(spec, int):
        return len(window) == spec
    return len(window) >= MIN_MONTHS_OPEN_WINDOW


def risk_free_monthly(
    store: DataStore, as_of: pd.Timestamp, series: str
) -> tuple[pd.Series, float | None]:
    """Monthly risk-free return = previous month-end 3-month T-bill yield / 12 (FRED, point-in-time)."""
    yields = store.macro(series, as_of=as_of, freq="M")
    if series not in yields:
        return pd.Series(dtype=float), None
    y = yields[series].dropna()
    rf = (y.shift(1) / 100 / m.MONTHS_PER_YEAR).dropna()
    return rf, (float(y.iloc[-1]) if len(y) else None)


def source_spans(
    sources: pd.Series, kinds: pd.Series, end: pd.Timestamp | None
) -> list[SourceSpan]:
    """Consecutive runs of the same source, oldest first."""
    frame = pd.concat([sources, kinds], axis=1, keys=["source", "kind"]).dropna()
    if end is not None:
        frame = frame.loc[:end]
    if frame.empty:
        return []
    # object dtype: pyarrow-backed string comparisons yield bool[pyarrow], which has no cumsum
    source = frame["source"].astype(object)
    run_id = (source != source.shift()).cumsum()
    spans = []
    for _, g in frame.groupby(run_id, sort=False):
        spans.append(
            SourceSpan(
                source=str(g["source"].iloc[0]),
                kind=str(g["kind"].iloc[0]),
                start=g.index.min().date(),
                end=g.index.max().date(),
                months=len(g),
            )
        )
    return spans


def window_stats(
    name: str,
    returns: pd.Series,
    sufficient: bool,
    risk_free: pd.Series,
    kinds: pd.Series,
    anchors: dict[str, pd.Series],
) -> WindowStats:
    stats = WindowStats(
        window=name,
        start=_day(returns.index.min()) if len(returns) else None,
        end=_day(returns.index.max()) if len(returns) else None,
        months=len(returns),
        sufficient=sufficient,
    )
    if not sufficient:
        return stats
    dd = m.max_drawdown(returns)
    rf = risk_free.reindex(returns.index)
    window_kinds = kinds.reindex(returns.index).astype(object)
    equity = anchors.get(EQUITY_ANCHOR, pd.Series(dtype=float)).reindex(returns.index)
    bonds = anchors.get(BOND_ANCHOR, pd.Series(dtype=float)).reindex(returns.index)
    return stats.model_copy(
        update={
            "annualized_return": _num(m.annualized_return(returns)),
            "cumulative_return": _num(m.cumulative_return(returns)),
            "annualized_volatility": _num(m.annualized_volatility(returns)),
            "sharpe_ratio": _num(m.sharpe_ratio(returns, rf)),
            "sortino_ratio": _num(m.sortino_ratio(returns, rf)),
            "max_drawdown": _num(dd.depth),
            "max_drawdown_peak": _day(dd.peak),
            "max_drawdown_trough": _day(dd.trough),
            "max_drawdown_recovery": _day(dd.recovery),
            "max_drawdown_duration_months": dd.duration_months,
            "current_drawdown": _num(m.current_drawdown(returns)),
            "var_95_monthly": _num(m.value_at_risk(returns)),
            "cvar_95_monthly": _num(m.conditional_value_at_risk(returns)),
            "skewness": _num(m.skewness(returns)),
            "excess_kurtosis": _num(m.excess_kurtosis(returns)),
            "best_month": _num(returns.max()),
            "best_month_date": _day(returns.idxmax()),
            "worst_month": _num(returns.min()),
            "worst_month_date": _day(returns.idxmin()),
            "hit_rate": _num(m.hit_rate(returns)),
            "beta_to_us_large_cap": _num(m.beta(returns, equity)),
            "correlation_to_us_large_cap": _num(m.correlation(returns, equity)),
            "correlation_to_intermediate_treasuries": _num(m.correlation(returns, bonds)),
            "proxy_share": _num((window_kinds != "etf").mean()) if len(window_kinds) else None,
        }
    )


def _daily_returns(store: DataStore, tickers: list[str], as_of: pd.Timestamp) -> pd.DataFrame:
    try:
        prices = store.prices(tickers, as_of=as_of)
    except FileNotFoundError:
        return pd.DataFrame()
    return prices.pct_change(fill_method=None)


def _stock_bond_correlation(
    returns: pd.DataFrame, end: pd.Timestamp, window: int
) -> StockBondCorrelation | None:
    if EQUITY_ANCHOR not in returns or BOND_ANCHOR not in returns:
        return None
    rolling = m.rolling_correlation(
        returns[EQUITY_ANCHOR].loc[:end], returns[BOND_ANCHOR].loc[:end], window
    ).dropna()
    if rolling.empty:
        return None
    last_10y = rolling.loc[rolling.index > end - pd.DateOffset(years=10)]
    return StockBondCorrelation(
        pair=[EQUITY_ANCHOR, BOND_ANCHOR],
        window_months=window,
        latest=_num(rolling.iloc[-1]),
        one_year_ago=_num(rolling.iloc[-13]) if len(rolling) > 12 else None,
        min_10y=_num(last_10y.min()),
        max_10y=_num(last_10y.max()),
    )


# --------------------------------------------------------------------------- entry points
def run_historical_analysis(
    store: DataStore | None = None,
    *,
    as_of: str | date | None = None,
    settings: AnalysisSettings | None = None,
    regime_labels: pd.Series | None = None,
) -> HistoricalAnalysis:
    """Statistics for every asset using only data available on ``as_of`` (default: today).

    ``regime_labels`` (month-end index -> regime name, e.g. from the macro agent's historical
    scoring) adds regime-conditional statistics per asset.
    """
    store = store or DataStore()
    settings = settings or AnalysisSettings()
    as_of_ts = pd.Timestamp(as_of if as_of is not None else date.today()).normalize()

    returns = store.asset_returns(as_of=as_of_ts)
    if returns.empty:
        raise ValueError(f"no asset returns available as of {as_of_ts.date()}")
    sources = store.asset_returns(field="source", as_of=as_of_ts)
    kinds = store.asset_returns(field="kind", as_of=as_of_ts)
    risk_free, current_yield = risk_free_monthly(store, as_of_ts, settings.risk_free_series)
    daily = _daily_returns(store, store.universe.tickers, as_of_ts)

    ends = {c: returns[c].last_valid_index() for c in returns.columns}
    common_end = min(e for e in ends.values() if e is not None)
    anchors = {k: returns[k] for k in (EQUITY_ANCHOR, BOND_ANCHOR) if k in returns}

    assets = []
    for asset in store.universe.assets:
        if asset.id not in returns:
            continue
        series, end = returns[asset.id], ends[asset.id]
        windows = {}
        for name, spec in settings.windows.items():
            window = window_slice(series, spec, end)
            windows[name] = window_stats(
                name, window, is_sufficient(window, spec), risk_free, kinds[asset.id], anchors
            )
        daily_asset = daily[asset.ticker] if asset.ticker in daily else pd.Series(dtype=float)
        assets.append(
            AssetHistoricalStats(
                asset_id=asset.id,
                name=asset.name,
                group=asset.group,
                ticker=asset.ticker,
                as_of=as_of_ts.date(),
                data_end=_day(end),
                history_start=_day(series.first_valid_index()),
                sources=source_spans(sources[asset.id], kinds[asset.id], end),
                windows=windows,
                recent_daily_volatility={
                    "3m": _num(m.realized_volatility(daily_asset, 63)),
                    "1y": _num(m.realized_volatility(daily_asset, 252)),
                },
            )
        )

    months, matrices = {}, {}
    upto_end = returns.loc[:common_end]
    for name in settings.correlation_windows:
        spec = settings.windows[name]
        if spec == "full":
            frame = upto_end
        elif isinstance(spec, int):
            frame = upto_end.iloc[-spec:]
        else:
            frame = upto_end.loc[pd.Timestamp(spec) :]
        months[name] = len(frame)
        matrices[name] = m.correlation_matrix(
            frame, min_periods=min(MIN_MONTHS_OPEN_WINDOW, len(frame))
        )
    correlation_rows = [
        CorrelationRow(
            asset_id=asset_id,
            as_of=as_of_ts.date(),
            end=_day(common_end),
            months=months,
            correlations={
                name: {
                    other: _num(matrix.loc[asset_id, other])
                    for other in matrix.columns
                    if other != asset_id
                }
                for name, matrix in matrices.items()
            },
        )
        for asset_id in returns.columns
    ]

    regime_stats = None
    if regime_labels is not None:
        regime_stats = {
            asset_id: [
                RegimeStats(**{k: (_num(v) if isinstance(v, float) else v) for k, v in row.items()})
                for row in m.conditional_stats(returns[asset_id], risk_free, regime_labels).to_dict(
                    "records"
                )
            ]
            for asset_id in returns.columns
        }

    provenance = store.provenance()
    for stats in assets:
        stats.provenance = provenance
    return HistoricalAnalysis(
        as_of=as_of_ts.date(),
        generated_at=datetime.now(UTC),
        data_end=_day(common_end),
        windows=settings.windows,
        risk_free={
            "series": settings.risk_free_series,
            "description": "FRED 3-month T-bill; monthly rate = previous month-end yield / 12",
            "current_annual_yield_pct": current_yield,
        },
        assets=assets,
        correlation_rows=correlation_rows,
        stock_bond_correlation=_stock_bond_correlation(
            returns, common_end, settings.rolling_correlation_months
        ),
        regime_stats=regime_stats,
        provenance=provenance,
    )


def _pct(value: float | None, digits: int = 1) -> str:
    return "n/a" if value is None else f"{value * 100:.{digits}f}%"


def _ratio(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def render_summary(analysis: HistoricalAnalysis) -> str:
    """Human-readable markdown summary (the paper pairs every JSON output with a report)."""
    rf = analysis.risk_free.get("current_annual_yield_pct")
    lines = [
        f"# Historical analysis as of {analysis.as_of}",
        "",
        f"Monthly returns through {analysis.data_end}. Risk-free: 3-month T-bill"
        + (f", currently {rf:.2f}%." if isinstance(rf, float) else "."),
        "",
        "| Asset | 10y return | 10y vol | 10y Sharpe | 10y max DD | Since-1990 return | Since-1990 vol | Current DD | Proxy share (since 1990) | 3m daily vol |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in analysis.assets:
        w10, w90 = s.windows.get("10y"), s.windows.get("since_1990")
        lines.append(
            "| "
            + " | ".join(
                [
                    f"{s.name} ({s.ticker})",
                    _pct(w10.annualized_return if w10 else None),
                    _pct(w10.annualized_volatility if w10 else None),
                    _ratio(w10.sharpe_ratio if w10 else None),
                    _pct(w10.max_drawdown if w10 else None),
                    _pct(w90.annualized_return if w90 else None),
                    _pct(w90.annualized_volatility if w90 else None),
                    _pct(w10.current_drawdown if w10 else None),
                    _pct(w90.proxy_share if w90 else None, 0),
                    _pct(s.recent_daily_volatility.get("3m")),
                ]
            )
            + " |"
        )
    sb = analysis.stock_bond_correlation
    if sb:
        lines += [
            "",
            f"Stock-bond correlation ({sb.pair[0]} vs {sb.pair[1]}, rolling {sb.window_months} months): "
            f"latest {_ratio(sb.latest)}, one year ago {_ratio(sb.one_year_ago)}, "
            f"10-year range {_ratio(sb.min_10y)} to {_ratio(sb.max_10y)}.",
        ]
    lines += [
        "",
        "Proxy share is the fraction of months taken from pre-ETF proxies; see each asset's "
        "`sources` and docs/asset_data_map.md for their tracking error.",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(analysis: HistoricalAnalysis, out_dir: Path | str) -> Path:
    """Write historical_analysis.json, per-asset historical_stats.json and correlation_row.json,
    and summary.md."""
    out_dir = Path(out_dir)
    (out_dir / "assets").mkdir(parents=True, exist_ok=True)
    (out_dir / "historical_analysis.json").write_text(
        analysis.model_dump_json(indent=2), encoding="utf-8"
    )
    rows = {row.asset_id: row for row in analysis.correlation_rows}
    for stats in analysis.assets:
        asset_dir = out_dir / "assets" / stats.asset_id
        asset_dir.mkdir(exist_ok=True)
        (asset_dir / "historical_stats.json").write_text(
            stats.model_dump_json(indent=2), encoding="utf-8"
        )
        if stats.asset_id in rows:
            (asset_dir / "correlation_row.json").write_text(
                rows[stats.asset_id].model_dump_json(indent=2), encoding="utf-8"
            )
    (out_dir / "summary.md").write_text(render_summary(analysis), encoding="utf-8")
    return out_dir

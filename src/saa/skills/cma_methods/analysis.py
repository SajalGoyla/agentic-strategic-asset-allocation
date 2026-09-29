"""CMA-methods skill: every candidate expected return per asset, as ``cma_methods.json``.

Ang, Azimbayev & Kim (2026) §3.3: the candidates "are written to a cma_methods.json file by a
Python script; no LLM judgment is involved up to this point." The CMA judge reads the file and
picks within the range it spans.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from saa.contracts.asset_class import METHODS_CONTRACT, CmaMethodId, CmaMethodsBody
from saa.contracts.base import InputRef, Producer
from saa.contracts.portfolio import CovarianceBody
from saa.data.store import DataStore
from saa.run import RunContext
from saa.skills.cma_methods.methods import MarketInputs, run_methods
from saa.skills.cma_methods.settings import (
    CALCULATED,
    WRDS_PREFIX,
    CmaSettings,
    load_cma_settings,
)
from saa.skills.covariance import estimate_covariance
from saa.skills.historical_analysis.analysis import risk_free_monthly

REPORT = "cma_methods.md"


@dataclass(frozen=True)
class CmaMethodsResult:
    as_of: date
    horizon_years: int
    bodies: dict[str, CmaMethodsBody]
    current_regime: str | None
    risk_aversion: float | None
    provenance: dict[str, dict]
    inputs: list[InputRef]


def _needed_series(settings: CmaSettings) -> list[str]:
    series = {settings.risk_free_series}
    for recipes in settings.yields.values():
        for recipe in recipes:
            series.update(n for n in recipe.series if not n.startswith(WRDS_PREFIX))
            if recipe.add_spread and not recipe.add_spread.startswith(WRDS_PREFIX):
                series.add(recipe.add_spread)
    return sorted(series)


def _surveys(store: DataStore, settings: CmaSettings, as_of: pd.Timestamp) -> dict:
    variables = set(settings.survey.values()) | {settings.growth_survey, settings.inflation_survey}
    out = {}
    for variable in sorted(variables):
        try:
            points = store.survey(variable, horizon="point", as_of=as_of).dropna()
        except (FileNotFoundError, KeyError):
            continue
        if len(points):
            out[variable] = (float(points.iloc[-1]), pd.Timestamp(points.index[-1]))
    return out


def _optional(load, default):
    try:
        return load()
    except FileNotFoundError:
        return default


def gather_inputs(
    store: DataStore,
    settings: CmaSettings,
    *,
    as_of: pd.Timestamp,
    horizon_years: int,
    covariance: CovarianceBody | None = None,
    regime_labels: pd.Series | None = None,
) -> MarketInputs:
    """Load everything the calculators read, restricted to what was known on ``as_of``."""
    returns = store.asset_returns(as_of=as_of, start=settings.history.start)
    if returns.empty:
        raise ValueError(f"no asset returns available as of {as_of.date()}")
    risk_free, rf_now = risk_free_monthly(store, as_of, settings.risk_free_series)
    if covariance is None:
        covariance = estimate_covariance(store, as_of=as_of).body
    if regime_labels is not None:
        regime_labels = regime_labels[regime_labels.index <= as_of]
    universe = store.universe.assets
    macro = store.macro(_needed_series(settings), as_of=as_of, freq="M")
    bonds = _optional(lambda: store.corporate_bond_yields(as_of=as_of), pd.DataFrame())
    if not bonds.empty:
        bonds = bonds.rename(columns=lambda c: WRDS_PREFIX + c)
        macro = macro.join(bonds.resample("ME").last(), how="outer")
    tickers = [a.ticker for a in universe]
    prices = _optional(
        lambda: store.prices(tickers, field="close", as_of=as_of).resample("ME").last(),
        pd.DataFrame(),
    )
    return MarketInputs(
        as_of=as_of,
        returns=returns,
        risk_free=risk_free,
        risk_free_pct=rf_now,
        covariance=covariance,
        horizon_years=horizon_years,
        groups={a.id: a.group for a in universe},
        tickers={a.id: a.ticker for a in universe},
        macro=macro,
        shiller=_optional(lambda: store.shiller(as_of=as_of), None),
        fund_snapshot=_optional(lambda: store.fund_snapshot(as_of=as_of), pd.DataFrame()),
        surveys=_optional(lambda: _surveys(store, settings, as_of), {}),
        regime_labels=regime_labels,
        equity_valuation=_optional(lambda: store.equity_valuation(as_of=as_of), pd.DataFrame()),
        etf_caps=_optional(lambda: store.etf_market_caps(as_of=as_of), pd.DataFrame()),
        etf_prices=prices,
    )


def run_cma_methods(
    store: DataStore,
    *,
    as_of: str | date | None = None,
    horizon_years: int | None = None,
    settings: CmaSettings | None = None,
    covariance: CovarianceBody | None = None,
    regime_labels: pd.Series | None = None,
    assets: list[str] | None = None,
    inputs: list[InputRef] | None = None,
) -> CmaMethodsResult:
    """Every CMA candidate for each asset (default: all 18), using only data known on ``as_of``.

    ``covariance`` defaults to the covariance skill's Ledoit-Wolf matrix; pass the run's
    ``covariance.json`` body to use exactly what the PC stage will. ``regime_labels`` are the
    macro skill's month-end labels; without them the regime-adjusted method is unavailable.
    """
    settings = settings or load_cma_settings(store.config)
    horizon_years = horizon_years or store.config.ips.objectives.cma_horizon_years
    as_of_ts = pd.Timestamp(as_of if as_of is not None else date.today()).normalize()
    market = gather_inputs(
        store,
        settings,
        as_of=as_of_ts,
        horizon_years=horizon_years,
        covariance=covariance,
        regime_labels=regime_labels,
    )
    ids = assets or [a.id for a in store.universe.assets]
    unknown = sorted(set(ids) - set(market.groups))
    if unknown:
        raise ValueError(f"unknown assets {unknown}")

    bodies = {
        asset_id: CmaMethodsBody(
            asset_id=asset_id,
            horizon_years=horizon_years,
            volatility_pct=round(market.volatility_pct(asset_id), 4),
            methods=run_methods(asset_id, market, settings),
        )
        for asset_id in ids
    }
    labels = market.regime_labels
    return CmaMethodsResult(
        as_of=as_of_ts.date(),
        horizon_years=horizon_years,
        bodies=bodies,
        current_regime=str(labels.dropna().iloc[-1])
        if labels is not None and len(labels)
        else None,
        risk_aversion=(market._equilibrium or {}).get("risk_aversion"),
        provenance=store.provenance(),
        inputs=list(inputs or []),
    )


# --------------------------------------------------------------------------- outputs
_SHORT = {
    CmaMethodId.HISTORICAL_ERP: "Hist",
    CmaMethodId.REGIME_ADJUSTED: "Regime",
    CmaMethodId.BL_EQUILIBRIUM: "BL",
    CmaMethodId.INVERSE_GORDON: "Gordon",
    CmaMethodId.IMPLIED_ERP_CAPE: "CAPE",
    CmaMethodId.SURVEY_CONSENSUS: "Survey",
    CmaMethodId.YIELD_BUILDING_BLOCK: "Yield",
    CmaMethodId.AUTO_BLEND: "Blend",
}


def render_report(result: CmaMethodsResult) -> str:
    """One table of every candidate for every asset, then each asset's rationales."""
    methods = [*CALCULATED, CmaMethodId.AUTO_BLEND]
    lines = [
        f"# CMA method candidates as of {result.as_of}",
        "",
        f"Arithmetic expected annual return, nominal, percent; {result.horizon_years}-year "
        "horizon. A dash means the method does not apply or lacks data (reasons below). "
        f"Current regime: {result.current_regime or 'n/a'}; Black-Litterman risk aversion: "
        + (f"{result.risk_aversion:.2f}" if result.risk_aversion is not None else "n/a")
        + ".",
        "",
        "| Asset | Vol | " + " | ".join(_SHORT[m] for m in methods) + " | Range |",
        "|---|---|" + "---|" * len(methods) + "---|",
    ]
    for asset_id, body in result.bodies.items():
        by_method = {e.method: e for e in body.methods}
        cells = []
        for m in methods:
            e = by_method.get(m)
            cells.append(
                "-"
                if e is None or e.expected_return_pct is None
                else f"{e.expected_return_pct:.1f}"
            )
        low, high = body.method_range
        lines.append(
            f"| {asset_id} | {body.volatility_pct:.1f} | {' | '.join(cells)} | "
            f"{low:.1f}-{high:.1f} |"
        )
    lines += ["", "## Rationales", ""]
    for asset_id, body in result.bodies.items():
        lines.append(f"### {asset_id}")
        lines.append("")
        for e in body.methods:
            if e.unavailable_reason is None:
                lines.append(
                    f"- **{e.method.value}** {e.expected_return_pct:.2f}% "
                    f"(confidence {e.confidence:.2f}): {e.rationale}"
                )
            else:
                lines.append(f"- **{e.method.value}** unavailable: {e.unavailable_reason}")
        lines.append("")
    lines.append("Method definitions and caveats: `src/saa/skills/cma_methods/SKILL.md`.")
    return "\n".join(lines) + "\n"


def write_outputs(result: CmaMethodsResult, run: RunContext) -> list[Path]:
    """Write ``cma/<asset>/cma_methods.json`` per asset and ``reports/cma_methods.md``."""
    report = run.write_report(render_report(result), REPORT)
    written = [report]
    for asset_id, body in result.bodies.items():
        written.append(
            run.write(
                METHODS_CONTRACT,
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

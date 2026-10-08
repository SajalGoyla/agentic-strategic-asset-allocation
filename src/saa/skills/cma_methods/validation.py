"""Validation of the CMA layer against expected ranges (plan, Phase 2 joint deliverable).

Reads what stage 2 wrote -- ``cma_methods.json`` for every asset, and ``cma.json`` where the
judge has run -- and checks the estimate each asset will carry into portfolio construction
against the ranges in ``config/cma_validation.yaml``. The estimate is the judged CMA when there
is one, otherwise the auto-blend, and the report says which. Deterministic, reads only the run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict

from saa.config import Config
from saa.contracts import read
from saa.contracts.asset_class import CmaMethodId
from saa.run import RunContext

REPORT = "cma_validation.md"


class Status(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ValidationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plausible_pct: dict[str, tuple[float, float]]
    yield_anchor_tolerance_pp: float
    sharpe_band: tuple[float, float]
    paper_exhibit_8: dict[str, float]
    paper_tolerance_pp: float
    min_return_risk_rank_correlation: float


def load_validation_settings(config: Config, path: Path | str | None = None) -> ValidationSettings:
    path = Path(path) if path is not None else config.config_dir / "cma_validation.yaml"
    settings = ValidationSettings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    groups = {a.group for a in config.universe.assets}
    missing = sorted(groups - set(settings.plausible_pct))
    unknown = sorted(set(settings.paper_exhibit_8) - {a.id for a in config.universe.assets})
    if missing or unknown:
        raise ValueError(
            f"cma_validation.yaml: no plausible range for {missing}; unknown assets {unknown}"
        )
    return settings


@dataclass(frozen=True)
class Check:
    name: str
    status: Status
    detail: str


@dataclass
class AssetValidation:
    asset_id: str
    group: str
    estimate_pct: float
    source: str  # "judge" or "auto_blend"
    volatility_pct: float
    method_range: tuple[float, float]
    checks: list[Check] = field(default_factory=list)

    @property
    def status(self) -> Status:
        states = {c.status for c in self.checks}
        if Status.FAIL in states:
            return Status.FAIL
        return Status.WARN if Status.WARN in states else Status.PASS


@dataclass
class CmaValidation:
    assets: dict[str, AssetValidation]
    cross_section: list[Check]

    @property
    def status(self) -> Status:
        states = {a.status for a in self.assets.values()} | {c.status for c in self.cross_section}
        if Status.FAIL in states:
            return Status.FAIL
        return Status.WARN if Status.WARN in states else Status.PASS


def _available(methods, method_id: CmaMethodId):
    return next(
        (m for m in methods if m.method is method_id and m.unavailable_reason is None), None
    )


def _estimate(methods, method_id: CmaMethodId) -> float | None:
    m = _available(methods, method_id)
    return m.expected_return_pct if m else None


def _component(methods, method_id: CmaMethodId, key: str) -> float | None:
    m = _available(methods, method_id)
    return m.components.get(key) if m else None


def validate_asset(
    asset_id: str, group: str, methods_body, cma_body, settings: ValidationSettings
) -> AssetValidation:
    methods = methods_body.methods
    if cma_body is not None:
        estimate, source = cma_body.expected_return_pct, "judge"
    else:
        estimate, source = _estimate(methods, CmaMethodId.AUTO_BLEND), "auto_blend"
    out = AssetValidation(
        asset_id=asset_id,
        group=group,
        estimate_pct=float(estimate),
        source=source,
        volatility_pct=methods_body.volatility_pct,
        method_range=methods_body.method_range,
    )

    low, high = settings.plausible_pct[group]
    inside = low <= out.estimate_pct <= high
    out.checks.append(
        Check(
            "plausible range",
            Status.PASS if inside else Status.FAIL,
            f"{out.estimate_pct:.2f}% vs [{low:g}, {high:g}] for {group}",
        )
    )

    yield_estimate = _estimate(methods, CmaMethodId.YIELD_BUILDING_BLOCK)
    if yield_estimate is not None:
        gap = out.estimate_pct - yield_estimate
        ok = abs(gap) <= settings.yield_anchor_tolerance_pp
        out.checks.append(
            Check(
                "yield anchor",
                Status.PASS if ok else Status.WARN,
                f"{gap:+.2f}pp from the yield building block ({yield_estimate:.2f}%)",
            )
        )

    risk_free = _component(methods, CmaMethodId.HISTORICAL_ERP, "risk_free_pct")
    if risk_free is not None and out.volatility_pct > 1.0:  # cash's ratio is noise
        sharpe = (out.estimate_pct - risk_free) / out.volatility_pct
        lo, hi = settings.sharpe_band
        out.checks.append(
            Check(
                "implied Sharpe",
                Status.PASS if lo <= sharpe <= hi else Status.WARN,
                f"{sharpe:.2f} at {out.volatility_pct:.1f}% volatility, T-bill {risk_free:.2f}%",
            )
        )

    paper = settings.paper_exhibit_8.get(asset_id)
    if paper is not None:
        gap = out.estimate_pct - paper
        ok = abs(gap) <= settings.paper_tolerance_pp
        out.checks.append(
            Check(
                "paper Exhibit 8",
                Status.PASS if ok else Status.WARN,
                f"{gap:+.2f}pp from the paper's judge value {paper:.1f}% (March 2026)",
            )
        )
    return out


def validate_cross_section(
    assets: dict[str, AssetValidation], settings: ValidationSettings
) -> list[Check]:
    frame = pd.DataFrame(
        {a: (v.estimate_pct, v.volatility_pct) for a, v in assets.items()},
        index=["estimate", "volatility"],
    ).T
    checks = []
    if len(frame) >= 3:
        rho = float(frame["estimate"].rank().corr(frame["volatility"].rank()))
        ok = rho >= settings.min_return_risk_rank_correlation
        checks.append(
            Check(
                "return rises with risk",
                Status.PASS if ok else Status.WARN,
                f"rank correlation {rho:.2f} across {len(frame)} assets "
                f"(minimum {settings.min_return_risk_rank_correlation:g})",
            )
        )
    if "cash" in frame.index:
        beaten = frame.index[frame["estimate"] < frame.loc["cash", "estimate"] - 1e-9].tolist()
        risky = [
            a for a in beaten if frame.loc[a, "volatility"] > 2 * frame.loc["cash", "volatility"]
        ]
        checks.append(
            Check(
                "risky assets beat cash",
                Status.WARN if risky else Status.PASS,
                f"below cash: {', '.join(risky)}" if risky else "every risky asset is above cash",
            )
        )
    return checks


def validate_run(
    run: RunContext, config: Config, settings: ValidationSettings | None = None
) -> CmaValidation:
    settings = settings or load_validation_settings(config)
    assets: dict[str, AssetValidation] = {}
    for asset in config.universe.assets:
        methods_path = run.path("cma_methods", asset_id=asset.id)
        if not methods_path.exists():
            raise FileNotFoundError(
                f"{methods_path} not found; run `uv run saa-skill cma-methods --run-id "
                f"{run.run_id}` first"
            )
        cma_path = run.path("cma", asset_id=asset.id)
        assets[asset.id] = validate_asset(
            asset.id,
            asset.group,
            read("cma_methods", methods_path).body,
            read("cma", cma_path).body if cma_path.exists() else None,
            settings,
        )
    return CmaValidation(assets=assets, cross_section=validate_cross_section(assets, settings))


_MARK = {Status.PASS: "pass", Status.WARN: "WARN", Status.FAIL: "FAIL"}


def render_report(result: CmaValidation, as_of) -> str:
    sources = {a.source for a in result.assets.values()}
    lines = [
        f"# CMA validation as of {as_of}",
        "",
        f"Overall: **{_MARK[result.status]}**. Estimates checked: "
        + ("judged CMAs" if sources == {"judge"} else "auto-blend where the judge has not run")
        + ". Ranges: `config/cma_validation.yaml`.",
        "",
        "| asset | estimate % | source | vol % | candidate range | status | warnings |",
        "|---|---|---|---|---|---|---|",
    ]
    for a in result.assets.values():
        issues = "; ".join(f"{c.name}: {c.detail}" for c in a.checks if c.status is not Status.PASS)
        lines.append(
            f"| {a.asset_id} | {a.estimate_pct:.2f} | {a.source} | {a.volatility_pct:.1f} | "
            f"{a.method_range[0]:.1f}-{a.method_range[1]:.1f} | {_MARK[a.status]} | "
            f"{issues or '-'} |"
        )
    lines += ["", "## Cross-section", ""]
    lines += [f"- **{c.name}** ({_MARK[c.status]}): {c.detail}" for c in result.cross_section]
    lines += ["", "## Every check", ""]
    for a in result.assets.values():
        lines.append(
            f"- **{a.asset_id}**: "
            + "; ".join(f"{c.name} {_MARK[c.status]} ({c.detail})" for c in a.checks)
        )
    return "\n".join(lines) + "\n"


def write_report(result: CmaValidation, run: RunContext) -> Path:
    return run.write_report(render_report(result, run.as_of), REPORT)


def summary_counts(result: CmaValidation) -> dict[str, int]:
    counts = {s.value: 0 for s in Status}
    for a in result.assets.values():
        counts[a.status.value] += 1
    return counts


__all__ = [
    "AssetValidation",
    "Check",
    "CmaValidation",
    "Status",
    "ValidationSettings",
    "load_validation_settings",
    "render_report",
    "summary_counts",
    "validate_asset",
    "validate_cross_section",
    "validate_run",
    "write_report",
]

"""Bull, base and bear returns per asset, from the CMA candidate range (Exhibit 3 step 8).

Deterministic: the bounds are the extreme available candidates and the base is the judge's own
estimate, so this skill reads two contracts and does arithmetic. The narratives name the method
that sits at each end, because "the bear case is 3.63%" is useless without "because the
CAPE-implied ERP says so".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from saa.contracts.asset_class import (
    CMA_CONTRACT,
    METHODS_CONTRACT,
    SCENARIOS_CONTRACT,
    CmaBody,
    CmaMethodEstimate,
    CmaMethodsBody,
    Scenario,
    ScenariosBody,
)
from saa.contracts.base import InputRef, Producer
from saa.contracts.registry import read
from saa.run import RunContext

REPORT = "scenarios.md"


@dataclass(frozen=True)
class AssetScenarios:
    asset_id: str
    body: ScenariosBody
    n_available: int
    bear_method: str
    bull_method: str
    base_selection: str

    @property
    def spread_pct(self) -> float:
        by_name = {s.name: s.expected_return_pct for s in self.body.scenarios}
        return by_name["bull"] - by_name["bear"]


@dataclass
class ScenariosResult:
    assets: dict[str, AssetScenarios] = field(default_factory=dict)
    inputs: list[InputRef] = field(default_factory=list)


def _label(method: CmaMethodEstimate) -> str:
    return method.method.value


def build_scenarios(methods: CmaMethodsBody, cma: CmaBody) -> AssetScenarios:
    """Three scenarios for one asset. Raises if the two contracts disagree about the asset."""
    if methods.asset_id != cma.asset_id:
        raise ValueError(f"asset mismatch: {methods.asset_id!r} vs {cma.asset_id!r}")

    available = [m for m in methods.available if m.expected_return_pct is not None]
    if not available:
        raise ValueError(f"{methods.asset_id}: no available candidate carries an estimate")

    low = min(available, key=lambda m: m.expected_return_pct)
    high = max(available, key=lambda m: m.expected_return_pct)
    base = cma.expected_return_pct
    selection = cma.judgment.selection.value

    # A single available method collapses the range onto a point. Say so rather than publish
    # three identical numbers as if they were a range.
    degenerate = len(available) == 1 or high.expected_return_pct == low.expected_return_pct
    span = "The candidates do not disagree, so there is no range to report: " if degenerate else ""

    scenarios = [
        Scenario(
            name="bear",
            expected_return_pct=low.expected_return_pct,
            narrative=(
                f"{span}the most pessimistic available candidate is `{_label(low)}` at "
                f"{low.expected_return_pct:.2f}%, {low.expected_return_pct - base:+.2f}pp "
                f"against the judged estimate. {low.rationale}"
            ),
        ),
        Scenario(
            name="base",
            expected_return_pct=base,
            narrative=(
                f"The judge's estimate, {base:.2f}%, by {selection.replace('_', ' ')} across "
                f"{len(available)} available candidates. This is the recommendation and the "
                f"number every downstream agent consumes."
            ),
        ),
        Scenario(
            name="bull",
            expected_return_pct=high.expected_return_pct,
            narrative=(
                f"{span}the most optimistic available candidate is `{_label(high)}` at "
                f"{high.expected_return_pct:.2f}%, {high.expected_return_pct - base:+.2f}pp "
                f"against the judged estimate. {high.rationale}"
            ),
        ),
    ]
    return AssetScenarios(
        asset_id=cma.asset_id,
        body=ScenariosBody(asset_id=cma.asset_id, scenarios=scenarios),
        n_available=len(available),
        bear_method=_label(low),
        bull_method=_label(high),
        base_selection=selection,
    )


def run_scenarios(run: RunContext, assets: list[str] | None = None) -> ScenariosResult:
    """Read each asset's methods and judged CMA from the run, and build its scenarios."""
    result = ScenariosResult()
    ids = assets or sorted(p.name for p in (run.root / "cma").iterdir() if p.is_dir())
    for asset_id in ids:
        methods_path = run.path(METHODS_CONTRACT, asset_id=asset_id)
        cma_path = run.path(CMA_CONTRACT, asset_id=asset_id)
        if not methods_path.exists() or not cma_path.exists():
            raise FileNotFoundError(
                f"{asset_id}: scenarios need both {methods_path.name} and {cma_path.name}; "
                "run `saa-skill cma-methods` and `saa-agent cma-judge` first"
            )
        methods = read(METHODS_CONTRACT, methods_path).body
        cma = read(CMA_CONTRACT, cma_path).body
        result.assets[asset_id] = build_scenarios(methods, cma)
        result.inputs.extend(
            [
                InputRef(contract=METHODS_CONTRACT, path=run.relative(methods_path)),
                InputRef(contract=CMA_CONTRACT, path=run.relative(cma_path)),
            ]
        )
    return result


def render_report(result: ScenariosResult) -> str:
    """One table, widest range first: the spread is the point of the report."""
    lines = [
        "# Scenarios",
        "",
        'Exhibit 3 step 8: "Scenario analysis (bull/bear from method range)". The bounds are the',
        "extreme available candidates, the base is the judge's estimate. The spread is the",
        "methodological disagreement the judge resolved, not a stress test.",
        "",
        "| Asset | Bear | Base | Bull | Spread | Bear method | Bull method | Candidates |",
        "|---|---:|---:|---:|---:|---|---|---:|",
    ]
    for a in sorted(result.assets.values(), key=lambda a: -a.spread_pct):
        by_name = {s.name: s.expected_return_pct for s in a.body.scenarios}
        lines.append(
            f"| {a.asset_id} | {by_name['bear']:.2f}% | {by_name['base']:.2f}% | "
            f"{by_name['bull']:.2f}% | {a.spread_pct:.2f}pp | `{a.bear_method}` | "
            f"`{a.bull_method}` | {a.n_available} |"
        )
    if result.assets:
        widest = max(result.assets.values(), key=lambda a: a.spread_pct)
        narrowest = min(result.assets.values(), key=lambda a: a.spread_pct)
        lines += [
            "",
            f"Widest: **{widest.asset_id}** at {widest.spread_pct:.2f}pp. "
            f"Narrowest: **{narrowest.asset_id}** at {narrowest.spread_pct:.2f}pp. "
            "A point estimate carries very different weight across that difference.",
        ]
    return "\n".join(lines) + "\n"


def write_outputs(result: ScenariosResult, run: RunContext) -> list[Path]:
    """Write ``cma/<asset>/scenarios.json`` per asset and ``reports/scenarios.md``."""
    report = run.write_report(render_report(result), REPORT)
    written = [report]
    for asset_id, scenarios in result.assets.items():
        written.append(
            run.write(
                SCENARIOS_CONTRACT,
                asset_id.replace("_", "-"),
                scenarios.body,
                produced_by=Producer.SCRIPT,
                asset_id=asset_id,
                inputs=result.inputs,
                report_path=report,
            )
        )
    return written

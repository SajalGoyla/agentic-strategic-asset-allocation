"""Scenarios skill: bull, base and bear per asset, from the CMA candidate range (Exhibit 3)."""

from saa.skills.scenarios.analysis import (
    REPORT,
    AssetScenarios,
    ScenariosResult,
    build_scenarios,
    render_report,
    run_scenarios,
    write_outputs,
)

__all__ = [
    "REPORT",
    "AssetScenarios",
    "ScenariosResult",
    "build_scenarios",
    "render_report",
    "run_scenarios",
    "write_outputs",
]

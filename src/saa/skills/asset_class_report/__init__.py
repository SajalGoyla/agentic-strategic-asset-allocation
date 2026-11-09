"""Asset-class report skill: the 13-section investment case per asset (Exhibit 3)."""

from saa.skills.asset_class_report.report import (
    ASSET_REPORT,
    N_SECTIONS,
    REPORT,
    AssetCase,
    CaseInputs,
    ReportsResult,
    key_considerations,
    load_case_inputs,
    render_case,
    render_index,
    run_reports,
    write_outputs,
)

__all__ = [
    "ASSET_REPORT",
    "N_SECTIONS",
    "REPORT",
    "AssetCase",
    "CaseInputs",
    "ReportsResult",
    "key_considerations",
    "load_case_inputs",
    "render_case",
    "render_index",
    "run_reports",
    "write_outputs",
]

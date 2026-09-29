"""CMA-methods skill: the candidate expected returns per asset (Exhibit 4), as cma_methods.json."""

from saa.skills.cma_methods.analysis import (
    REPORT,
    CmaMethodsResult,
    gather_inputs,
    render_report,
    run_cma_methods,
    write_outputs,
)
from saa.skills.cma_methods.methods import MarketInputs, Unavailable, run_methods
from saa.skills.cma_methods.settings import CmaSettings, load_cma_settings

__all__ = [
    "REPORT",
    "CmaMethodsResult",
    "CmaSettings",
    "MarketInputs",
    "Unavailable",
    "gather_inputs",
    "load_cma_settings",
    "render_report",
    "run_cma_methods",
    "run_methods",
    "write_outputs",
]

"""Signals skill: asset-level macro, technical and valuation signals (Exhibit 3, Exhibit 4)."""

from saa.skills.signals.analysis import (
    AGENT,
    REPORT,
    AssetSignals,
    SignalsResult,
    composite,
    render_report,
    run_signals,
    score_against_history,
    write_outputs,
)
from saa.skills.signals.settings import SignalSettings, load_signal_settings

__all__ = [
    "AGENT",
    "REPORT",
    "AssetSignals",
    "SignalSettings",
    "SignalsResult",
    "composite",
    "load_signal_settings",
    "render_report",
    "run_signals",
    "score_against_history",
    "write_outputs",
]

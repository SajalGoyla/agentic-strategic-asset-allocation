"""Historical-analysis skill: return, risk, drawdown and correlation statistics per asset.

Writes the shared ``historical_stats`` and ``correlation_row`` contracts; the models live in
``saa.contracts.asset_class``, not here.
"""

from saa.skills.historical_analysis.analysis import (
    AGENT,
    AnalysisSettings,
    HistoricalAnalysis,
    StockBondCorrelation,
    render_asset_report,
    render_summary,
    run_historical_analysis,
    write_outputs,
)

__all__ = [
    "AGENT",
    "AnalysisSettings",
    "HistoricalAnalysis",
    "StockBondCorrelation",
    "render_asset_report",
    "render_summary",
    "run_historical_analysis",
    "write_outputs",
]

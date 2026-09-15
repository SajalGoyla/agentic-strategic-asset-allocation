"""Historical-analysis skill: return, risk, drawdown and correlation statistics per asset."""

from saa.skills.historical_analysis.analysis import (
    AnalysisSettings,
    render_summary,
    run_historical_analysis,
    write_outputs,
)
from saa.skills.historical_analysis.models import (
    AssetHistoricalStats,
    CorrelationRow,
    HistoricalAnalysis,
    WindowStats,
)

__all__ = [
    "AnalysisSettings",
    "AssetHistoricalStats",
    "CorrelationRow",
    "HistoricalAnalysis",
    "WindowStats",
    "render_summary",
    "run_historical_analysis",
    "write_outputs",
]

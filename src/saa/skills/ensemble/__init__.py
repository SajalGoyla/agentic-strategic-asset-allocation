"""Ensemble skill: the CIO's combination techniques and their diagnostics (§3.6, §4.4)."""

from saa.skills.ensemble.ensembles import (
    Ensemble,
    EnsembleInputs,
    backtest_sharpe_weighted,
    build_ensembles,
    composite_score_weighted,
    default_choice,
    ensemble_score,
    evaluate,
    inverse_tracking_error,
    meta_optimization,
    project_to_policy,
    regime_conditional,
    simple_average,
    single_method,
    trimmed_mean,
)

__all__ = [
    "Ensemble",
    "EnsembleInputs",
    "backtest_sharpe_weighted",
    "build_ensembles",
    "composite_score_weighted",
    "default_choice",
    "ensemble_score",
    "evaluate",
    "project_to_policy",
    "inverse_tracking_error",
    "meta_optimization",
    "regime_conditional",
    "simple_average",
    "single_method",
    "trimmed_mean",
]

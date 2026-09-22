"""Macro regime skill: the four-dimension scoring framework (Ang et al. 2026 §3.2).

Methodology in ``SKILL.md``, computation in ``scoring.py``. Deterministic throughout -- the
macro agent calls this, then reasons about the result.
"""

from saa.skills.macro_regime.scoring import (
    ScorePanel,
    apply_transform,
    classify,
    score_history,
    to_dimension_scores,
    to_pit_quality,
    to_score,
)

__all__ = [
    "ScorePanel",
    "apply_transform",
    "classify",
    "score_history",
    "to_dimension_scores",
    "to_pit_quality",
    "to_score",
]

"""Voting skill: the modified Borda tally, the metric blend and the diversity rule (§3.5)."""

from saa.skills.voting.tally import (
    CANONICAL,
    Tally,
    VotingSettings,
    borda_points,
    enforce_diversity,
    load_voting_settings,
    render_report,
    tally,
)

__all__ = [
    "CANONICAL",
    "Tally",
    "VotingSettings",
    "borda_points",
    "enforce_diversity",
    "load_voting_settings",
    "render_report",
    "tally",
]

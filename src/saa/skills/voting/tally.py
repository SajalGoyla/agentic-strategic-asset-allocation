"""The modified Borda tally, the metric blend and the diversity rule (Ang et al. 2026 §3.5).

"Voting follows a modified Borda count. Each agent submits a top-five ranking (awarding 5, 4, 3,
2, and 1 points) and a bottom flag (-2 points), excluding itself ... The vote totals are then
blended with a quantitative metric score ... using a regime-dependent weight ... A diversity
constraint requires the top-five shortlist to include representation from at least three of
the four families, preventing a single philosophical school from monopolizing the
recommendation set."

Pure arithmetic over the ballots and the six-dimension metric scores; the ballots themselves
come from ``agents/vote``. Exhibit 9's composite runs from 1.000 to 0.000, so the blend is
rescaled the same way.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from saa.config import Config
from saa.contracts.cio import MethodScore
from saa.contracts.portfolio import PcCategory, PcProposalBody
from saa.contracts.review import TOP_N, TallyRow, VoteBody, VoteTallyBody

CANONICAL = {
    PcCategory.HEURISTIC,
    PcCategory.RETURN_OPTIMIZED,
    PcCategory.RISK_STRUCTURED,
    PcCategory.NON_TRADITIONAL,
}


class VotingSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vote_weight: dict[str, float]
    min_families: int = Field(ge=1, le=4)
    dissent_share: float = Field(gt=0.0, le=1.0)
    own_family_bonus: float = Field(ge=0.0)

    def weight_for(self, regime: str | None) -> float:
        weight = self.vote_weight.get(regime or "", self.vote_weight.get("default", 0.5))
        if not 0.0 <= weight <= 1.0:
            raise ValueError(f"vote weight for {regime!r} is {weight}; it must be in [0, 1]")
        return weight


def load_voting_settings(config: Config, path: Path | str | None = None) -> VotingSettings:
    path = Path(path) if path is not None else config.config_dir / "voting.yaml"
    return VotingSettings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def _minmax(values: dict[str, float]) -> dict[str, float]:
    lo, hi = min(values.values()), max(values.values())
    if hi - lo < 1e-12:
        return {k: 0.5 for k in values}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def borda_points(ballots: list[VoteBody], candidates: list[str]) -> dict[str, int]:
    """Total points per candidate; one with no mention on any ballot scores 0."""
    points = {c: 0 for c in candidates}
    for ballot in ballots:
        for agent_id, p in ballot.points().items():
            if agent_id not in points:
                raise ValueError(f"{ballot.voter_agent_id} voted for unknown agent {agent_id}")
            points[agent_id] += p
    return points


def enforce_diversity(
    ranked: list[str], categories: dict[str, PcCategory], *, min_families: int
) -> tuple[list[str], list[str]]:
    """The top ``TOP_N`` of ``ranked``, adjusted until it spans ``min_families`` canonical
    families. Returns the shortlist and a note per substitution.

    Each pass swaps out the lowest-ranked shortlist member whose family is represented more than
    once, for the highest-ranked candidate from a family not on the shortlist. So the vote's
    order is kept as far as the rule allows, and every departure from it is recorded.
    """
    available = {categories[a] for a in ranked} & CANONICAL
    if len(available) < min_families:
        raise ValueError(
            f"the field spans {len(available)} canonical families; the diversity rule needs "
            f"{min_families}"
        )
    shortlist = ranked[:TOP_N]
    notes: list[str] = []

    def families(items: list[str]) -> set[PcCategory]:
        return {categories[a] for a in items} & CANONICAL

    while len(families(shortlist)) < min_families:
        counts = Counter(categories[a] for a in shortlist)
        out = next(
            a
            for a in reversed(shortlist)
            if categories[a] not in CANONICAL or counts[categories[a]] > 1
        )
        present = families(shortlist)
        incoming = next(
            a
            for a in ranked
            if a not in shortlist and categories[a] in CANONICAL and categories[a] not in present
        )
        shortlist = [incoming if a == out else a for a in shortlist]
        notes.append(
            f"{incoming} ({categories[incoming].value}, rank {ranked.index(incoming) + 1}) "
            f"replaces {out} ({categories[out].value}, rank {ranked.index(out) + 1}) so the "
            f"shortlist spans {min_families} families"
        )
    # Keep the shortlist in vote order.
    return sorted(shortlist, key=ranked.index), notes


@dataclass
class Tally:
    body: VoteTallyBody
    diversity_notes: list[str]
    dissent: dict[str, int]  # bottom-flagged candidates at or over the dissent share -> flags
    ballots: int
    blended: dict[str, float] = field(default_factory=dict)


def tally(
    ballots: list[VoteBody],
    proposals: dict[str, PcProposalBody],
    scores: dict[str, MethodScore],
    settings: VotingSettings,
    *,
    regime: str | None,
) -> Tally:
    """Blend the Borda points with the metric score, rank, and pick a diverse shortlist."""
    candidates = sorted(proposals)
    missing = sorted(set(candidates) - set(scores))
    if missing:
        raise ValueError(f"no metric score for {missing}")
    if not ballots:
        raise ValueError("no ballots to tally")

    points = borda_points(ballots, candidates)
    vote_norm = _minmax({k: float(v) for k, v in points.items()})
    metric = {k: scores[k].composite for k in candidates}
    w = settings.weight_for(regime)
    blended = {k: w * vote_norm[k] + (1.0 - w) * metric[k] for k in candidates}
    composite = _minmax(blended)
    ranked = sorted(candidates, key=lambda k: (-blended[k], -metric[k], k))

    categories = {k: proposals[k].category for k in candidates}
    shortlist, notes = enforce_diversity(ranked, categories, min_families=settings.min_families)
    rows = [
        TallyRow(
            agent_id=k,
            method=proposals[k].method,
            category=categories[k],
            vote_points=points[k],
            metric_score=round(metric[k], 6),
            composite=round(composite[k], 6),
            rank=ranked.index(k) + 1,
        )
        for k in ranked
    ]
    body = VoteTallyBody(
        rows=rows,
        shortlist=shortlist,
        regime=regime or "unknown",
        vote_weight=w,
        metric_weight=1.0 - w,
        diversity_categories=len({categories[a] for a in shortlist} & CANONICAL),
    )
    flags = Counter(b.bottom_flag for b in ballots if b.bottom_flag)
    dissent = {k: n for k, n in sorted(flags.items()) if n / len(ballots) >= settings.dissent_share}
    return Tally(
        body=body, diversity_notes=notes, dissent=dissent, ballots=len(ballots), blended=blended
    )


def render_report(result: Tally) -> str:
    b = result.body
    lines = [
        "# Vote tally",
        "",
        f"{result.ballots} ballots. Regime **{b.regime}**: vote weight {b.vote_weight:.2f}, "
        f"metric weight {b.metric_weight:.2f}. Composite rescaled 1.000 (top) to 0.000 "
        "(bottom), as Exhibit 9.",
        "",
        "| rank | agent | family | vote points | metric | composite | shortlist |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in b.rows:
        mark = "yes" if r.agent_id in b.shortlist else ""
        lines.append(
            f"| {r.rank} | {r.agent_id} | {r.category.value} | {r.vote_points} | "
            f"{r.metric_score:.3f} | {r.composite:.3f} | {mark} |"
        )
    lines += [
        "",
        f"Shortlist ({b.diversity_categories} of 4 families): " + ", ".join(b.shortlist) + ".",
    ]
    if result.diversity_notes:
        lines += ["", "## Diversity rule", ""] + [f"- {n}" for n in result.diversity_notes]
    if result.dissent:
        lines += ["", "## Dissent", ""]
        lines += [
            f"- **{k}** was bottom-flagged on {n} of {result.ballots} ballots."
            for k, n in result.dissent.items()
        ]
    return "\n".join(lines) + "\n"

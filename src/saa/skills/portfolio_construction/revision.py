"""Revising a proposal after the review (Ang et al. 2026 §3.5): the levers, applied.

"The top five ranking PC agents then revise their proposals, taking into account the peer
reviews and the CRO report." A PC agent's weights come from an optimiser, so a revision is
expressed as levers on that portfolio, each the remedy for a critique a review typically makes:

* **exclude assets** -- the portfolio leans on an asset the reviewer believes is mis-estimated;
* **cap any single weight** -- it is too concentrated;
* **shrink toward equal weight** -- it is too sensitive to estimation error (DeMiguel, Garlappi
  and Uppal 2009: 1/N is the portfolio that estimates nothing).

The levers are applied to the method's own portfolio, and the result is held to the IPS's
ex-ante limits exactly as every candidate is (decision 37), with the levers kept as
constraints so the re-solve cannot undo them. A revision changes the portfolio, not the
method: risk parity revised is still risk parity's portfolio, adjusted.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from saa.config import Config
from saa.contracts.portfolio import PcProposalBody
from saa.skills.portfolio_construction.analysis import (
    Candidate,
    StageInputs,
    candidate_from_weights,
    ex_ante_limits,
    portfolio_inputs,
)
from saa.skills.portfolio_construction.methods import (
    ADVERSARIAL,
    METHODS,
    RESEARCH_LIBRARY,
    Method,
    enforce_ex_ante_limits,
)

MAX_SHRINK = 0.5  # beyond half-way to 1/N the revision has become a different method


@dataclass(frozen=True)
class RevisionLevers:
    exclude: tuple[str, ...] = ()
    max_weight: float | None = None  # decimal, e.g. 0.25
    shrink_to_equal: float = 0.0  # 0 = keep the method's weights, 0.5 = half-way to 1/N

    @property
    def changes_anything(self) -> bool:
        return bool(self.exclude) or self.max_weight is not None or self.shrink_to_equal > 0

    def describe(self) -> str:
        parts = []
        if self.exclude:
            parts.append("excluded " + ", ".join(self.exclude))
        if self.max_weight is not None:
            parts.append(f"capped every weight at {self.max_weight:.0%}")
        if self.shrink_to_equal > 0:
            parts.append(f"shrunk {self.shrink_to_equal:.0%} of the way toward equal weight")
        return "; ".join(parts) or "no change"


def method_for(proposal: PcProposalBody) -> Method:
    """The method behind a proposal: by agent id for the registry, by name for the researcher."""
    if proposal.agent_id in METHODS:
        return METHODS[proposal.agent_id]
    if proposal.agent_id == ADVERSARIAL.id:
        return ADVERSARIAL
    for method in RESEARCH_LIBRARY.values():
        if method.name == proposal.method:
            return method
    raise ValueError(f"no method found for {proposal.agent_id} ({proposal.method})")


def _cap(weights: np.ndarray, allowed: np.ndarray, cap: float) -> np.ndarray:
    """Water-fill: clip every weight at ``cap`` and hand the excess to the allowed assets below
    it, in proportion to their weights, until none exceeds it."""
    w = weights.copy()
    for _ in range(len(w)):
        over = w > cap + 1e-12
        if not over.any():
            break
        excess = float((w[over] - cap).sum())
        w[over] = cap
        room = allowed & (w < cap - 1e-12)
        base = w[room].sum()
        if base > 0:
            w[room] += excess * w[room] / base
        else:
            w[room] += excess / room.sum()
    return w


def apply_levers(weights: pd.Series, asset_ids: list[str], levers: RevisionLevers) -> pd.Series:
    """The method's portfolio with the levers applied, before the IPS is re-imposed."""
    unknown = sorted(set(levers.exclude) - set(asset_ids))
    if unknown:
        raise ValueError(f"cannot exclude unknown assets {unknown}")
    if not 0.0 <= levers.shrink_to_equal <= MAX_SHRINK:
        raise ValueError(f"shrink_to_equal must be in [0, {MAX_SHRINK}]")
    allowed = np.array([a not in levers.exclude for a in asset_ids])
    if not allowed.any():
        raise ValueError("a revision cannot exclude every asset")
    if levers.max_weight is not None and levers.max_weight * allowed.sum() < 1.0 - 1e-9:
        raise ValueError(
            f"a {levers.max_weight:.0%} cap over {int(allowed.sum())} assets cannot sum to 100%"
        )

    w = weights.reindex(asset_ids).fillna(0.0).to_numpy(dtype=float)
    w = np.where(allowed, w, 0.0)
    w = w / w.sum() if w.sum() > 0 else allowed / allowed.sum()
    if levers.shrink_to_equal > 0:
        equal = allowed / allowed.sum()
        w = (1.0 - levers.shrink_to_equal) * w + levers.shrink_to_equal * equal
    if levers.max_weight is not None:
        w = _cap(w, allowed, levers.max_weight)
    return pd.Series(w / w.sum(), index=asset_ids, dtype="float64")


def lever_constraints(asset_ids: list[str], levers: RevisionLevers) -> list[dict]:
    """The levers as solver constraints, so re-imposing the IPS band cannot undo them."""
    cons: list[dict] = []
    for i, asset in enumerate(asset_ids):
        if asset in levers.exclude:
            cons.append({"type": "eq", "fun": lambda w, i=i: w[i]})
    if levers.max_weight is not None:
        cap = levers.max_weight
        # One scalar constraint per asset: the IPS re-solve checks each constraint as a number.
        for i in range(len(asset_ids)):
            cons.append({"type": "ineq", "fun": lambda w, i=i: cap - w[i]})
    return cons


def revise(
    proposal: PcProposalBody,
    levers: RevisionLevers,
    stage: StageInputs,
    config: Config,
) -> Candidate:
    """The revised candidate: levers applied, then held to the IPS's ex-ante limits."""
    method = method_for(proposal)
    ids = stage.asset_ids
    target = apply_levers(pd.Series(proposal.weights, dtype="float64"), ids, levers)
    weights, before_band = enforce_ex_ante_limits(
        target,
        portfolio_inputs(stage),
        ex_ante_limits(stage, config),
        objective=None,  # nearest permitted portfolio to the revised one
        constraints=lever_constraints(ids, levers),
    )
    return candidate_from_weights(
        method,
        weights,
        stage,
        config,
        agent=proposal.agent_id,
        unconstrained_volatility_pct=before_band,
    )


def turnover(before: dict[str, float], after: pd.Series) -> float:
    """One-way turnover of the revision, as a fraction: half the sum of absolute weight changes."""
    ids = sorted(set(before) | set(after.index))
    b = pd.Series(before, dtype="float64").reindex(ids).fillna(0.0)
    a = after.reindex(ids).fillna(0.0)
    return float(0.5 * (a - b).abs().sum())

"""Who reviews whom: the randomised peer-review assignment (Ang et al. 2026 §3.5).

"Each PC agent reviews exactly two peers -- one from its own category, which is more likely to
identify technical errors within a shared framework, and one from a different category, which
can challenge foundational assumptions. Assignments are randomized with a recorded seed."

Deterministic given the seed, which is the point: the same run id reproduces the same pairing,
and the seed is written into every review's header so a published result can be re-derived.

Two things the paper leaves to the implementation:

* **Balance.** A free random draw leaves some proposals with four reviews and others with none,
  and an unreviewed proposal still goes to the vote. So each reviewer picks the eligible peer
  with the fewest reviews so far, ties broken by the seeded shuffle. The pairing stays random;
  the load does not.
* **A category of one.** The PC-researcher is its own category (Exhibit 9 lists it as "E:
  PC-Researcher"), so it has no intra-category peer and no amount of shuffling will find one.
  Rather than drop its second review, it does a second inter-category review and the
  substitution is recorded in ``fallbacks`` -- it belongs in the audit trail, not in a silent
  branch (decision 35).
"""

from __future__ import annotations

import hashlib
import logging
import random
from collections import Counter
from dataclasses import dataclass, field

from saa.contracts import PcCategory, ReviewKind

log = logging.getLogger(__name__)

SKILL = "peer-review"

# §3.5: "reviews exactly two peers".
REVIEWS_PER_AGENT = 2
# Two reviewers per proposal is what the roster supports; below it a proposal goes to the vote
# unexamined, which the balancing exists to prevent.
MIN_REVIEWS_PER_PROPOSAL = 1


@dataclass(frozen=True)
class Assignment:
    """One review to be written: who reviews whom, and under which framing."""

    reviewer: str
    reviewer_category: PcCategory
    reviewed: str
    reviewed_category: PcCategory
    kind: ReviewKind

    @property
    def pair(self) -> tuple[str, str]:
        return (self.reviewer, self.reviewed)


@dataclass(frozen=True)
class AssignmentPlan:
    """Every review in one run, plus the seed that produced it."""

    seed: int
    assignments: list[Assignment]
    # agent id -> why it could not be given the review kind the protocol asks for.
    fallbacks: dict[str, str] = field(default_factory=dict)

    def for_reviewer(self, agent_id: str) -> list[Assignment]:
        return [a for a in self.assignments if a.reviewer == agent_id]

    def for_reviewed(self, agent_id: str) -> list[Assignment]:
        return [a for a in self.assignments if a.reviewed == agent_id]

    @property
    def review_counts(self) -> dict[str, int]:
        """Reviews each proposal will receive."""
        counts = Counter(a.reviewed for a in self.assignments)
        return {agent_id: counts.get(agent_id, 0) for agent_id in self.reviewers}

    @property
    def reviewers(self) -> list[str]:
        return sorted({a.reviewer for a in self.assignments})

    def counts_by_kind(self) -> dict[str, int]:
        counts = Counter(a.kind.value for a in self.assignments)
        return {kind.value: counts.get(kind.value, 0) for kind in ReviewKind}


def seed_for(run_id: str) -> int:
    """A stable seed derived from the run id, so a run's pairing is reproducible from its name.

    §3.5 asks only that the seed be recorded. Deriving it from the run id means a reader who
    has the run id can reproduce the assignment without being handed a separate number, and an
    explicit ``--seed`` still overrides it.
    """
    return int(hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:8], 16)


def assign_reviews(
    categories: dict[str, PcCategory], *, seed: int, reviews_per_agent: int = REVIEWS_PER_AGENT
) -> AssignmentPlan:
    """Pair every agent with one intra-category and one inter-category peer to review.

    ``categories`` maps agent id to its Exhibit 5 family -- normally taken from the proposals
    the run actually produced, not the static roster, so a method that failed to run is not
    assigned a reviewer.
    """
    if len(categories) < reviews_per_agent + 1:
        raise ValueError(
            f"{len(categories)} agents cannot each review {reviews_per_agent} peers; "
            f"at least {reviews_per_agent + 1} are needed"
        )

    rng = random.Random(seed)
    order = sorted(categories)
    rng.shuffle(order)

    received: Counter[str] = Counter()
    assignments: list[Assignment] = []
    taken: set[tuple[str, str]] = set()
    fallbacks: dict[str, str] = {}

    def eligible(reviewer: str, kind: ReviewKind) -> list[str]:
        same = categories[reviewer]
        # Sorted before the shuffle, so the seed alone decides the pairing. Without it the
        # order the proposals happened to be read off disk would leak into the result, and the
        # recorded seed would no longer reproduce the run.
        peers = sorted(
            peer
            for peer, category in categories.items()
            if peer != reviewer
            and (category == same if kind is ReviewKind.INTRA_CATEGORY else category != same)
            and (reviewer, peer) not in taken
        )
        rng.shuffle(peers)
        return peers

    def take(reviewer: str, kind: ReviewKind) -> bool:
        peers = eligible(reviewer, kind)
        if not peers:
            return False
        # min() is stable, so it returns the first of the least-reviewed peers in shuffled order.
        reviewed = min(peers, key=lambda peer: received[peer])
        assignments.append(
            Assignment(
                reviewer=reviewer,
                reviewer_category=categories[reviewer],
                reviewed=reviewed,
                reviewed_category=categories[reviewed],
                kind=kind,
            )
        )
        taken.add((reviewer, reviewed))
        received[reviewed] += 1
        return True

    # Intra-category first: it has the fewest candidates, so it is assigned while the load is
    # still even and the inter-category pass can even it out afterwards.
    for reviewer in order:
        if not take(reviewer, ReviewKind.INTRA_CATEGORY):
            fallbacks[reviewer] = (
                f"{categories[reviewer].value} has no other member in this run, so the "
                "intra-category review is substituted with a second inter-category review"
            )
    for reviewer in order:
        if not take(reviewer, ReviewKind.INTER_CATEGORY):
            raise ValueError(
                f"{reviewer} has no peer outside {categories[reviewer].value} to review"
            )
    # Make up the shortfall for anyone whose category had no second member.
    for reviewer in order:
        while len([a for a in assignments if a.reviewer == reviewer]) < reviews_per_agent and take(
            reviewer, ReviewKind.INTER_CATEGORY
        ):
            pass

    plan = AssignmentPlan(seed=seed, assignments=assignments, fallbacks=fallbacks)
    validate_plan(plan, categories, reviews_per_agent=reviews_per_agent)
    return plan


def validate_plan(
    plan: AssignmentPlan,
    categories: dict[str, PcCategory],
    *,
    reviews_per_agent: int = REVIEWS_PER_AGENT,
) -> None:
    """Fail loudly on anything the protocol forbids, rather than on read in the review stage."""
    for assignment in plan.assignments:
        if assignment.reviewer == assignment.reviewed:
            raise ValueError(f"{assignment.reviewer} was assigned to review itself")
        same = assignment.reviewer_category == assignment.reviewed_category
        expected = ReviewKind.INTRA_CATEGORY if same else ReviewKind.INTER_CATEGORY
        if assignment.kind is not expected:
            raise ValueError(
                f"{assignment.reviewer} -> {assignment.reviewed} is marked "
                f"{assignment.kind.value} but the categories say {expected.value}"
            )

    pairs = [a.pair for a in plan.assignments]
    if len(set(pairs)) != len(pairs):
        duplicates = sorted({p for p in pairs if pairs.count(p) > 1})
        raise ValueError(f"the same review was assigned twice: {duplicates}")

    for agent_id in categories:
        written = len(plan.for_reviewer(agent_id))
        if written != reviews_per_agent:
            raise ValueError(
                f"{agent_id} was assigned {written} reviews; §3.5 requires exactly "
                f"{reviews_per_agent}"
            )

    thin = {a: n for a, n in plan.review_counts.items() if n < MIN_REVIEWS_PER_PROPOSAL}
    if thin:
        raise ValueError(f"these proposals would go to the vote unreviewed: {sorted(thin)}")


# --------------------------------------------------------------------------------- report
def render_report(plan: AssignmentPlan, *, as_of=None, run_id: str | None = None) -> str:
    """Markdown for human review (§3.2), and the record of the seed the pairing used."""
    counts = plan.review_counts
    lines = [
        "# Peer-Review Assignments",
        "",
        (f"As of {as_of}. " if as_of else "")
        + (f"Run `{run_id}`. " if run_id else "")
        + f"Seed **{plan.seed}**.",
        "",
        f"{len(plan.assignments)} reviews across {len(plan.reviewers)} agents: "
        + ", ".join(f"{n} {kind}" for kind, n in plan.counts_by_kind().items())
        + ".",
        "",
        "§3.5: each agent reviews exactly two peers, one from its own category and one from "
        "another. The pairing is random; the seed above reproduces it.",
        "",
        "| reviewer | category | reviews | kind |",
        "|---|---|---|---|",
    ]
    for assignment in sorted(plan.assignments, key=lambda a: (a.reviewer, a.kind.value)):
        lines.append(
            f"| {assignment.reviewer} | {assignment.reviewer_category.value} | "
            f"{assignment.reviewed} | {assignment.kind.value.replace('_', '-')} |"
        )

    lines += ["", "## Reviews received per proposal", "", "| proposal | reviews |", "|---|---|"]
    for agent_id in sorted(counts, key=lambda a: (-counts[a], a)):
        lines.append(f"| {agent_id} | {counts[agent_id]} |")

    if plan.fallbacks:
        lines += ["", "## Substitutions", ""]
        lines += [f"- **{agent}**: {why}" for agent, why in sorted(plan.fallbacks.items())]
    return "\n".join(lines) + "\n"

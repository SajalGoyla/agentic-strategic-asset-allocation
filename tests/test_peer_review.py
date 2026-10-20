"""The peer-review pairing and the review prompts (§3.5)."""

import pandas as pd
import pytest

from saa.contracts import PcCategory, PcProposalBody, ReviewKind
from saa.contracts.base import IpsCompliance
from saa.skills.peer_review import (
    REVIEW_FRAMING,
    REVIEWS_PER_AGENT,
    Assignment,
    AssignmentPlan,
    assign_reviews,
    render_report,
    render_review_prompt,
    seed_for,
    validate_plan,
)

H, R, K, N, P = (
    PcCategory.HEURISTIC,
    PcCategory.RETURN_OPTIMIZED,
    PcCategory.RISK_STRUCTURED,
    PcCategory.NON_TRADITIONAL,
    PcCategory.PC_RESEARCHER,
)

# The 15-agent roster as it actually runs (decision 33), including the one-member researcher
# family and the adversarial diversifier.
ROSTER: dict[str, PcCategory] = {
    "equal_weight": H,
    "inverse_volatility": H,
    "inverse_variance": H,
    "market_cap_weight": H,
    "volatility_targeting": H,
    "max_sharpe": R,
    "black_litterman": R,
    "resampled_efficient_frontier": R,
    "risk_parity": K,
    "hierarchical_risk_parity": K,
    "maximum_diversification": K,
    "cvar_minimization": N,
    "tail_risk_parity": N,
    "adversarial_diversifier": N,
    "pc_researcher": P,
}


# ------------------------------------------------------------------------------ the protocol
def test_every_agent_reviews_exactly_two_peers():
    plan = assign_reviews(ROSTER, seed=1)
    assert len(plan.assignments) == len(ROSTER) * REVIEWS_PER_AGENT
    for agent_id in ROSTER:
        assert len(plan.for_reviewer(agent_id)) == REVIEWS_PER_AGENT


def test_each_agent_gets_one_intra_and_one_inter_category_review():
    plan = assign_reviews(ROSTER, seed=1)
    for agent_id in ROSTER:
        kinds = sorted(a.kind.value for a in plan.for_reviewer(agent_id))
        if agent_id in plan.fallbacks:
            continue
        assert kinds == ["inter_category", "intra_category"]


def test_no_agent_reviews_itself():
    plan = assign_reviews(ROSTER, seed=7)
    assert all(a.reviewer != a.reviewed for a in plan.assignments)


def test_the_same_review_is_never_assigned_twice():
    plan = assign_reviews(ROSTER, seed=7)
    pairs = [a.pair for a in plan.assignments]
    assert len(set(pairs)) == len(pairs)


def test_the_kind_follows_from_the_categories_not_from_a_label():
    plan = assign_reviews(ROSTER, seed=3)
    for a in plan.assignments:
        same = a.reviewer_category == a.reviewed_category
        assert a.kind is (ReviewKind.INTRA_CATEGORY if same else ReviewKind.INTER_CATEGORY)


# ---------------------------------------------------------------------------- reproducibility
def test_the_same_seed_reproduces_the_same_pairing():
    """§3.5: "randomized with a recorded seed" -- the record is only worth having if it works."""
    assert (
        assign_reviews(ROSTER, seed=42).assignments == assign_reviews(ROSTER, seed=42).assignments
    )


def test_a_different_seed_gives_a_different_pairing():
    assert (
        assign_reviews(ROSTER, seed=42).assignments != assign_reviews(ROSTER, seed=43).assignments
    )


def test_the_seed_derives_from_the_run_id_so_a_run_reproduces_itself():
    assert seed_for("run-2026-10-16-abc") == seed_for("run-2026-10-16-abc")
    assert seed_for("run-2026-10-16-abc") != seed_for("run-2026-10-16-abd")


def test_the_pairing_does_not_depend_on_the_order_the_agents_arrive_in():
    """Two people reading the same run must get the same plan, whatever the dict order."""
    forward = assign_reviews(ROSTER, seed=11)
    backward = assign_reviews(dict(reversed(list(ROSTER.items()))), seed=11)
    assert sorted(a.pair for a in forward.assignments) == sorted(
        a.pair for a in backward.assignments
    )


# -------------------------------------------------------------------------------- balancing
def test_no_proposal_goes_to_the_vote_unreviewed():
    """A free random draw leaves some proposals with none, and they still get voted on."""
    for seed in range(25):
        counts = assign_reviews(ROSTER, seed=seed).review_counts
        assert min(counts.values()) >= 1


def test_every_proposal_gets_exactly_two_reviews():
    """Decision 35's claim, now for every seed: the greedy pass alone left about one seed in
    seven with a proposal on one review and another on three; the rebalancing redirects reviews
    until each has exactly two, without changing any agent's reviewer role or review kind."""
    for seed in range(500):
        plan = assign_reviews(ROSTER, seed=seed)
        assert set(plan.review_counts.values()) == {REVIEWS_PER_AGENT}, seed
        for agent_id in ROSTER:
            kinds = sorted(a.kind.value for a in plan.for_reviewer(agent_id))
            expected = (
                ["inter_category", "inter_category"]
                if agent_id in plan.fallbacks
                else ["inter_category", "intra_category"]
            )
            assert kinds == expected, (seed, agent_id)


def test_the_roster_splits_evenly_between_the_two_framings():
    plan = assign_reviews(ROSTER, seed=5)
    counts = plan.counts_by_kind()
    # One family has a single member, so it trades its intra-category review for an inter one.
    assert counts["intra_category"] == len(ROSTER) - len(plan.fallbacks)
    assert counts["inter_category"] == len(ROSTER) + len(plan.fallbacks)


# ------------------------------------------------------------------------ a category of one
def test_a_one_member_family_substitutes_a_second_inter_category_review():
    plan = assign_reviews(ROSTER, seed=1)
    assert "pc_researcher" in plan.fallbacks
    assert "no other member" in plan.fallbacks["pc_researcher"]
    kinds = [a.kind for a in plan.for_reviewer("pc_researcher")]
    assert kinds == [ReviewKind.INTER_CATEGORY, ReviewKind.INTER_CATEGORY]


def test_the_substitution_is_recorded_rather_than_silent():
    """It changes what the protocol delivered, so it belongs in the audit trail."""
    plan = assign_reviews(ROSTER, seed=1)
    assert "pc_researcher" in render_report(plan)
    assert "Substitutions" in render_report(plan)


def test_a_roster_with_no_shared_category_still_assigns_two_reviews_each():
    singletons = {"a": H, "b": R, "c": K, "d": N}
    plan = assign_reviews(singletons, seed=2)
    assert set(plan.fallbacks) == set(singletons)
    assert all(len(plan.for_reviewer(a)) == 2 for a in singletons)
    assert all(a.kind is ReviewKind.INTER_CATEGORY for a in plan.assignments)


def test_a_roster_too_small_to_review_is_refused():
    with pytest.raises(ValueError, match="cannot each review"):
        assign_reviews({"a": H, "b": R}, seed=1)


# -------------------------------------------------------------------------------- validation
def test_a_self_review_is_refused():
    bad = AssignmentPlan(
        seed=1,
        assignments=[Assignment("a", H, "a", H, ReviewKind.INTRA_CATEGORY)],
    )
    with pytest.raises(ValueError, match="review itself"):
        validate_plan(bad, {"a": H}, reviews_per_agent=1)


def test_a_mislabelled_kind_is_refused():
    bad = AssignmentPlan(
        seed=1, assignments=[Assignment("a", H, "b", R, ReviewKind.INTRA_CATEGORY)]
    )
    with pytest.raises(ValueError, match="marked intra_category"):
        validate_plan(bad, {"a": H, "b": R}, reviews_per_agent=1)


def test_an_unreviewed_proposal_is_refused():
    plan = AssignmentPlan(
        seed=1,
        assignments=[
            Assignment("a", H, "b", R, ReviewKind.INTER_CATEGORY),
            Assignment("b", R, "a", H, ReviewKind.INTER_CATEGORY),
            Assignment("c", K, "a", H, ReviewKind.INTER_CATEGORY),
        ],
    )
    with pytest.raises(ValueError, match="unreviewed"):
        validate_plan(plan, {"a": H, "b": R, "c": K}, reviews_per_agent=1)


# ------------------------------------------------------------------------------ the prompt
def proposal(agent_id="risk_parity", category=PcCategory.RISK_STRUCTURED) -> PcProposalBody:
    return PcProposalBody(
        agent_id=agent_id,
        method="Risk parity",
        category=category,
        weights={"us_large_cap": 0.3, "intermediate_treasuries": 0.5, "cash": 0.2},
        expected_return_pct=5.4,
        expected_volatility_pct=6.2,
        sharpe_ratio=0.39,
        effective_n=2.7,
        ex_ante_tracking_error_pct=4.1,
        ips_compliance=IpsCompliance(compliant=True),
        rationale="Equal risk contribution across the universe.",
    )


ASSETS = ["us_large_cap", "intermediate_treasuries", "cash"]
BENCHMARK = pd.Series({"us_large_cap": 0.6, "intermediate_treasuries": 0.3, "cash": 0.1})


def test_the_two_framings_ask_for_different_things():
    """§3.5 gives each pairing a purpose; one prompt with a label would waste the distinction."""
    intra = REVIEW_FRAMING[ReviewKind.INTRA_CATEGORY]
    inter = REVIEW_FRAMING[ReviewKind.INTER_CATEGORY]
    assert "technical errors within a shared framework" in intra
    assert "challenge foundational assumptions" in inter
    assert intra != inter


def test_the_prompt_carries_the_framing_for_its_own_kind():
    for kind, other in (
        (ReviewKind.INTRA_CATEGORY, ReviewKind.INTER_CATEGORY),
        (ReviewKind.INTER_CATEGORY, ReviewKind.INTRA_CATEGORY),
    ):
        reviewed_category = (
            PcCategory.RISK_STRUCTURED
            if kind is ReviewKind.INTRA_CATEGORY
            else PcCategory.HEURISTIC
        )
        assignment = Assignment(
            "risk_parity", PcCategory.RISK_STRUCTURED, "other", reviewed_category, kind
        )
        prompt = render_review_prompt(
            assignment,
            proposal("other", reviewed_category),
            asset_ids=ASSETS,
            as_of="2026-10-16",
            benchmark=BENCHMARK,
        )
        assert REVIEW_FRAMING[kind] in prompt
        assert REVIEW_FRAMING[other] not in prompt


def test_the_prompt_shows_the_proposal_its_case_and_the_active_weights():
    assignment = Assignment(
        "max_sharpe",
        PcCategory.RETURN_OPTIMIZED,
        "risk_parity",
        PcCategory.RISK_STRUCTURED,
        ReviewKind.INTER_CATEGORY,
    )
    prompt = render_review_prompt(
        assignment,
        proposal(),
        asset_ids=ASSETS,
        as_of="2026-10-16",
        regime="late_cycle",
        benchmark=BENCHMARK,
    )
    assert "Risk parity" in prompt
    assert "Equal risk contribution" in prompt, "the review is of an argued proposal"
    assert "-30.0%" in prompt, "active weight against the benchmark"
    assert "late_cycle" in prompt


def test_the_prompt_tells_the_reviewer_the_reviews_are_simultaneous():
    assignment = Assignment(
        "max_sharpe",
        PcCategory.RETURN_OPTIMIZED,
        "risk_parity",
        PcCategory.RISK_STRUCTURED,
        ReviewKind.INTER_CATEGORY,
    )
    prompt = render_review_prompt(assignment, proposal(), asset_ids=ASSETS, as_of="2026-10-16")
    assert "simultaneously" in prompt
    assert "cannot respond" in prompt


def test_the_prompt_says_a_breach_does_not_disqualify_a_candidate():
    """Decision 32. A reviewer told otherwise would mark down 13 of 15 portfolios on sight."""
    assignment = Assignment(
        "max_sharpe",
        PcCategory.RETURN_OPTIMIZED,
        "risk_parity",
        PcCategory.RISK_STRUCTURED,
        ReviewKind.INTER_CATEGORY,
    )
    prompt = render_review_prompt(assignment, proposal(), asset_ids=ASSETS, as_of="2026-10-16")
    assert "does not disqualify" in prompt


def test_the_prompt_notes_an_absent_cro_report_rather_than_omitting_it():
    assignment = Assignment(
        "max_sharpe",
        PcCategory.RETURN_OPTIMIZED,
        "risk_parity",
        PcCategory.RISK_STRUCTURED,
        ReviewKind.INTER_CATEGORY,
    )
    prompt = render_review_prompt(assignment, proposal(), asset_ids=ASSETS, as_of="2026-10-16")
    assert "No CRO report was produced" in prompt


def test_rendering_a_self_review_is_refused():
    assignment = Assignment("a", H, "a", H, ReviewKind.INTRA_CATEGORY)
    with pytest.raises(ValueError, match="cannot review itself"):
        render_review_prompt(assignment, proposal("a"), asset_ids=ASSETS, as_of="2026-10-16")


# -------------------------------------------------------------------------------- the report
def test_the_report_records_the_seed_and_every_pairing():
    plan = assign_reviews(ROSTER, seed=99)
    report = render_report(plan, as_of="2026-10-16", run_id="run-x")
    assert "Seed **99**" in report
    assert "run-x" in report
    for assignment in plan.assignments:
        assert assignment.reviewed in report
    assert "Reviews received per proposal" in report

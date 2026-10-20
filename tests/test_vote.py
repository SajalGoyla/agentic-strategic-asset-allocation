"""The modified Borda vote (§3.5): ballots, the tally, the metric blend and the diversity rule.

No network and no API key: ``FakeAnthropic`` stands in for the SDK, and the free path ranks by
the six-dimension metric score.
"""

import dataclasses

import pandas as pd
import pytest
from pydantic import ValidationError

from saa.agents.cro import agent as cro_agent
from saa.agents.pc import agent as pc_agent
from saa.agents.peer_review import run_peer_reviews
from saa.agents.vote import ballot_model, field_briefing, load_reviews, run_vote
from saa.contracts import PcCategory, read
from saa.contracts.cio import SCORE_WEIGHTS, MethodScore
from saa.contracts.review import VoteBody
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.method_scoring import load_cro_reports, load_proposals
from saa.skills.voting import (
    VotingSettings,
    borda_points,
    enforce_diversity,
    load_voting_settings,
    tally,
)
from tests.test_macro_agent import FakeAnthropic
from tests.test_pc_roster import rich_stage_inputs

H, R, K, N, P = (
    PcCategory.HEURISTIC,
    PcCategory.RETURN_OPTIMIZED,
    PcCategory.RISK_STRUCTURED,
    PcCategory.NON_TRADITIONAL,
    PcCategory.PC_RESEARCHER,
)


def score(agent_id, composite):
    """A MethodScore whose six dimensions all equal ``composite``, so the rubric holds."""
    return MethodScore(
        agent_id=agent_id, composite=composite, **dict.fromkeys(SCORE_WEIGHTS, composite)
    )


class Proposal:
    def __init__(self, agent_id, category):
        self.agent_id, self.category, self.method = agent_id, category, agent_id


def field(categories):
    return {a: Proposal(a, c) for a, c in categories.items()}


SETTINGS = VotingSettings(
    vote_weight={"expansion": 0.6, "default": 0.5},
    min_families=3,
    dissent_share=0.5,
    own_family_bonus=0.05,
)


# --------------------------------------------------------------------------------- tally
def test_borda_points_are_5_4_3_2_1_and_minus_2():
    ballots = [
        VoteBody(voter_agent_id="z", top_five=list("abcde"), bottom_flag="f", rationale="-"),
        VoteBody(voter_agent_id="y", top_five=list("bacde"), bottom_flag=None, rationale="-"),
    ]
    points = borda_points(ballots, list("abcdefg"))
    assert points == {"a": 9, "b": 9, "c": 6, "d": 4, "e": 2, "f": -2, "g": 0}
    with pytest.raises(ValueError, match="unknown agent"):
        borda_points(ballots, list("abcde"))


def test_the_blend_uses_the_regime_weight_and_rescales_like_exhibit_9():
    cats = {"a": H, "b": R, "c": K, "d": N, "e": H, "f": R}
    ballots = [VoteBody(voter_agent_id="x", top_five=list("abcde"), bottom_flag="f", rationale="-")]
    scores = {a: score(a, s) for a, s in zip("abcdef", [0.5, 0.6, 0.4, 0.7, 0.5, 0.9], strict=True)}
    result = tally(ballots, field(cats), scores, SETTINGS, regime="expansion")
    body = result.body
    assert (body.vote_weight, body.metric_weight) == (0.6, pytest.approx(0.4))
    composites = {r.agent_id: r.composite for r in body.rows}
    assert max(composites.values()) == 1.0 and min(composites.values()) == 0.0
    # a: vote 5 -> 1.0 normalised; blended 0.6*1.0 + 0.4*0.5 = 0.80, the top.
    assert body.rows[0].agent_id == "a"
    assert [r.rank for r in body.rows] == list(range(1, 7))
    assert tally(ballots, field(cats), scores, SETTINGS, regime="recession").body.vote_weight == 0.5


def test_the_diversity_rule_replaces_the_lowest_duplicate_with_the_best_missing_family():
    ranked = ["h1", "h2", "r1", "h3", "h4", "k1", "n1"]
    cats = {"h1": H, "h2": H, "h3": H, "h4": H, "r1": R, "k1": K, "n1": N}
    shortlist, notes = enforce_diversity(ranked, cats, min_families=3)
    assert shortlist == ["h1", "h2", "r1", "h3", "k1"]
    assert len(notes) == 1 and "k1" in notes[0] and "h4" in notes[0]


def test_the_researcher_does_not_count_as_a_family():
    ranked = ["h1", "p1", "r1", "h2", "r2", "k1"]
    cats = {"h1": H, "p1": P, "r1": R, "h2": H, "r2": R, "k1": K}
    shortlist, notes = enforce_diversity(ranked, cats, min_families=3)
    assert "k1" in shortlist and len(notes) == 1
    assert {cats[a] for a in shortlist} - {P} >= {H, R, K}


def test_a_field_without_enough_families_is_refused():
    with pytest.raises(ValueError, match="spans 2"):
        enforce_diversity(
            ["a", "b", "c", "d", "e"],
            dict.fromkeys("abc", H) | dict.fromkeys("de", R),
            min_families=3,
        )


def test_mass_bottom_flags_are_reported_as_dissent():
    cats = {a: c for a, c in zip("abcdefg", [H, R, K, N, H, R, K], strict=True)}
    ballots = [
        VoteBody(voter_agent_id=v, top_five=list("abcde"), bottom_flag="g", rationale="-")
        for v in "xyz"
    ] + [VoteBody(voter_agent_id="w", top_five=list("abcde"), bottom_flag="f", rationale="-")]
    scores = {a: score(a, 0.5) for a in cats}
    result = tally(ballots, field(cats), scores, SETTINGS, regime=None)
    assert result.dissent == {"g": 3}


def test_the_settings_load(config):
    s = load_voting_settings(config)
    assert s.min_families == 3
    assert 0.0 <= s.weight_for("late_cycle") <= 1.0


# --------------------------------------------------------------------------------- ballots
def test_a_ballot_can_only_name_the_candidates_the_voter_may_rank():
    model = ballot_model("me", ["a", "b", "c", "d", "e", "f"])
    ok = model(top_five=list("abcde"), bottom_flag="f", rationale="-")
    assert [str(x) for x in ok.top_five] == list("abcde")
    for bad in (
        {"top_five": ["me", "a", "b", "c", "d"]},
        {"top_five": list("abcdz")},
        {"top_five": list("abcde"), "bottom_flag": "me"},
        {"top_five": list("abcd")},
        {"top_five": list("abcde"), "bottom_flag": "a"},
    ):
        with pytest.raises(ValidationError):
            model(**{"rationale": "-", **bad})
    with pytest.raises(ValueError, match="cannot be offered itself"):
        ballot_model("me", ["me", "a"])


# --------------------------------------------------------------------------------- the stage
@pytest.fixture(scope="module")
def voting_run(config, tmp_path_factory):
    """Fifteen proposals, their CRO reports and their reviews: ready to vote."""
    root = tmp_path_factory.mktemp("voting")
    settings = config.settings.model_copy(update={"data_dir": root / "data"})
    cfg = dataclasses.replace(config, settings=settings)
    stage = rich_stage_inputs()
    labels = pd.Series(
        "expansion",
        index=pd.date_range("1994-01-31", periods=len(stage.scenario_returns), freq="ME"),
    )
    stage.scenario_returns.index = labels.index
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(pc_agent, "gather_inputs", lambda run, store, config: stage)
        run = RunContext.create(cfg, as_of="2026-10-01", run_id="r", root=root / "run")
        pc_agent.run_pc_agents(run, None, config=cfg, llm=None)
    cro_agent.run_cro(run, None, config=cfg, llm=None, stage=stage)
    run_peer_reviews(run, None, config=cfg, llm=None, stage=stage, regime_labels=labels)
    return run, stage, labels, cfg


def test_every_agent_votes_and_the_tally_reads_back(voting_run):
    run, stage, labels, cfg = voting_run
    result = run_vote(run, None, config=cfg, llm=None, stage=stage, regime_labels=labels)
    roster = set(pc_agent.ROSTER)
    assert set(result.ballots) == roster and not result.skipped
    for voter in roster:
        ballot = read("vote", run.path("vote", agent_id=voter)).body
        assert ballot.voter_agent_id == voter and voter not in ballot.top_five
    tally_file = read("vote_tally", run.path("vote_tally"))
    assert len(tally_file.body.rows) == len(roster)
    assert tally_file.body.diversity_categories >= 3
    assert {i.contract for i in tally_file.header.inputs} == {"vote"}


def test_the_model_ranks_and_the_script_signs(voting_run):
    """Each voter's schema offers only the others; the voter id comes from the script; every
    voter sees the same cached briefing, which does not show the metric score."""
    run, stage, labels, cfg = voting_run
    voters = sorted(pc_agent.ROSTER)
    payloads = []
    for voter in voters:
        others = [a for a in voters if a != voter]
        payloads.append({"top_five": others[:5], "bottom_flag": others[-1], "rationale": "R" * 200})
    llm = LlmClient(FakeAnthropic(payloads))
    result = run_vote(run, None, config=cfg, llm=llm, stage=stage, regime_labels=labels, workers=1)
    assert not result.skipped and len(result.ballots) == len(voters)
    calls = llm._client.messages.calls
    systems = {c["system"][0]["text"] for c in calls}
    assert len(systems) == 1, "one briefing for every voter, so the cache serves 14 of 15"
    assert "metric" not in next(iter(systems)).split("---", 1)[1].lower()
    vote = read("vote", run.path("vote", agent_id=voters[0]))
    assert vote.header.produced_by.value == "llm" and vote.header.model_calls


def test_a_thin_ballot_rationale_is_refused(voting_run):
    run, stage, labels, cfg = voting_run
    voters = sorted(pc_agent.ROSTER)
    others = [a for a in voters if a != voters[0]]
    payloads = [{"top_five": others[:5], "bottom_flag": None, "rationale": "Top five."}]
    payloads += [
        {"top_five": [a for a in voters if a != v][:5], "bottom_flag": None, "rationale": "R" * 200}
        for v in voters[1:]
    ]
    llm = LlmClient(FakeAnthropic(payloads), max_retries=0)
    result = run_vote(run, None, config=cfg, llm=llm, stage=stage, regime_labels=labels, workers=1)
    assert list(result.skipped) == [voters[0]]
    assert "too thin" in result.skipped[voters[0]]


def test_the_briefing_carries_every_proposal_and_its_reviews(voting_run):
    run, _, _, _ = voting_run
    proposals, reports, reviews = load_proposals(run), load_cro_reports(run), load_reviews(run)
    briefing = field_briefing(proposals, reports, reviews)
    for agent_id in proposals:
        assert f"## {agent_id}" in briefing
    assert briefing.count("- weakness:") == len(reviews)


def test_voting_needs_the_reviews_first(tmp_config, tmp_path, monkeypatch):
    stage = rich_stage_inputs()
    monkeypatch.setattr(pc_agent, "gather_inputs", lambda run, store, config: stage)
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    pc_agent.run_pc_agents(
        run,
        None,
        config=tmp_config,
        llm=None,
        methods=["equal_weight", "max_sharpe", "risk_parity"],
    )
    with pytest.raises(FileNotFoundError, match="saa-agent peer-review"):
        run_vote(run, None, config=tmp_config, llm=None, stage=stage)

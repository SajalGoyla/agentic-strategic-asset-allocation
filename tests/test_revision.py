"""The revision of the shortlist (§3.5): the levers, and the agent that pulls them.

No network and no API key: ``FakeAnthropic`` stands in for the SDK.
"""

import dataclasses

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from saa.agents.cro import agent as cro_agent
from saa.agents.pc import agent as pc_agent
from saa.agents.peer_review import run_peer_reviews
from saa.agents.revision import (
    RevisionJudgment,
    consequence_note,
    judgment_model,
    run_revisions,
)
from saa.agents.revision.agent import revise_agent, system_prompt
from saa.agents.vote import load_reviews, run_vote
from saa.contracts import read
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.method_scoring import load_proposals
from saa.skills.portfolio_construction.revision import (
    RevisionLevers,
    apply_levers,
    revise,
    turnover,
)
from tests.test_macro_agent import FakeAnthropic, FakeResponse, FakeUsage
from tests.test_pc_roster import RICH_IDS, rich_stage_inputs

W = pd.Series([0.40, 0.25, 0.15, 0.10, 0.05, 0.03, 0.02], index=RICH_IDS)


# --------------------------------------------------------------------------------- levers
def test_excluding_an_asset_zeroes_it_and_renormalises():
    w = apply_levers(W, RICH_IDS, RevisionLevers(exclude=("us_large_cap",)))
    assert w["us_large_cap"] == 0.0
    assert w.sum() == pytest.approx(1.0)
    assert w["us_small_cap"] == pytest.approx(0.25 / 0.60)


def test_a_cap_is_water_filled_and_holds_exactly():
    w = apply_levers(W, RICH_IDS, RevisionLevers(max_weight=0.20))
    assert w.max() == pytest.approx(0.20)
    assert w.sum() == pytest.approx(1.0)
    # The excess goes to the uncapped assets in proportion to their weights.
    assert w["gold"] / w["cash"] == pytest.approx(0.03 / 0.02)


def test_shrinking_moves_part_way_to_equal_weight():
    w = apply_levers(W, RICH_IDS, RevisionLevers(shrink_to_equal=0.5))
    expected = 0.5 * W + 0.5 / len(RICH_IDS)
    np.testing.assert_allclose(w.to_numpy(), expected.to_numpy())


def test_impossible_or_unknown_levers_are_refused():
    with pytest.raises(ValueError, match="cannot sum to 100%"):
        apply_levers(W, RICH_IDS, RevisionLevers(max_weight=0.10))
    with pytest.raises(ValueError, match="unknown assets"):
        apply_levers(W, RICH_IDS, RevisionLevers(exclude=("bitcoin",)))
    with pytest.raises(ValueError, match="shrink_to_equal"):
        apply_levers(W, RICH_IDS, RevisionLevers(shrink_to_equal=0.9))
    with pytest.raises(ValueError, match="every asset"):
        apply_levers(W, RICH_IDS, RevisionLevers(exclude=tuple(RICH_IDS)))


def test_turnover_is_half_the_absolute_change():
    after = pd.Series({"a": 0.5, "b": 0.5})
    assert turnover({"a": 1.0}, after) == pytest.approx(0.5)


# ------------------------------------------------------------------------------ judgment
def test_the_decision_and_the_levers_must_agree():
    base = {"response_to_reviews": [], "rationale": "-"}
    with pytest.raises(ValidationError, match="revise is false"):
        RevisionJudgment(revise=False, max_weight_pct=30.0, **base)
    with pytest.raises(ValidationError, match="no lever moved"):
        RevisionJudgment(revise=True, **base)


def test_the_schema_offers_only_this_runs_assets_and_reviewers():
    model = judgment_model(RICH_IDS, ["max_sharpe", "risk_parity"])
    ok = model(
        revise=True,
        exclude=["gold"],
        response_to_reviews=[{"reviewer": "max_sharpe", "response": "-"}],
        rationale="-",
    )
    assert [str(a) for a in ok.exclude] == ["gold"]
    with pytest.raises(ValidationError):
        model(revise=True, exclude=["bitcoin"], response_to_reviews=[], rationale="-")
    with pytest.raises(ValidationError):
        model(
            revise=False,
            response_to_reviews=[{"reviewer": "someone_else", "response": "-"}],
            rationale="-",
        )


# --------------------------------------------------------------------------------- the stage
@pytest.fixture(scope="module")
def voted_run(config, tmp_path_factory):
    """Proposals, CRO reports, reviews and the vote: ready for the shortlist to revise."""
    root = tmp_path_factory.mktemp("revision")
    cfg = dataclasses.replace(
        config, settings=config.settings.model_copy(update={"data_dir": root / "data"})
    )
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
    run_vote(run, None, config=cfg, llm=None, stage=stage, regime_labels=labels)
    return run, stage, cfg


def test_the_levers_are_applied_exactly(voted_run):
    run, stage, cfg = voted_run
    proposal = load_proposals(run)["max_sharpe"]
    held = max(proposal.weights, key=proposal.weights.get)
    revised = revise(proposal, RevisionLevers(exclude=(held,), max_weight=0.30), stage, cfg)
    assert revised.weights[held] == pytest.approx(0.0, abs=1e-6)
    assert revised.weights.max() <= 0.30 + 1e-6


def test_without_a_model_the_shortlist_is_kept_and_filed_beside_the_originals(voted_run):
    run, stage, cfg = voted_run
    result = run_revisions(run, None, config=cfg, llm=None, stage=stage)
    shortlist = read("vote_tally", run.path("vote_tally")).body.shortlist
    assert list(result.revisions) == shortlist and not result.skipped
    for agent_id in shortlist:
        original = read("pc_proposal", run.path("pc_proposal", agent_id=agent_id)).body
        revised = read("pc_proposal", run.path("pc_proposal", agent_id=agent_id, revision=True))
        assert revised.body.revision_of == f"pc/{agent_id}/pc_proposal.json"
        assert revised.body.weights == pytest.approx(original.weights)
        assert result.revisions[agent_id].turnover == pytest.approx(0.0, abs=1e-9)
        assert revised.header.produced_by.value == "script"
        assert original.revision_of is None, "the original is untouched"


class ByAgent:
    """A fake SDK that answers each shortlisted agent from its own payload, however many times
    it is asked, so a one-time note to one agent cannot shift the answers of the next."""

    def __init__(self, payloads: dict[str, dict]):
        self.payloads, self.calls = payloads, []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        prompt = kwargs["messages"][0]["content"]
        agent = next(a for a in self.payloads if f"You are `{a}`" in prompt)
        return FakeResponse(parsed_output=self.payloads[agent], usage=FakeUsage())


def responses(run, agent_id, text="Accepted: the concentration point is fair, so capped it."):
    return [
        {"reviewer": r.reviewer_agent_id, "response": text}
        for r in load_reviews(run)
        if r.reviewed_agent_id == agent_id
    ]


def test_a_model_revision_moves_the_levers_and_answers_every_review(voted_run):
    run, stage, cfg = voted_run
    shortlist = read("vote_tally", run.path("vote_tally")).body.shortlist
    payloads = {
        a: {
            "revise": True,
            "max_weight_pct": 35.0,
            "shrink_to_equal": 0.2,
            "response_to_reviews": responses(run, a),
            "rationale": "R" * 220,
        }
        for a in shortlist
    }
    llm = LlmClient(ByAgent(payloads))
    result = run_revisions(run, None, config=cfg, llm=llm, stage=stage, workers=1)
    assert not result.skipped
    for item in result.revisions.values():
        assert item.levers.shrink_to_equal == 0.2
        assert max(item.body.weights.values()) <= 0.35 + 1e-6
        assert "Responses to reviews" in item.body.notes
    first = read("pc_proposal", run.path("pc_proposal", agent_id=shortlist[0], revision=True))
    assert first.header.produced_by.value == "hybrid" and first.header.model_calls


def test_a_lever_that_creates_a_breach_is_shown_once_then_kept(voted_run):
    """§3.5: the agent revises "taking into account ... the CRO report". A shrink that drops a
    tuned portfolio below the volatility floor is shown to it once; repeating it files it."""
    run, stage, cfg = voted_run
    proposal = load_proposals(run)["max_sharpe"]
    assert proposal.ips_compliance.compliant
    levers = RevisionLevers(shrink_to_equal=0.5)
    note = consequence_note(proposal, levers, stage, cfg)
    assert note and "newly breaches" in note and "volatility" in note
    assert consequence_note(proposal, RevisionLevers(), stage, cfg) is None

    reviews = load_reviews(run)
    reviews = [r for r in reviews if r.reviewed_agent_id == "max_sharpe"]
    tally = read("vote_tally", run.path("vote_tally")).body
    payload = {
        "revise": True,
        "shrink_to_equal": 0.5,
        "response_to_reviews": responses(run, "max_sharpe"),
        "rationale": "R" * 220,
    }
    fake = FakeAnthropic([payload, payload])
    result = revise_agent(
        "max_sharpe",
        proposal,
        None,
        reviews,
        tally,
        stage,
        cfg,
        LlmClient(fake),
        ips_status="draft",
        system=system_prompt(),
    )
    calls = fake.messages.calls
    assert len(calls) == 2, "shown once, then the same levers are accepted"
    assert "newly breaches" in calls[1]["messages"][-1]["content"]
    assert result.levers.shrink_to_equal == 0.5
    assert not result.body.ips_compliance.compliant, "the agent's choice is filed as it is"


def test_a_revision_that_ignores_a_review_is_refused(voted_run):
    run, stage, cfg = voted_run
    shortlist = read("vote_tally", run.path("vote_tally")).body.shortlist
    partial = responses(run, shortlist[0])[:1]
    payloads = [{"revise": False, "response_to_reviews": partial, "rationale": "R" * 220}]
    payloads += [
        {"revise": False, "response_to_reviews": responses(run, a), "rationale": "R" * 220}
        for a in shortlist[1:]
    ]
    llm = LlmClient(FakeAnthropic(payloads), max_retries=0)
    result = run_revisions(run, None, config=cfg, llm=llm, stage=stage, workers=1)
    assert list(result.skipped) == [shortlist[0]]
    assert "no response to the review" in result.skipped[shortlist[0]]


def test_revisions_need_the_vote_first(tmp_config, tmp_path):
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    with pytest.raises(FileNotFoundError, match="saa-agent vote"):
        run_revisions(run, None, config=tmp_config, llm=None)


def test_only_a_proposal_has_a_revised_file(tmp_config, tmp_path):
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    assert run.path("pc_proposal", agent_id="a", revision=True).name == "pc_proposal-revised.json"
    with pytest.raises(ValueError, match="only to pc_proposal"):
        run.path("vote", agent_id="a", revision=True)

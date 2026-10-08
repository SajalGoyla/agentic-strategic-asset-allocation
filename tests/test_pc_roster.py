"""The full PC roster: the PC-researcher and the adversarial diversifier, and the order the stage
runs them in. No network and no API key: ``FakeAnthropic`` stands in for the SDK.
"""

import pandas as pd
import pytest

from saa.agents import pc_researcher
from saa.agents.pc import agent as pc_agent
from saa.contracts import read
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.portfolio_construction import METHODS, build_candidates
from tests.test_cma_judge import stage_inputs
from tests.test_macro_agent import FakeAnthropic

LONG = "The registry has no method that rewards breadth under a return constraint. " * 4


def research_payload(**overrides) -> dict:
    payload = {
        "method_id": "global_minimum_variance",
        "objective": "Maximise the diversification ratio.",
        "not_spanned_by": ["risk_parity", "equal_weight", "not_a_method"],
        "gap": "Every risk-based method concentrates in cash.",
        "implementation_notes": "Long-only SLSQP from two starts.",
        "rationale": LONG,
        "main_weakness": "Ignores expected returns.",
    }
    payload.update(overrides)
    return payload


def rationale_payload() -> dict:
    return {
        "rationale": LONG,
        "key_assumption": "a",
        "main_weakness": "b",
        "when_preferred": "c",
        "invalidation": "d",
    }


# --------------------------------------------------------------------------- researcher
def test_researcher_without_a_model_proposes_the_papers_choice(tmp_config):
    stage = stage_inputs(tmp_config)
    registry, _ = build_candidates(stage, tmp_config)
    outcome = pc_researcher.research(stage, tmp_config, registry, None, ips_status="draft")
    assert outcome.call is None
    assert outcome.research.method_name.startswith("Maximum entropy")
    assert outcome.proposal.agent_id == "pc_researcher"
    assert outcome.proposal.category.value == "pc_researcher"
    assert "--no-llm" in outcome.proposal.rationale


def test_researcher_runs_the_method_the_model_chose(tmp_config):
    stage = stage_inputs(tmp_config)
    registry, _ = build_candidates(stage, tmp_config)
    llm = LlmClient(FakeAnthropic([research_payload()]))
    outcome = pc_researcher.research(stage, tmp_config, registry, llm, ips_status="draft")
    assert outcome.candidate.method.id == "global_minimum_variance"
    assert outcome.candidate.agent_id == "pc_researcher"
    # Names that are not registry methods are dropped from the contract, not trusted.
    assert outcome.research.not_spanned_by == ["risk_parity", "equal_weight"]
    assert "Gap in the registry" in outcome.proposal.notes


def test_researcher_can_only_choose_an_implemented_method(tmp_config):
    """A proposal the pipeline cannot run cannot be reviewed, so the schema forbids it."""
    stage = stage_inputs(tmp_config)
    registry, _ = build_candidates(stage, tmp_config)
    bad = research_payload(method_id="quantum_annealing")
    llm = LlmClient(FakeAnthropic([bad, bad, bad]))
    with pytest.raises(Exception, match="quantum_annealing|method_id"):
        pc_researcher.research(stage, tmp_config, registry, llm, ips_status="draft")


def test_researcher_rejects_a_thin_rationale(tmp_config):
    stage = stage_inputs(tmp_config)
    registry, _ = build_candidates(stage, tmp_config)
    llm = LlmClient(FakeAnthropic([research_payload(rationale="Short.")]))
    with pytest.raises(ValueError, match="too thin"):
        pc_researcher.research(stage, tmp_config, registry, llm, ips_status="draft")


def test_the_researcher_prompt_shows_what_the_registry_produced(tmp_config):
    stage = stage_inputs(tmp_config)
    registry, _ = build_candidates(stage, tmp_config)
    prompt = pc_researcher.build_prompt(
        stage, registry, pc_researcher.library_options(METHODS), ips_status="draft"
    )
    for method_id in METHODS:
        assert method_id in prompt
    assert "`maximum_entropy`" in prompt and "`global_minimum_variance`" in prompt


# --------------------------------------------------------------------------- the stage
@pytest.fixture
def stage_run(tmp_config, tmp_path, monkeypatch):
    stage = stage_inputs(tmp_config)
    monkeypatch.setattr(pc_agent, "gather_inputs", lambda run, store, config: stage)
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    return stage, run


def test_the_whole_roster_runs_without_a_model(stage_run, tmp_config):
    stage, run = stage_run
    result = pc_agent.run_pc_agents(run, None, config=tmp_config, llm=None)
    assert not result.skipped
    assert list(result.proposals) == pc_agent.ROSTER  # registry, then researcher, then adversary
    for agent_id in result.proposals:
        read("pc_proposal", run.path("pc_proposal", agent_id=agent_id))
    assert read("pc_research", run.path("pc_research")).body.method_name


def test_the_adversary_moves_away_from_everyone_else(stage_run, tmp_config):
    stage, run = stage_run
    result = pc_agent.run_pc_agents(run, None, config=tmp_config, llm=None)
    others = [p.candidate for k, p in result.proposals.items() if k != "adversarial_diversifier"]
    center = pc_agent.centroid(others, stage.asset_ids)
    sigma = stage.covariance.to_numpy()

    def distance(weights: pd.Series) -> float:
        d = (weights.reindex(stage.asset_ids).fillna(0.0) - center).to_numpy()
        return float(d @ sigma @ d)

    adversary = result.proposals["adversarial_diversifier"]
    assert all(distance(adversary.candidate.weights) >= distance(c.weights) - 1e-9 for c in others)
    assert adversary.body.notes.startswith(
        f"Tracking error to the centroid of the other {len(pc_agent.ROSTER) - 1}"
    )


def test_the_adversary_needs_others_to_oppose(stage_run, tmp_config):
    _, run = stage_run
    result = pc_agent.run_pc_agents(
        run, None, config=tmp_config, llm=None, methods=["equal_weight", "adversarial_diversifier"]
    )
    assert "adversarial_diversifier" in result.skipped
    assert list(result.proposals) == ["equal_weight"]


def test_one_call_per_agent_and_a_flagship_researcher(stage_run, tmp_config):
    _, run = stage_run
    roster = len(pc_agent.ROSTER)
    # Registry methods run in parallel, so their responses are interchangeable; the researcher
    # is called after them and the adversary last.
    outputs = [rationale_payload()] * len(METHODS) + [research_payload(), rationale_payload()]
    llm = LlmClient(FakeAnthropic(outputs))
    result = pc_agent.run_pc_agents(run, None, config=tmp_config, llm=llm, workers=1)
    assert len(result.proposals) == roster
    calls = llm._client.messages.calls
    assert len(calls) == roster
    assert calls[len(METHODS)]["model"] == llm.models[pc_researcher.agent.Tier.FLAGSHIP]
    research = read("pc_research", run.path("pc_research"))
    assert research.header.produced_by.value == "llm"
    assert research.header.model_calls


def test_unknown_agents_are_reported_not_ignored(stage_run, tmp_config):
    _, run = stage_run
    result = pc_agent.run_pc_agents(
        run, None, config=tmp_config, llm=None, methods=["equal_weight", "momentum"]
    )
    assert "momentum" in result.skipped


def test_agent_slugs():
    assert pc_agent.agent_slug("max_sharpe") == "pc-max-sharpe"
    assert pc_agent.agent_slug("pc_researcher") == "pc-researcher"

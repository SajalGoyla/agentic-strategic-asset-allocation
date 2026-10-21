"""The full PC roster: the PC-researcher and the adversarial diversifier, and the order the stage
runs them in. No network and no API key: ``FakeAnthropic`` stands in for the SDK.
"""

import logging

import numpy as np
import pandas as pd
import pytest

from saa.agents import pc_researcher
from saa.agents.pc import agent as pc_agent
from saa.contracts import read
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.portfolio_construction import METHODS, StageInputs, build_candidates
from tests.test_cma_judge import stage_inputs
from tests.test_macro_agent import FakeAnthropic

LONG = "The registry has no method that rewards breadth under a return constraint. " * 4

RICH_IDS = [
    "us_large_cap",
    "us_small_cap",
    "intl_developed",
    "intermediate_treasuries",
    "ig_corporates",
    "gold",
    "cash",
]


def rich_stage_inputs() -> StageInputs:
    """Seven assets across equity, bonds, gold and cash.

    The three-asset stage the other tests use cannot test the researcher's substitution: pinned
    to the 8% volatility floor, three assets leave room for essentially one portfolio, so every
    library method lands on a registry one. Seven leave enough room for the methods to differ,
    as the real 18 do, while maximum entropy still collapses onto equal weight -- the case the
    substitution exists for.
    """
    vol = np.array([0.15, 0.20, 0.16, 0.065, 0.07, 0.18, 0.006])
    corr = np.array(
        [
            [1.0, 0.85, 0.80, -0.10, 0.30, 0.05, 0.0],
            [0.85, 1.0, 0.75, -0.15, 0.30, 0.05, 0.0],
            [0.80, 0.75, 1.0, -0.05, 0.30, 0.10, 0.0],
            [-0.10, -0.15, -0.05, 1.0, 0.70, 0.20, 0.10],
            [0.30, 0.30, 0.30, 0.70, 1.0, 0.15, 0.10],
            [0.05, 0.05, 0.10, 0.20, 0.15, 1.0, 0.0],
            [0.0, 0.0, 0.0, 0.10, 0.10, 0.0, 1.0],
        ]
    )
    cov = pd.DataFrame(np.outer(vol, vol) * corr, index=RICH_IDS, columns=RICH_IDS)
    mu = pd.Series([0.075, 0.09, 0.08, 0.05, 0.055, 0.065, 0.037], index=RICH_IDS)
    scenarios = pd.DataFrame(
        np.random.default_rng(3).multivariate_normal(mu / 12, cov.to_numpy() / 12, size=360),
        columns=RICH_IDS,
    )
    benchmark = pd.Series(
        {"us_large_cap": 0.6, "intermediate_treasuries": 0.3, "ig_corporates": 0.1}
    )
    return StageInputs(
        as_of=pd.Timestamp("2026-10-01").date(),
        asset_ids=RICH_IDS,
        covariance=cov,
        expected_returns=mu,
        risk_free=0.037,
        inflation_pct=2.4,
        market_weights=pd.Series([0.45, 0.06, 0.12, 0.08, 0.06, 0.08, 0.15], index=RICH_IDS),
        benchmark=benchmark.reindex(RICH_IDS).fillna(0.0),
        regime="expansion",
        provenance={},
        inputs=[],
        scenario_returns=scenarios,
        cash_id="cash",
    )


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
def test_researcher_without_a_model_substitutes_when_its_default_is_already_spanned(tmp_config):
    """§3.4 asks for a method "not spanned by the current registry", and a portfolio identical
    to a registry one is spanned however novel the objective sounds.

    Maximum entropy is the paper's own March 2026 choice and the default without a model, but
    it reduces to equal weight whenever equal weight already clears the Sharpe floor. The
    researcher then moves down its library and says why.
    """
    stage = rich_stage_inputs()
    registry, _ = build_candidates(stage, tmp_config)
    outcome = pc_researcher.research(stage, tmp_config, registry, None, ips_status="draft")

    assert outcome.call is None
    assert outcome.proposal.agent_id == "pc_researcher"
    assert outcome.proposal.category.value == "pc_researcher"
    assert "--no-llm" in outcome.proposal.rationale
    assert not outcome.research.method_name.startswith("Maximum entropy")
    # The substitution is explained, and against the method it actually ran.
    assert "reduces to" in outcome.proposal.notes
    ran = outcome.candidate.method
    assert outcome.research.method_name == ran.name and outcome.research.reference == ran.reference


def test_the_researcher_never_duplicates_a_registry_portfolio(tmp_config):
    stage = rich_stage_inputs()
    registry, _ = build_candidates(stage, tmp_config)
    outcome = pc_researcher.research(stage, tmp_config, registry, None, ips_status="draft")

    sigma = stage.covariance.loc[stage.asset_ids, stage.asset_ids].to_numpy()
    mine = outcome.candidate.weights.reindex(stage.asset_ids).fillna(0.0).to_numpy()
    for agent_id, candidate in registry.items():
        other = candidate.weights.reindex(stage.asset_ids).fillna(0.0).to_numpy()
        active = mine - other
        distance = 100 * float((active @ sigma @ active) ** 0.5)
        assert distance > pc_researcher.agent.DUPLICATE_TRACKING_ERROR_PCT, (
            f"the researcher's portfolio is indistinguishable from {agent_id}"
        )


def test_when_every_library_method_is_spanned_the_default_stays_and_says_so(tmp_config, caplog):
    """A registry that already holds every library portfolio leaves nothing novel to propose.
    The researcher then keeps its choice rather than fail the stage, and logs it; the peer
    review sees a proposal it can call redundant."""
    from saa.skills.portfolio_construction import RESEARCH_LIBRARY, build_candidate

    stage = stage_inputs(tmp_config)
    registry = {
        f"copy_of_{m}": build_candidate(method, stage, tmp_config, agent=f"copy_of_{m}")
        for m, method in RESEARCH_LIBRARY.items()
    }
    with caplog.at_level(logging.WARNING, logger="saa.agents.pc_researcher.agent"):
        outcome = pc_researcher.research(stage, tmp_config, registry, None, ips_status="draft")
    assert outcome.research.method_name.startswith("Maximum entropy")
    assert "every library method duplicates a registry portfolio" in caplog.text


def test_researcher_runs_the_method_the_model_chose(tmp_config):
    stage = stage_inputs(tmp_config)
    registry, _ = build_candidates(stage, tmp_config)
    llm = LlmClient(FakeAnthropic([research_payload(method_id="mean_downside_risk")]))
    outcome = pc_researcher.research(stage, tmp_config, registry, llm, ips_status="draft")
    assert outcome.candidate.method.id == "mean_downside_risk"
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
    llm = LlmClient(FakeAnthropic([research_payload(rationale="Short.")]), max_retries=0)
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

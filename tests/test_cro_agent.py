"""The CRO agent: one standardised risk report per candidate, and it never votes (§3.5).

No network and no API key: ``FakeAnthropic`` stands in for the SDK.
"""

import pytest

from saa.agents.cro import agent as cro
from saa.agents.pc import agent as pc_agent
from saa.contracts import CroJudgment, CroReportBody, read
from saa.contracts.review import CRO_CONTRACT
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.portfolio_construction import build_candidates
from tests.test_cma_judge import stage_inputs
from tests.test_macro_agent import FakeAnthropic

METHODS = ["equal_weight", "max_sharpe", "risk_parity"]
COMMENTARY = (
    "The binding risk here is duration, not equity: the portfolio carries two thirds of its "
    "variance in intermediate Treasuries, and the ex-ante estimate leans on a correlation that "
    "held through 2010 and broke in 2022. The backtest understates it for that reason. "
)


def judgment_payload(**overrides) -> dict:
    payload = {
        "key_risks": ["duration concentration in intermediate Treasuries", "correlation breakdown"],
        "concentration_assessment": "The tilt is the method working as designed.",
        "tail_risk_assessment": "The 1993 panel start omits the last inflationary drawdown.",
        "ips_assessment": "Below the volatility floor; relevant to the ensemble, not fatal.",
        "commentary": COMMENTARY,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def run_with_proposals(tmp_config):
    """A run directory holding PC proposals, written the way the PC stage writes them."""
    run = RunContext.create(tmp_config, as_of="2026-10-16", run_id="run-test")
    stage = stage_inputs(tmp_config)
    candidates, _ = build_candidates(stage, tmp_config, method_ids=METHODS)
    for method_id, candidate in candidates.items():
        run.write(
            "pc_proposal",
            pc_agent.agent_slug(method_id),
            candidate.body("a rationale long enough for a reviewer to engage with"),
            agent_id=pc_agent.agent_slug(method_id),
        )
    return run, stage


# --------------------------------------------------------------------------- loading proposals
def test_proposals_are_keyed_by_the_agent_id_inside_them_not_the_directory(run_with_proposals):
    run, _ = run_with_proposals
    proposals = cro.load_proposals(run)
    assert set(proposals) == set(METHODS)
    assert all(body.agent_id == agent_id for agent_id, body in proposals.items())


def test_a_run_with_no_proposals_says_what_to_run(tmp_config):
    from saa.data.store import DataStore

    run = RunContext.create(tmp_config, as_of="2026-10-16", run_id="empty")
    with pytest.raises(FileNotFoundError, match="saa-agent pc"):
        cro.run_cro(run, DataStore(tmp_config), config=tmp_config, llm=None)


# ------------------------------------------------------------------------------- the report
def test_without_a_model_every_metric_is_still_computed(run_with_proposals, tmp_config):
    run, stage = run_with_proposals
    for method_id in METHODS:
        proposal = cro.load_proposals(run)[method_id]
        profile = cro.profile_proposal(proposal, stage, tmp_config)
        report = cro.assess(profile, proposal, stage, None, ips_status="draft", system="")

        assert report.call is None, "no model, no spend"
        assert report.body.ex_ante_volatility_pct > 0
        assert report.body.risk_score_components
        assert "--no-llm" in report.body.judgment.commentary


def test_the_model_writes_the_assessment_and_never_the_numbers(run_with_proposals, tmp_config):
    run, stage = run_with_proposals
    proposal = cro.load_proposals(run)["equal_weight"]
    profile = cro.profile_proposal(proposal, stage, tmp_config)
    llm = LlmClient(FakeAnthropic([judgment_payload()]))
    report = cro.assess(profile, proposal, stage, llm, ips_status="draft", system="s")

    # The judgment schema is what constrains the model, and it holds no metric at all.
    assert llm._client.messages.calls[0]["output_format"] is CroJudgment
    assert set(CroJudgment.model_fields) == {
        "key_risks",
        "concentration_assessment",
        "tail_risk_assessment",
        "ips_assessment",
        "commentary",
    }
    assert report.body.risk_score == pytest.approx(profile.risk_score)
    assert report.body.ex_ante_volatility_pct == pytest.approx(profile.ex_ante_volatility_pct)


def test_a_risk_report_with_no_named_risk_is_refused():
    with pytest.raises(ValueError, match="no named risk"):
        CroJudgment(**judgment_payload(key_risks=[]))


def test_thin_commentary_is_refused(run_with_proposals, tmp_config):
    """A restatement of the table is not an assessment, and the reviewers read this."""
    run, stage = run_with_proposals
    proposal = cro.load_proposals(run)["equal_weight"]
    profile = cro.profile_proposal(proposal, stage, tmp_config)
    llm = LlmClient(
        FakeAnthropic([judgment_payload(commentary="Volatility is 9.1%.")]), max_retries=0
    )
    with pytest.raises(ValueError, match="too thin"):
        cro.assess(profile, proposal, stage, llm, ips_status="draft", system="s")


def test_the_cro_has_no_ballot():
    """§3.5: "it scores risk and produces commentary, but does not vote"."""
    fields = set(CroReportBody.model_fields) | set(CroJudgment.model_fields)
    assert not {f for f in fields if "vote" in f or "rank" in f or "top" in f}


# ---------------------------------------------------------------------------------- the stage
def test_the_stage_writes_a_valid_contract_for_every_candidate(run_with_proposals, tmp_config):
    from saa.data.store import DataStore

    run, stage = run_with_proposals
    result = cro.run_cro(run, DataStore(tmp_config), config=tmp_config, llm=None, stage=stage)

    assert set(result.reports) == set(METHODS)
    assert not result.skipped
    assert result.cost_usd == 0.0
    for agent_id in METHODS:
        path = run.path(CRO_CONTRACT, agent_id=agent_id)
        output = read(CRO_CONTRACT, path)
        assert output.body.portfolio_agent_id == agent_id
        assert output.header.produced_by.value == "script"
        assert output.header.ips_status == tmp_config.ips.status


def test_the_report_records_the_proposal_it_assessed(run_with_proposals, tmp_config):
    from saa.data.store import DataStore

    run, stage = run_with_proposals
    cro.run_cro(run, DataStore(tmp_config), config=tmp_config, llm=None, stage=stage)
    header = read(CRO_CONTRACT, run.path(CRO_CONTRACT, agent_id="equal_weight")).header
    assert any(ref.contract == "pc_proposal" for ref in header.inputs)


def test_an_unknown_agent_is_reported_not_silently_dropped(run_with_proposals, tmp_config):
    from saa.data.store import DataStore

    run, stage = run_with_proposals
    result = cro.run_cro(
        run,
        DataStore(tmp_config),
        config=tmp_config,
        llm=None,
        agents=["equal_weight", "not_a_method"],
        stage=stage,
    )
    assert set(result.reports) == {"equal_weight"}
    assert "not_a_method" in result.skipped


def test_the_summary_ranks_by_risk_and_says_the_cro_does_not_vote(run_with_proposals, tmp_config):
    from saa.data.store import DataStore

    run, stage = run_with_proposals
    result = cro.run_cro(run, DataStore(tmp_config), config=tmp_config, llm=None, stage=stage)
    summary = cro.render_summary(result)

    assert "does not vote" in summary
    scores = [
        result.reports[a].body.risk_score
        for a in [
            line.split("|")[1].strip() for line in summary.splitlines() if line.count("|") > 8
        ]
        if a in result.reports
    ]
    assert scores == sorted(scores, reverse=True)


# ------------------------------------------------------------------------------- the prompt
def test_the_prompt_gives_the_model_the_metrics_the_compliance_and_the_agents_own_case(
    run_with_proposals, tmp_config
):
    run, stage = run_with_proposals
    proposal = cro.load_proposals(run)["risk_parity"]
    profile = cro.profile_proposal(proposal, stage, tmp_config)
    prompt = cro.build_prompt(profile, proposal, stage, ips_status="draft")

    assert "ex-ante volatility" in prompt
    assert "IPS compliance" in prompt
    assert proposal.rationale in prompt, "the CRO reads the case the agent made"
    assert "neutral assessor" in prompt
    assert "Do not rank" in prompt
    assert "one of fifteen" in prompt


def test_the_prompt_states_the_risk_score_is_not_the_models_to_set(run_with_proposals, tmp_config):
    run, stage = run_with_proposals
    proposal = cro.load_proposals(run)["equal_weight"]
    profile = cro.profile_proposal(proposal, stage, tmp_config)
    prompt = cro.build_prompt(profile, proposal, stage, ips_status="draft")
    assert f"{profile.risk_score:.2f}" in prompt
    assert "Components:" in prompt


def test_the_agent_description_and_the_risk_skill_are_both_in_the_system_prompt():
    system = cro.system_prompt()
    assert "does not vote" in system
    assert "Risk Skill" in system, "the skill that computed every number it is reading"

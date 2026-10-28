"""The peer-review agent (§3.5): the reviews themselves, written over the seeded pairing.

No network and no API key: ``FakeAnthropic`` stands in for the SDK, and the free path writes
metric-based reviews.
"""

import pandas as pd
import pytest

from saa.agents.cro import agent as cro_agent
from saa.agents.pc import agent as pc_agent
from saa.agents.peer_review import run_peer_reviews
from saa.contracts import ReviewKind, read
from saa.contracts.review import ReviewJudgment
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.method_scoring import load_scoring_settings, score_candidates
from saa.skills.peer_review import seed_for
from tests.test_macro_agent import FakeAnthropic, schema_title
from tests.test_pc_roster import rich_stage_inputs

LONG = "The method's premise depends on expected returns being stable across regimes. " * 4


def judgment_payload(**overrides) -> dict:
    payload = {
        "strengths": ["spreads risk across the equity sleeve"],
        "weaknesses": ["concentrates in duration if rates rise"],
        "technical_errors": [],
        "score": 0.62,
        "rationale": LONG,
    }
    payload.update(overrides)
    return payload


@pytest.fixture(scope="module")
def reviewed_run(config, tmp_path_factory):
    """A run with all 15 proposals and their CRO reports, ready to be reviewed.

    Built once per module: the roster takes about a minute (the resampled frontier and the
    adversarial diversifier dominate), and every test re-runs the reviews it reads, so sharing
    the proposals and risk reports is safe.
    """
    import dataclasses

    root = tmp_path_factory.mktemp("reviewed")
    settings = config.settings.model_copy(update={"data_dir": root / "data"})
    tmp_config = dataclasses.replace(config, settings=settings)
    stage = rich_stage_inputs()
    labels = pd.Series(
        "expansion",
        index=pd.date_range("1994-01-31", periods=len(stage.scenario_returns), freq="ME"),
    )
    stage.scenario_returns.index = labels.index
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(pc_agent, "gather_inputs", lambda run, store, config: stage)
        run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=root / "run")
        pc_agent.run_pc_agents(run, None, config=tmp_config, llm=None)
    cro_agent.run_cro(run, None, config=tmp_config, llm=None, stage=stage)
    return run, stage, labels


def test_every_agent_writes_two_reviews_and_every_proposal_gets_two(reviewed_run, tmp_config):
    run, stage, labels = reviewed_run
    result = run_peer_reviews(
        run, None, config=tmp_config, llm=None, stage=stage, regime_labels=labels
    )
    roster = set(pc_agent.ROSTER)
    assert not result.skipped
    assert len(result.reviews) == 2 * len(roster)
    for agent_id in roster:
        assert len(result.received(agent_id)) == 2
        assert len(result.plan.for_reviewer(agent_id)) == 2


def test_each_review_is_filed_with_the_seed_and_reads_back(reviewed_run, tmp_config):
    run, stage, labels = reviewed_run
    result = run_peer_reviews(
        run, None, config=tmp_config, llm=None, stage=stage, regime_labels=labels
    )
    assert result.plan.seed == seed_for(run.run_id)
    for reviewer, reviewed in result.reviews:
        path = run.path("peer_review", agent_id=reviewer, reviewed=reviewed)
        loaded = read("peer_review", path)
        assert loaded.header.seed == result.plan.seed
        assert loaded.header.produced_by.value == "script"
        assert (loaded.body.reviewer_agent_id, loaded.body.reviewed_agent_id) == (
            reviewer,
            reviewed,
        )
        refs = {i.contract for i in loaded.header.inputs}
        assert {"pc_proposal", "cro_report"} <= refs


def test_free_reviews_score_with_the_shared_metric(reviewed_run, tmp_config):
    """Without a model, a review's score is the six-dimension composite the vote and the CIO
    read, so a free run agrees with itself."""
    run, stage, labels = reviewed_run
    result = run_peer_reviews(
        run, None, config=tmp_config, llm=None, stage=stage, regime_labels=labels
    )
    from saa.skills.method_scoring import load_cro_reports, load_proposals

    scores = score_candidates(
        load_proposals(run),
        load_cro_reports(run),
        stage,
        load_scoring_settings(tmp_config),
        labels=labels,
    ).scores
    for (_, reviewed), item in result.reviews.items():
        assert item.body.score == pytest.approx(scores[reviewed].composite)
        assert "--no-llm" in item.body.rationale
        assert item.body.weaknesses


def test_the_model_writes_the_assessment_and_the_plan_writes_the_rest(reviewed_run, tmp_config):
    """The model is never asked who it reviews or under which framing: those come from the
    seeded plan, so a review cannot rewrite the protocol."""
    run, stage, _ = reviewed_run
    n = 2 * len(pc_agent.ROSTER)
    llm = LlmClient(FakeAnthropic([judgment_payload() for _ in range(n)]))
    result = run_peer_reviews(run, None, config=tmp_config, llm=llm, stage=stage, workers=1)
    assert len(result.reviews) == n and not result.skipped

    calls = llm._client.messages.calls
    assert all(schema_title(c) == "ReviewJudgment" for c in calls)
    for assignment in result.plan.assignments:
        body = result.reviews[assignment.pair].body
        assert body.kind is assignment.kind
        assert body.reviewer_category is assignment.reviewer_category
        assert body.score == 0.62
    first = result.plan.assignments[0]
    review = read(
        "peer_review", run.path("peer_review", agent_id=first.reviewer, reviewed=first.reviewed)
    )
    assert review.header.produced_by.value == "llm"
    assert review.header.model_calls


def test_the_review_prompt_carries_the_framing_for_its_kind(reviewed_run, tmp_config):
    run, stage, _ = reviewed_run
    n = 2 * len(pc_agent.ROSTER)
    llm = LlmClient(FakeAnthropic([judgment_payload() for _ in range(n)]))
    result = run_peer_reviews(run, None, config=tmp_config, llm=llm, stage=stage, workers=1)
    prompts = [c["messages"][0]["content"] for c in llm._client.messages.calls]
    kinds = [a.kind for a in result.plan.assignments]
    for prompt, kind in zip(prompts, kinds, strict=True):
        assert ("Audit the execution" in prompt) is (kind is ReviewKind.INTRA_CATEGORY)
        assert ("Go after the premise" in prompt) is (kind is ReviewKind.INTER_CATEGORY)


def test_a_thin_or_weakness_free_review_is_refused(reviewed_run, tmp_config):
    run, stage, _ = reviewed_run
    n = 2 * len(pc_agent.ROSTER)
    payloads = [judgment_payload(rationale="Fine.")] + [judgment_payload() for _ in range(n)]
    llm = LlmClient(FakeAnthropic(payloads), max_retries=0)
    result = run_peer_reviews(run, None, config=tmp_config, llm=llm, stage=stage, workers=1)
    assert len(result.skipped) == 1
    assert "too thin" in next(iter(result.skipped.values()))

    with pytest.raises(ValueError, match="names no weakness"):
        ReviewJudgment(**judgment_payload(weaknesses=[]))


def test_reviews_need_the_cro_reports_first(tmp_config, tmp_path, monkeypatch):
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
    with pytest.raises(FileNotFoundError, match="saa-agent cro"):
        run_peer_reviews(run, None, config=tmp_config, llm=None, stage=stage)


def test_an_explicit_seed_overrides_the_run_id(reviewed_run, tmp_config):
    run, stage, labels = reviewed_run
    a = run_peer_reviews(
        run, None, config=tmp_config, llm=None, stage=stage, regime_labels=labels, seed=7
    )
    b = run_peer_reviews(
        run, None, config=tmp_config, llm=None, stage=stage, regime_labels=labels, seed=7
    )
    assert a.plan.seed == 7
    assert [x.pair for x in a.plan.assignments] == [x.pair for x in b.plan.assignments]

"""The CIO stage (§3.6, §4.4): the ensembles, their IPS discipline, and the decision and memo.

No network and no API key: ``FakeAnthropic`` stands in for the SDK.
"""

import dataclasses

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from saa.agents.cio import judgment_model, load_candidates, run_cio, score_ensembles
from saa.agents.cio.agent import escalations
from saa.agents.cro import agent as cro_agent
from saa.agents.pc import agent as pc_agent
from saa.agents.peer_review import run_peer_reviews
from saa.agents.revision import run_revisions
from saa.agents.vote import run_vote
from saa.contracts import CioJudgment, EnsembleMethod, read
from saa.contracts.cio import BoardMemo
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.ensemble import (
    Ensemble,
    EnsembleInputs,
    backtest_sharpe_weighted,
    build_ensembles,
    default_choice,
    inverse_tracking_error,
    meta_optimization,
    project_to_policy,
    simple_average,
    single_method,
    trimmed_mean,
)
from saa.skills.method_scoring import (
    load_cro_reports,
    load_proposals,
    load_scoring_settings,
    score_candidates,
)
from tests.test_macro_agent import FakeAnthropic
from tests.test_pc_roster import RICH_IDS, rich_stage_inputs


# --------------------------------------------------------------------------------- the run
@pytest.fixture(scope="module")
def full_run(config, tmp_path_factory):
    """Every stage before the CIO, free: proposals, CRO, reviews, vote, revisions."""
    root = tmp_path_factory.mktemp("cio")
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
    run_revisions(run, None, config=cfg, llm=None, stage=stage)
    return run, stage, labels, cfg


@pytest.fixture(scope="module")
def ensemble_inputs(full_run):
    run, stage, _, _ = full_run
    tally = read("vote_tally", run.path("vote_tally")).body
    candidates = load_candidates(run, tally.shortlist)
    reports = load_cro_reports(run)
    return EnsembleInputs(
        weights=pd.DataFrame({a: pd.Series(p.weights) for a, p in candidates.items()})
        .reindex(stage.asset_ids)
        .fillna(0.0),
        stage=stage,
        backtest_sharpe={a: reports[a].backtest_sharpe for a in candidates},
        tally_composite={r.agent_id: r.composite for r in tally.rows},
        regime_fit={a: 0.5 for a in candidates},
        categories={a: p.category for a, p in candidates.items()},
    )


# ------------------------------------------------------------------------------ techniques
def test_the_simple_average_weights_every_candidate_equally(ensemble_inputs):
    w = simple_average(ensemble_inputs)
    assert list(w.values()) == pytest.approx([1 / len(ensemble_inputs.candidates)] * len(w))


def test_inverse_tracking_error_favours_the_consensus(ensemble_inputs):
    """§4.4: higher weight to "methods whose portfolios are closer to the ensemble centroid"."""
    w = inverse_tracking_error(ensemble_inputs)
    x = ensemble_inputs
    sigma = x.stage.covariance.loc[RICH_IDS, RICH_IDS].to_numpy()
    center = x.matrix.mean(axis=1)
    dist = {
        c: float(np.sqrt((x.matrix[:, i] - center) @ sigma @ (x.matrix[:, i] - center)))
        for i, c in enumerate(x.candidates)
    }
    nearest, furthest = min(dist, key=dist.get), max(dist, key=dist.get)
    assert w[nearest] > w[furthest]


def test_backtest_sharpe_weighting_gives_nothing_to_a_negative_sharpe(ensemble_inputs):
    x = dataclasses.replace(
        ensemble_inputs,
        backtest_sharpe={**ensemble_inputs.backtest_sharpe, "max_sharpe": -0.3},
    )
    assert "max_sharpe" not in backtest_sharpe_weighted(x)


def test_the_trimmed_mean_drops_the_outliers(ensemble_inputs):
    w = trimmed_mean(ensemble_inputs)
    assert len(w) == len(ensemble_inputs.candidates) - round(0.1 * len(ensemble_inputs.candidates))
    assert list(w.values()) == pytest.approx([1 / len(w)] * len(w))


def test_single_method_picks_the_top_compliant_candidate(ensemble_inputs):
    ranked = sorted(
        ensemble_inputs.tally_composite, key=lambda a: -ensemble_inputs.tally_composite[a]
    )
    assert single_method(ensemble_inputs, ranked[1:]) == {ranked[1]: 1.0}
    with pytest.raises(ValueError, match="no candidate"):
        single_method(ensemble_inputs, [])


def test_the_meta_optimisation_respects_every_ips_limit(ensemble_inputs, config):
    a = meta_optimization(ensemble_inputs, config)
    assert sum(a.values()) == pytest.approx(1.0)
    ensembles, _ = build_ensembles(ensemble_inputs, config, compliant_candidates=[])
    meta = ensembles[EnsembleMethod.META_OPTIMIZATION]
    assert meta.compliant and not meta.policy_adjusted, "verified by the CRO backtest, unadjusted"


def test_a_breaching_ensemble_is_projected_and_then_verified(ensemble_inputs, config):
    ensembles, _ = build_ensembles(ensemble_inputs, config, compliant_candidates=[])
    for e in ensembles.values():
        if e.policy_adjusted:
            assert e.compliant, "a projection is kept only if the CRO's backtest verifies it"
            assert not e.projected_from.compliance.compliant
            assert "projected into the IPS" in e.note


def test_projection_moves_an_allocation_into_the_volatility_band(ensemble_inputs, config):
    stage = ensemble_inputs.stage
    cash_heavy = pd.Series(0.0, index=RICH_IDS)
    cash_heavy["cash"] = 0.9
    cash_heavy["us_large_cap"] = 0.1
    w = project_to_policy(cash_heavy, ensemble_inputs, config).to_numpy()
    sigma = stage.covariance.loc[RICH_IDS, RICH_IDS].to_numpy()
    band = config.ips.objectives.volatility
    assert band.min_pct - 0.01 <= 100 * np.sqrt(w @ sigma @ w) <= band.max_pct + 0.01


def test_an_ensemble_reports_what_it_is_made_of(ensemble_inputs, config):
    ensembles, _ = build_ensembles(ensemble_inputs, config, compliant_candidates=[])
    e = ensembles[EnsembleMethod.SIMPLE_AVERAGE]
    n = len(ensemble_inputs.candidates)
    assert e.candidates_held == n and e.effective_candidates == pytest.approx(n)
    lead = Ensemble(e.method, {"a": 0.9, "b": 0.1}, e.final_weights, e.profile, 0.0, 0.0)
    assert lead.largest_share == ("a", 0.9) and lead.candidates_held == 2
    assert 1.0 < lead.effective_candidates < 2.0
    assert lead.projection_turnover == 0.0
    for e in ensembles.values():
        if e.policy_adjusted:
            assert 0.0 < e.projection_turnover <= 1.0


def test_ensembles_are_scored_on_the_candidates_rubric(full_run, ensemble_inputs, config):
    """§3.6: each ensemble "on the same diagnostic suite used for individual portfolios"."""
    run, stage, labels, cfg = full_run
    settings = load_scoring_settings(cfg)
    scoring = score_candidates(
        load_proposals(run), load_cro_reports(run), stage, settings, labels=labels
    )
    ensembles, _ = build_ensembles(
        ensemble_inputs, config, compliant_candidates=list(scoring.scores)
    )
    scores = score_ensembles(ensembles, scoring, stage, settings, labels)
    assert set(scores) == set(ensembles)
    single = ensembles[EnsembleMethod.SINGLE_METHOD]
    (only,) = single.ensemble_weights
    # What only a method has is inherited from the one candidate it holds.
    s, c = scores[EnsembleMethod.SINGLE_METHOD], scoring.scores[only]
    assert s.estimation_robustness == pytest.approx(c.estimation_robustness)
    assert s.cma_utilization == pytest.approx(c.cma_utilization)


def test_with_nothing_compliant_there_is_no_choice():
    with pytest.raises(ValueError, match="no ensemble is IPS-compliant"):
        default_choice({}, {})


# --------------------------------------------------------------------------------- the agent
def test_the_free_cio_recommends_a_compliant_allocation_and_writes_the_memo(full_run):
    run, stage, labels, cfg = full_run
    result = run_cio(run, None, config=cfg, llm=None, stage=stage, regime_labels=labels)
    decision = read("cio_decision", run.path("cio_decision"))
    body = decision.body
    assert body.ips_compliance.compliant
    assert sum(body.final_weights.values()) == pytest.approx(1.0)
    assert body.ensemble_method is result.chosen and result.ensembles[result.chosen].compliant
    assert len(body.method_scores) == len(pc_agent.ROSTER)
    assert body.invalidation_conditions
    memo = (run.root / "reports" / "board_memo.md").read_text(encoding="utf-8")
    assert "draft, not yet ratified" in memo
    assert decision.header.report_path == "reports/board_memo.md"
    assert (run.root / "reports" / "cio_ensembles.md").exists()


def memo_payload() -> dict:
    return {
        "recommendation": "Adopt the ensemble.",
        "expected_performance_vs_benchmark": "Above the benchmark at lower volatility.",
        "macro_rationale": "Expansion.",
        "largest_positions": "Equities and Treasuries.",
        "changes_since_last_review": "First review.",
        "key_risks": ["drawdown"],
        "rebalancing_plan": "Quarterly.",
        "ips_compliance_statement": "IPS v0.2, a draft; every hard limit is met.",
    }


def test_the_model_chooses_only_among_compliant_ensembles(full_run):
    run, stage, labels, cfg = full_run
    payload = {
        "ensemble_method": "meta_optimization",
        "rationale": "R" * 320,
        "dissenting_views": ["one"],
        "invalidation_conditions": ["a regime change"],
        "board_memo": memo_payload(),
    }
    fake = FakeAnthropic([payload])
    result = run_cio(run, None, config=cfg, llm=LlmClient(fake), stage=stage, regime_labels=labels)
    assert result.chosen is EnsembleMethod.META_OPTIMIZATION
    # §3.6's inputs: the IPS limits, the candidates with their CRO reports and peer reviews.
    prompt = fake.messages.calls[0]["messages"][0]["content"]
    assert "8% (floor) and 12% (ceiling)" in prompt
    assert "candidates held" in prompt and "largest share" in prompt
    assert "## The candidates" in prompt and "review by `" in prompt and "CRO" in prompt
    for agent_id in load_proposals(run):
        assert f"`{agent_id}`" in prompt
    decision = read("cio_decision", run.path("cio_decision"))
    assert decision.header.produced_by.value == "hybrid" and decision.header.model_calls
    assert decision.body.board_memo.ips_compliance_statement.startswith("IPS v0.2")

    model = judgment_model([EnsembleMethod.SIMPLE_AVERAGE])
    with pytest.raises(ValidationError):
        model(**{**payload, "ensemble_method": "meta_optimization"})


def test_a_thin_rationale_is_refused(full_run):
    run, stage, labels, cfg = full_run
    payload = {
        "ensemble_method": "simple_average",
        "rationale": "Looks good.",
        "invalidation_conditions": ["x"],
        "board_memo": memo_payload(),
    }
    llm = LlmClient(FakeAnthropic([payload]), max_retries=0)
    with pytest.raises(ValueError, match="too thin"):
        run_cio(run, None, config=cfg, llm=llm, stage=stage, regime_labels=labels)


def test_a_cio_must_say_what_would_make_it_wrong():
    with pytest.raises(ValidationError, match="no longer be valid"):
        CioJudgment(
            ensemble_method="simple_average",
            rationale="-",
            invalidation_conditions=[],
            board_memo=BoardMemo(**memo_payload()),
        )


def test_the_cio_needs_the_vote_first(tmp_config, tmp_path):
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    with pytest.raises(FileNotFoundError, match="saa-agent vote"):
        run_cio(run, None, config=tmp_config, llm=None)


def test_the_escalation_rules_are_evaluated_by_the_script(config):
    """Decision 53: the first paid run's memo said no rule fired at a regime confidence of 0.36,
    below the IPS's 0.40 trigger."""
    fired = escalations(config, confidence=0.36, composite=0.80)
    assert len(fired) == 1 and fired[0].startswith("regime_confidence_below")
    low = escalations(config, confidence=0.9, composite=0.2)
    assert len(low) == 1 and low[0].startswith("cio_selects_below_composite")
    assert escalations(config, confidence=None, composite=None) == []


def test_the_memo_carries_the_scripts_escalations(full_run):
    run, stage, labels, cfg = full_run
    result = run_cio(run, None, config=cfg, llm=None, stage=stage, regime_labels=labels)
    memo = (run.root / "reports" / "board_memo.md").read_text(encoding="utf-8")
    assert "## Escalations under the IPS" in memo
    assert all(e in memo for e in result.body.escalations)

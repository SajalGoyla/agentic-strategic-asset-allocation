"""The CMA judge agent (stage 2) and the PC agents (stage 4), with a stubbed model.

No network and no API key: ``FakeAnthropic`` from the macro-agent tests stands in for the SDK.
"""

import numpy as np
import pandas as pd
import pytest

from saa.agents.cma_judge import agent as judge_agent
from saa.agents.pc import agent as pc_agent
from saa.contracts import (
    CmaMethodEstimate,
    CmaMethodId,
    CmaMethodsBody,
    Producer,
    Signal,
    SignalCategory,
    SignalsBody,
    read,
)
from saa.llm import LlmClient
from saa.run import RunContext
from saa.skills.portfolio_construction import METHODS, Candidate, StageInputs, build_candidates
from tests.test_macro_agent import FakeAnthropic

ASSET = "us_large_cap"

# Exhibit 8's US Large Cap row: candidates spanning 4.0% to 12.5%, auto-blend 7.9, judge 6.8.
CANDIDATES = {
    CmaMethodId.HISTORICAL_ERP: 12.5,
    CmaMethodId.REGIME_ADJUSTED: 9.8,
    CmaMethodId.BL_EQUILIBRIUM: 9.3,
    CmaMethodId.INVERSE_GORDON: 4.3,
    CmaMethodId.IMPLIED_ERP_CAPE: 4.0,
    CmaMethodId.AUTO_BLEND: 7.9,
}


def methods_body(asset_id=ASSET, values=None, unavailable=()) -> CmaMethodsBody:
    values = values or CANDIDATES
    estimates = [
        CmaMethodEstimate(
            method=m, expected_return_pct=v, confidence=0.5, rationale="…", components={"x": v}
        )
        for m, v in values.items()
    ]
    estimates += [
        CmaMethodEstimate(method=m, confidence=0.0, rationale="…", unavailable_reason="no data")
        for m in unavailable
    ]
    return CmaMethodsBody(
        asset_id=asset_id, horizon_years=3, volatility_pct=15.2, methods=estimates
    )


def judgment_payload(expected=6.8, **overrides):
    payload = {
        "selection": "custom_blend",
        "method_weights": {
            "historical_erp": 0.05,
            "regime_adjusted": 0.20,
            "bl_equilibrium": 0.15,
            "inverse_gordon": 0.35,
            "implied_erp_cape": 0.25,
        },
        "expected_return_pct": expected,
        "confidence": "medium",
        "dispersion": "wide",
        "regime_logic": "late-cycle tilts to valuation",
        "valuation_context": "CAPE 25",
        "signal_alignment": "signals confirm",
        "rationale": "…",
    }
    payload.update(overrides)
    return payload


def signals_body(asset_id=ASSET) -> SignalsBody:
    return SignalsBody(
        asset_id=asset_id,
        signals=[
            Signal(
                name="cape",
                category=SignalCategory.VALUATION,
                score=-0.78,
                rationale="stretched",
            )
        ],
        composite_score=-0.23,
    )


@pytest.fixture
def run(tmp_config, tmp_path):
    return RunContext.create(tmp_config, run_id="testrun", root=tmp_path / "run")


def seed_asset(run, asset_id=ASSET, *, with_signals=True, **kw):
    run.write("cma_methods", "x", methods_body(asset_id, **kw), asset_id=asset_id)
    if with_signals:
        run.write("signals", "x", signals_body(asset_id), asset_id=asset_id)


# ------------------------------------------------------------------------------- evidence
def test_evidence_reads_what_the_run_has(run):
    seed_asset(run)
    evidence = judge_agent.load_evidence(run, ASSET)
    assert evidence.methods.method_range == (4.0, 12.5)
    assert evidence.dispersion.value == "wide"  # 8.5pp spread
    assert evidence.signals is not None
    assert evidence.stats is None  # not written in this run, and that is allowed


def test_missing_cma_methods_fails_with_the_command_to_run(run):
    with pytest.raises(FileNotFoundError, match="saa-skill cma-methods"):
        judge_agent.load_evidence(run, ASSET)


def test_the_prompt_carries_the_evidence_and_the_hard_constraint(run):
    seed_asset(run)
    evidence = judge_agent.load_evidence(run, ASSET)
    prompt = judge_agent.build_prompt(evidence, None, as_of=run.as_of, ips_status="draft")

    assert "must lie within [4.00, 12.50]" in prompt
    assert "historical_erp" in prompt and "12.50" in prompt  # the candidate table
    assert "cape" in prompt  # the signals table
    assert "auto-blend is 7.90%" in prompt


def test_unavailable_methods_are_shown_as_unavailable_not_omitted(run):
    seed_asset(run, unavailable=[CmaMethodId.SURVEY_CONSENSUS])
    evidence = judge_agent.load_evidence(run, ASSET)
    prompt = judge_agent.build_prompt(evidence, None, as_of=run.as_of, ips_status="draft")
    assert "unavailable: no data" in prompt
    # It must not appear in the list of methods the judge may weight.
    weightable = prompt.split("`method_weights` may only name available methods:")[1]
    assert "survey_consensus" not in weightable


def test_the_system_prompt_is_the_description_plus_the_skill():
    system = judge_agent.system_prompt()
    assert "# CMA Judge Agent" in system
    assert "# CMA Methods Skill" in system


# --------------------------------------------------------------------------------- judging
def test_judging_writes_a_readable_contract(run, tmp_config):
    seed_asset(run)
    llm = LlmClient(FakeAnthropic([judgment_payload()]))
    result = judge_agent.run_cma_judge(run, config=tmp_config, llm=llm, assets=[ASSET], workers=1)

    assert not result.failed
    body = read("cma", run.path("cma", asset_id=ASSET)).body
    assert body.expected_return_pct == pytest.approx(6.8)
    assert body.method_range == (4.0, 12.5)
    assert body.judgment.selection.value == "custom_blend"


def test_the_header_records_the_model_call_and_its_inputs(run, tmp_config):
    seed_asset(run)
    llm = LlmClient(FakeAnthropic([judgment_payload()]))
    judge_agent.run_cma_judge(run, config=tmp_config, llm=llm, assets=[ASSET], workers=1)

    header = read("cma", run.path("cma", asset_id=ASSET)).header
    assert header.produced_by is Producer.HYBRID
    assert len(header.model_calls) == 1
    assert header.cost_usd > 0
    assert {i.contract for i in header.inputs} >= {"cma_methods", "signals"}


def test_an_estimate_outside_the_candidate_range_is_rejected(run, tmp_config):
    """Exhibit 4 makes this a hard constraint, and the contract is what enforces it."""
    seed_asset(run)
    outside = judgment_payload(expected=14.0)
    llm = LlmClient(FakeAnthropic([outside, outside, outside]))
    result = judge_agent.run_cma_judge(run, config=tmp_config, llm=llm, assets=[ASSET], workers=1)

    assert ASSET in result.failed
    assert not run.path("cma", asset_id=ASSET).exists()


def test_weighting_an_unavailable_method_is_rejected(run, tmp_config):
    seed_asset(run, unavailable=[CmaMethodId.SURVEY_CONSENSUS])
    payload = judgment_payload(
        method_weights={"survey_consensus": 0.5, "historical_erp": 0.5}, expected=10.2
    )
    llm = LlmClient(FakeAnthropic([payload, payload, payload]))
    result = judge_agent.run_cma_judge(run, config=tmp_config, llm=llm, assets=[ASSET], workers=1)

    assert "unavailable methods" in result.failed[ASSET]


def test_one_failing_asset_does_not_stop_the_others(run, tmp_config):
    seed_asset(run, "us_large_cap")
    seed_asset(run, "us_value")
    # The first response is unusable; the second asset still gets a good one.
    llm = LlmClient(FakeAnthropic([judgment_payload(expected=99.0)] * 3 + [judgment_payload()]))
    result = judge_agent.run_cma_judge(
        run, config=tmp_config, llm=llm, assets=["us_large_cap", "us_value"], workers=1
    )
    assert len(result.judged) + len(result.failed) == 2
    assert result.judged or result.failed


def test_the_summary_reports_the_move_against_the_auto_blend(run, tmp_config):
    """Exhibit 8's shape: the judge's selection against the confidence-weighted blend."""
    seed_asset(run)
    llm = LlmClient(FakeAnthropic([judgment_payload()]))
    result = judge_agent.run_cma_judge(run, config=tmp_config, llm=llm, assets=[ASSET], workers=1)
    summary = judge_agent.render_summary(result)
    assert "-1.10" in summary  # 6.8 against the 7.9 auto-blend
    assert "4.0–12.5" in summary


def test_latest_cmas_feeds_the_pc_stage(run, tmp_config):
    seed_asset(run)
    llm = LlmClient(FakeAnthropic([judgment_payload()]))
    judge_agent.run_cma_judge(run, config=tmp_config, llm=llm, assets=[ASSET], workers=1)
    assert judge_agent.latest_cmas(run, tmp_config).to_dict() == {ASSET: pytest.approx(6.8)}


# ------------------------------------------------------------------------------- pc agents
IDS = ["us_large_cap", "intermediate_treasuries", "cash"]


def stage_inputs(tmp_config) -> StageInputs:
    cov = pd.DataFrame(
        [[0.0400, 0.0010, 0.0001], [0.0010, 0.0036, 0.0001], [0.0001, 0.0001, 0.0001]],
        index=IDS,
        columns=IDS,
    )
    return StageInputs(
        as_of=tmp_config.ips.ratified_on or pd.Timestamp("2026-10-01").date(),
        asset_ids=IDS,
        covariance=cov,
        expected_returns=pd.Series(
            {"us_large_cap": 0.07, "intermediate_treasuries": 0.04, "cash": 0.03}
        ),
        risk_free=0.03,
        inflation_pct=2.4,
        market_weights=pd.Series(
            {"us_large_cap": 0.6, "intermediate_treasuries": 0.3, "cash": 0.1}
        ),
        benchmark=pd.Series({"us_large_cap": 0.6, "intermediate_treasuries": 0.3, "cash": 0.1}),
        regime="expansion",
        provenance={},
        inputs=[],
        cash_id="cash",
        scenario_returns=pd.DataFrame(
            np.random.default_rng(1).multivariate_normal(
                [0.006, 0.003, 0.0025], cov.to_numpy() / 12, size=240
            ),
            columns=IDS,
        ),
    )


def test_every_method_produces_a_valid_proposal(tmp_config):
    stage = stage_inputs(tmp_config)
    candidates, skipped = build_candidates(stage, tmp_config)
    assert not skipped
    assert len(candidates) == len(METHODS)
    for candidate in candidates.values():
        body = candidate.body("a rationale long enough to be read")
        assert sum(body.weights.values()) == pytest.approx(1.0)
        assert body.ips_compliance is not None


def test_a_proposal_carries_a_real_compliance_result(tmp_config):
    """The same `check_compliance` the CRO will call, so the two cannot disagree."""
    stage = stage_inputs(tmp_config)
    candidates, _ = build_candidates(stage, tmp_config, method_ids=["inverse_variance"])
    candidate: Candidate = candidates["inverse_variance"]
    # Not a placeholder: the rules that could be evaluated at this stage were, and the ones
    # that need a backtest are reported as such rather than silently passing.
    assert candidate.compliance.not_evaluated
    assert "objectives.max_drawdown" in candidate.compliance.not_evaluated


def test_a_method_with_no_parameter_is_proposed_outside_the_band(tmp_config):
    """Decision 49. Inverse variance concentrates in cash, far below the volatility floor, and
    has no parameter that changes that without changing the method: it is not forced in."""
    stage = stage_inputs(tmp_config)
    band = tmp_config.ips.objectives.volatility
    candidates, _ = build_candidates(stage, tmp_config, method_ids=["inverse_variance"])
    candidate: Candidate = candidates["inverse_variance"]

    assert candidate.tuning is None
    assert candidate.stats.expected_volatility_pct < band.min_pct
    # The breach is reported by the same check the CRO runs; it binds on the CIO, not here.
    assert any(v.rule == "objectives.volatility" for v in candidate.compliance.violations)
    assert candidate.body("a rationale long enough to be read").tuning is None


def test_maximum_sharpe_is_tuned_along_its_own_frontier(tmp_config):
    """Its risk aversion is turned until the portfolio reaches the floor, and the portfolio is
    exactly the mean-variance solution at that risk aversion."""
    from saa.skills.portfolio_construction import mean_variance
    from saa.skills.portfolio_construction.analysis import portfolio_inputs

    stage = stage_inputs(tmp_config)
    band = tmp_config.ips.objectives.volatility
    candidate = build_candidates(stage, tmp_config, method_ids=["max_sharpe"])[0]["max_sharpe"]

    tuning = candidate.tuning_record()
    assert tuning is not None and tuning.parameter == "risk_aversion" and tuning.reached_band
    assert tuning.untuned_volatility_pct < band.min_pct
    assert candidate.stats.expected_volatility_pct == pytest.approx(band.min_pct, abs=0.01)
    assert not any(v.rule == "objectives.volatility" for v in candidate.compliance.violations)
    direct = mean_variance(portfolio_inputs(stage), tuning.value)
    pd.testing.assert_series_equal(candidate.weights, direct, atol=1e-6)
    assert candidate.body("a rationale long enough to be read").tuning == tuning


def test_cvar_is_tuned_by_a_return_target_and_still_reads_no_cma(tmp_config):
    stage = stage_inputs(tmp_config)
    band = tmp_config.ips.objectives.volatility
    candidate = build_candidates(stage, tmp_config, method_ids=["cvar_minimization"])[0][
        "cvar_minimization"
    ]
    tuning = candidate.tuning_record()
    assert tuning is not None and tuning.parameter == "minimum_return_pct"
    assert candidate.stats.expected_volatility_pct == pytest.approx(band.min_pct, abs=0.01)
    assert not candidate.method.uses_cmas


def test_a_portfolio_inside_the_band_is_not_tuned(tmp_config):
    """The band is a limit, not a target: nothing is moved that does not have to be."""
    from saa.skills.portfolio_construction import tune_toward_band
    from saa.skills.portfolio_construction.analysis import portfolio_inputs
    from saa.skills.portfolio_construction.methods import MAX_SHARPE_KNOB

    inputs = portfolio_inputs(stage_inputs(tmp_config))
    inside = pd.Series({"us_large_cap": 0.4, "intermediate_treasuries": 0.4, "cash": 0.2})
    weights, tuning = tune_toward_band(MAX_SHARPE_KNOB, inputs, inside, 0.02, 0.30)
    assert tuning is None
    pd.testing.assert_series_equal(weights, inside)


def test_a_parameter_that_cannot_reach_the_band_goes_as_far_as_it_can(tmp_config):
    from saa.skills.portfolio_construction import Knob, tune_toward_band
    from saa.skills.portfolio_construction.analysis import portfolio_inputs

    inputs = portfolio_inputs(stage_inputs(tmp_config))
    # A knob that only ever mixes treasuries and cash: at most 6% volatility.
    knob = Knob(
        parameter="share",
        description="treasury share",
        prepare=lambda _inputs: (
            lambda x: pd.Series(
                {"us_large_cap": 0.0, "intermediate_treasuries": x, "cash": 1.0 - x}
            )
        ),
        low=0.0,
        high=1.0,
        riskier_when_higher=True,
        log_scale=False,
    )
    start = pd.Series({"us_large_cap": 0.0, "intermediate_treasuries": 0.1, "cash": 0.9})
    weights, tuning = tune_toward_band(knob, inputs, start, 0.08, 0.12)
    assert tuning is not None and not tuning.reached_band
    assert tuning.value == 1.0 and weights["intermediate_treasuries"] == 1.0


def test_a_revision_applies_its_levers_and_nothing_else(tmp_config):
    """Decision 49: no IPS re-solve after the levers, so the revised weights are exactly the
    levers applied to the proposal."""
    from saa.skills.portfolio_construction.revision import RevisionLevers, apply_levers, revise

    stage = stage_inputs(tmp_config)
    candidate = build_candidates(stage, tmp_config, method_ids=["inverse_variance"])[0][
        "inverse_variance"
    ]
    proposal = candidate.body("a rationale long enough to be read")
    levers = RevisionLevers(shrink_to_equal=0.5)
    revised = revise(proposal, levers, stage, tmp_config)
    expected = apply_levers(pd.Series(proposal.weights), stage.asset_ids, levers)
    pd.testing.assert_series_equal(revised.weights, expected)


def test_no_llm_writes_a_deterministic_rationale(tmp_config):
    stage = stage_inputs(tmp_config)
    candidates, _ = build_candidates(stage, tmp_config, method_ids=["equal_weight"])
    proposal = pc_agent.propose(
        candidates["equal_weight"], stage, None, ips_status="draft", system=""
    )
    assert proposal.call is None
    assert "--no-llm" in proposal.body.rationale


def test_a_thin_rationale_is_rejected(tmp_config):
    """A proposal the peer review cannot engage with is not a proposal."""
    stage = stage_inputs(tmp_config)
    candidates, _ = build_candidates(stage, tmp_config, method_ids=["equal_weight"])
    payload = {
        "rationale": "Looks fine.",
        "key_assumption": "…",
        "main_weakness": "…",
        "when_preferred": "…",
        "invalidation": "…",
    }
    llm = LlmClient(FakeAnthropic([payload]), max_retries=0)
    with pytest.raises(ValueError, match="too thin for peer review"):
        pc_agent.propose(candidates["equal_weight"], stage, llm, ips_status="draft", system="s")


def test_the_pc_prompt_frames_the_method_honestly(tmp_config):
    stage = stage_inputs(tmp_config)
    candidates, _ = build_candidates(stage, tmp_config)
    heuristic = pc_agent.build_prompt(candidates["equal_weight"], stage, ips_status="draft")
    optimized = pc_agent.build_prompt(candidates["max_sharpe"], stage, ips_status="draft")

    assert "ignores expected returns entirely" in heuristic
    assert "inherits their estimation error" in optimized
    for prompt in (heuristic, optimized):
        assert "main_weakness" in prompt
        assert "IPS compliance" in prompt


def test_the_stats_table_reads_the_historical_stats_contract():
    # Rendered from the real model, so a renamed field fails here and not on a live run.
    from saa.contracts.asset_class import HistoricalStatsBody, RegimeStats, WindowStats

    stats = HistoricalStatsBody(
        asset_id="cash",
        name="Cash",
        group="cash",
        ticker="BIL",
        windows={
            "10y": WindowStats(
                window="10y",
                months=120,
                sufficient=True,
                annualized_return_pct=2.1,
                annualized_volatility_pct=0.5,
                sharpe_ratio=0.2,
                max_drawdown_pct=-0.3,
            )
        },
        by_regime=[
            RegimeStats(
                regime="late_cycle",
                months=60,
                annualized_mean_return_pct=2.4,
                annualized_volatility_pct=0.4,
            )
        ],
    )
    table = judge_agent._stats_table(stats)
    assert "| 10y | 2.10 | 0.50 | 0.20 | -0.30 |" in table
    assert "| late_cycle | 2.40 | 0.40 | 60 |" in table

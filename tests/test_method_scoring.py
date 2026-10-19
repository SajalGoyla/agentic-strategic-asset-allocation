"""The six-dimension metric score shared by the vote and the CIO (§3.5, §4.4).

Deterministic: no lake and no API key. The run-level test builds proposals and CRO reports from
the same synthetic stage the PC tests use.
"""

import numpy as np
import pandas as pd
import pytest

from saa.agents.cro import agent as cro_agent
from saa.agents.pc import agent as pc_agent
from saa.contracts.base import IpsCompliance, Violation
from saa.contracts.cio import SCORE_WEIGHTS
from saa.run import RunContext
from saa.skills.method_scoring import (
    RegimeFit,
    cma_alignment,
    ips_compliance_score,
    load_cro_reports,
    load_scoring_settings,
    method_id_of,
    regime_fit,
    relative_regime_fit,
    run_method_scoring,
    sharpe_to_score,
)
from tests.test_pc_roster import rich_stage_inputs


@pytest.fixture(scope="module")
def settings(config):
    return load_scoring_settings(config)


def report_with(violations, **kw):
    """A CRO report body stand-in carrying only what the scorer reads."""

    class Stub:
        ips_compliance = IpsCompliance(
            compliant=not any(v.severity == "hard" for v in violations), violations=violations
        )
        effective_n = kw.get("effective_n")
        backtest_sharpe = kw.get("backtest_sharpe")

    return Stub()


# ------------------------------------------------------------------------------ dimensions
def test_sharpe_maps_linearly_and_clips(settings):
    lo, hi = settings.sharpe_anchors
    assert sharpe_to_score(lo, settings.sharpe_anchors) == 0.0
    assert sharpe_to_score(hi, settings.sharpe_anchors) == 1.0
    assert sharpe_to_score((lo + hi) / 2, settings.sharpe_anchors) == pytest.approx(0.5)
    assert sharpe_to_score(5.0, settings.sharpe_anchors) == 1.0
    assert sharpe_to_score(-1.0, settings.sharpe_anchors) == 0.0
    assert sharpe_to_score(None, settings.sharpe_anchors) is None


def drawdown(observed):
    return Violation(
        rule="objectives.max_drawdown",
        severity="hard",
        message="-",
        observed=observed,
        limit=-25.0,
    )


def test_ips_compliance_grades_a_breach_by_its_size(settings):
    """A near miss on the drawdown limit costs less than a collapse, and neither is free."""
    s = settings.ips_compliance
    assert ips_compliance_score(report_with([]), s) == 1.0
    near = ips_compliance_score(report_with([drawdown(-26.0)]), s)
    far = ips_compliance_score(report_with([drawdown(-53.0)]), s)
    assert 1.0 - s.hard_max <= far < near <= 1.0 - s.hard_min
    assert far == pytest.approx(1.0 - s.hard_max)
    soft = Violation(rule="objectives.x", severity="soft", message="-")
    assert ips_compliance_score(report_with([soft]), s) == pytest.approx(1.0 - s.soft)


def test_relative_regime_fit_spans_the_roster():
    fits = {
        "a": RegimeFit(0.5, "measured", 100, 1.2),
        "b": RegimeFit(0.5, "measured", 100, 0.8),
        "c": RegimeFit(0.5, "measured", 100, 1.0),
        "d": RegimeFit(0.6, "prior", 10, None),
    }
    out = relative_regime_fit(fits)
    assert (out["a"].score, out["b"].score, out["c"].score) == (1.0, 0.0, pytest.approx(0.5))
    assert out["d"].score == 0.6, "a prior is not rescaled"
    single = relative_regime_fit({"a": RegimeFit(0.5, "measured", 100, 1.2)})
    assert single["a"].score == 0.5


def test_regime_fit_measures_where_history_allows_and_falls_back_otherwise(settings):
    stage = rich_stage_inputs()
    weights = pd.Series(1 / len(stage.asset_ids), index=stage.asset_ids)
    index = stage.scenario_returns.index
    labels = pd.Series(
        "expansion", index=pd.date_range("1990-01-31", periods=len(index), freq="ME")
    )
    stage.scenario_returns.index = labels.index

    measured = regime_fit(weights, "heuristic", stage, "expansion", labels, settings)
    assert measured.source == "measured" and measured.months == len(index)
    assert measured.sharpe is not None

    thin = labels.copy()
    thin.iloc[: len(thin) - 5] = "recession"
    fallback = regime_fit(weights, "risk_structured", stage, "expansion", thin, settings)
    assert fallback.source == "prior"
    assert fallback.score == settings.regime_fit.prior["expansion"]["risk_structured"]
    no_labels = regime_fit(weights, "heuristic", stage, "expansion", None, settings)
    assert no_labels.source == "prior"


def test_cma_alignment_rewards_leaning_toward_what_the_cmas_favour():
    stage = rich_stage_inputs()
    ids = stage.asset_ids
    equal = pd.Series(1 / len(ids), index=ids)
    assert cma_alignment(equal, stage) == 0.5, "equal weight leans neither way"

    vols = np.sqrt(np.diag(stage.covariance.loc[ids, ids].to_numpy()))
    attractiveness = (stage.expected_returns.reindex(ids).to_numpy() - stage.risk_free) / vols
    toward = pd.Series(attractiveness - attractiveness.min() + 0.01, index=ids)
    toward /= toward.sum()
    away = pd.Series(attractiveness.max() - attractiveness + 0.01, index=ids)
    away /= away.sum()
    assert cma_alignment(toward, stage) == pytest.approx(1.0)
    assert cma_alignment(away, stage) == pytest.approx(0.0)


def test_the_researcher_is_scored_by_the_method_it_ran():
    class Proposal:
        agent_id = "pc_researcher"
        method = "Global minimum variance"

    assert method_id_of(Proposal()) == "global_minimum_variance"


def test_settings_reject_unknown_methods(config, tmp_path):
    raw = (config.config_dir / "method_scoring.yaml").read_text(encoding="utf-8")
    path = tmp_path / "method_scoring.yaml"
    path.write_text(raw.replace("    equal_weight: 1.0", "    momentum: 1.0"), encoding="utf-8")
    with pytest.raises(ValueError, match="momentum"):
        load_scoring_settings(config, path)


# ---------------------------------------------------------------------------- whole roster
@pytest.fixture
def scored_run(tmp_config, tmp_path, monkeypatch):
    stage = rich_stage_inputs()
    labels = pd.Series(
        np.where(np.arange(len(stage.scenario_returns)) % 3 == 0, "recession", "expansion"),
        index=pd.date_range("1994-01-31", periods=len(stage.scenario_returns), freq="ME"),
    )
    stage.scenario_returns.index = labels.index
    monkeypatch.setattr(pc_agent, "gather_inputs", lambda run, store, config: stage)
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    pc_agent.run_pc_agents(run, None, config=tmp_config, llm=None)
    cro_agent.run_cro(run, None, config=tmp_config, llm=None, stage=stage)
    result = run_method_scoring(run, None, config=tmp_config, regime_labels=labels, stage=stage)
    return run, stage, result


def test_every_candidate_gets_a_valid_six_dimension_score(scored_run):
    run, _, result = scored_run
    assert set(result.scores) == set(load_cro_reports(run)) == set(pc_agent.ROSTER)
    for score in result.scores.values():
        # MethodScore validates the composite against the §4.4 weights on construction.
        expected = sum(getattr(score, dim) * w for dim, w in SCORE_WEIGHTS.items())
        assert score.composite == pytest.approx(expected, abs=1e-6)
        for dim in SCORE_WEIGHTS:
            assert 0.0 <= getattr(score, dim) <= 1.0


def test_regime_fit_is_measured_and_spread_across_the_roster(scored_run):
    _, _, result = scored_run
    fits = [s.regime_fit for s in result.scores.values()]
    assert result.regime == "expansion"  # the last label, absent a macro view
    assert all(d.regime.source == "measured" for d in result.details.values())
    assert min(fits) == 0.0 and max(fits) == 1.0


def test_the_scores_reflect_what_each_method_is(scored_run):
    _, _, result = scored_run
    s = result.scores
    # Equal weight is projected into the IPS band (decision 37), so it is near, not exactly, 1/N.
    assert s["equal_weight"].diversification == pytest.approx(1.0, abs=1e-3)
    assert s["equal_weight"].estimation_robustness > s["max_sharpe"].estimation_robustness
    assert s["max_sharpe"].cma_utilization > s["equal_weight"].cma_utilization
    ranked = result.ranked()
    assert [x.composite for x in ranked] == sorted((x.composite for x in ranked), reverse=True)


def test_scoring_needs_the_cro_reports(tmp_config, tmp_path, monkeypatch):
    stage = rich_stage_inputs()
    monkeypatch.setattr(pc_agent, "gather_inputs", lambda run, store, config: stage)
    run = RunContext.create(tmp_config, as_of="2026-10-01", run_id="r", root=tmp_path / "run")
    pc_agent.run_pc_agents(run, None, config=tmp_config, llm=None, methods=["equal_weight"])
    with pytest.raises(FileNotFoundError, match="saa-agent cro"):
        run_method_scoring(run, None, config=tmp_config, stage=stage)

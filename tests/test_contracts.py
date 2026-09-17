"""Contract tests.

Most assertions are anchored to a number or a rule the paper states, so a schema change that
silently drifts away from Ang et al. (2026) fails here rather than in Week 9.
"""

import importlib
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from saa.config import PROJECT_ROOT
from saa.contracts import (
    CONTRACTS,
    SCORE_WEIGHTS,
    TOP_N,
    AgentOutput,
    BoardMemo,
    CioDecisionBody,
    CmaBody,
    CmaJudgment,
    CmaMethodEstimate,
    CmaMethodId,
    CmaMethodsBody,
    Confidence,
    CorrelationRowBody,
    CovarianceBody,
    Dispersion,
    EnsembleMethod,
    Header,
    HistoricalStatsBody,
    IpsCompliance,
    MacroJudgment,
    MacroScores,
    MacroViewBody,
    MethodScore,
    PcCategory,
    PcProposalBody,
    PeerReviewBody,
    Producer,
    Regime,
    ReviewKind,
    SelectionMode,
    TallyRow,
    VoteBody,
    VoteTallyBody,
    WindowStats,
    json_schema,
    read,
    spec,
    write,
)
from saa.contracts.export import check, schema_files
from saa.contracts.macro import DimensionRationale, DimensionScore, IndicatorScore, Transform
from saa.ips import PortfolioMetrics, check_compliance

PAPER_SECTIONS = "Ang et al. (2026)"


# ------------------------------------------------------------------------------- fixtures
def header(contract="macro_view", agent="macro", produced_by=Producer.HYBRID):
    return Header(
        contract=contract,
        agent=agent,
        pipeline_run_id="20260915T120000Z",
        as_of=date(2026, 3, 31),
        generated_at=datetime(2026, 3, 31, 12, 0, tzinfo=UTC),
        produced_by=produced_by,
        ips_version=0.1,
        ips_status="draft",
    )


def indicator(series_id="PAYEMS", score=0.2, pit=True):
    return IndicatorScore(
        series_id=series_id,
        name=series_id,
        value=0.5,
        transform=Transform.ZSCORE,
        score=score,
        weight=0.25,
        observation_date=date(2026, 2, 28),
        available_from=date(2026, 3, 6),
        point_in_time=pit,
    )


def macro_scores():
    return MacroScores(
        lookback_years=20,
        dimensions=[
            DimensionScore(dimension=d, score=0.1, indicators=[indicator()])
            for d in ("growth", "inflation", "monetary_policy", "financial_conditions")
        ],
    )


def macro_judgment(**kw):
    defaults = dict(
        regime=Regime.LATE_CYCLE,
        regime_qualifier="with stagflationary risk",
        confidence=Confidence.MEDIUM_HIGH,
        confidence_score=0.65,
        recession_probability={"low_pct": 25.0, "high_pct": 35.0},
        dimension_rationales=[
            DimensionRationale(dimension=d, rationale="...")
            for d in ("growth", "inflation", "monetary_policy", "financial_conditions")
        ],
        key_risks=["oil supply shock"],
        narrative="...",
    )
    return MacroJudgment(**{**defaults, **kw})


def cma_methods(values=(12.5, 9.8, 9.3, 4.3, 4.0, 7.0, 7.9)):
    """Exhibit 8's US Large Cap row: 12.5 / 9.8 / 9.3 / 4.3 / 4.0, auto-blend 7.9, judge 6.8."""
    ids = [
        CmaMethodId.HISTORICAL_ERP,
        CmaMethodId.REGIME_ADJUSTED,
        CmaMethodId.BL_EQUILIBRIUM,
        CmaMethodId.INVERSE_GORDON,
        CmaMethodId.IMPLIED_ERP_CAPE,
        CmaMethodId.SURVEY_CONSENSUS,
        CmaMethodId.AUTO_BLEND,
    ]
    return CmaMethodsBody(
        asset_id="us_large_cap",
        horizon_years=3,
        volatility_pct=15.2,
        methods=[
            CmaMethodEstimate(method=m, expected_return_pct=v, confidence=0.6, rationale="...")
            for m, v in zip(ids, values, strict=True)
        ],
    )


def cma_judgment(expected=6.8):
    return CmaJudgment(
        selection=SelectionMode.CUSTOM_BLEND,
        method_weights={
            CmaMethodId.HISTORICAL_ERP: 0.05,
            CmaMethodId.REGIME_ADJUSTED: 0.20,
            CmaMethodId.BL_EQUILIBRIUM: 0.15,
            CmaMethodId.INVERSE_GORDON: 0.35,
            CmaMethodId.IMPLIED_ERP_CAPE: 0.25,
        },
        expected_return_pct=expected,
        confidence=Confidence.MEDIUM,
        dispersion=Dispersion.WIDE,
        regime_logic="late-cycle: tilt valuation and regime-adjusted",
        valuation_context="CAPE 25",
        signal_alignment="signals confirm",
        rationale="...",
    )


# ------------------------------------------------------------------------------- registry
def test_every_output_file_the_paper_names_is_registered():
    """Exhibit 3 lists the asset-class agent's outputs; §3.2 names macro-view.json."""
    filenames = {s.filename for s in CONTRACTS.values()}
    assert {
        "cma_methods.json",
        "cma.json",
        "signals.json",
        "historical_stats.json",
        "scenarios.json",
        "correlation_row.json",
        "macro-view.json",
    } <= filenames


def test_script_generated_contracts_have_no_judgment_model():
    """§3.3: the seven CMA candidates are written by a Python script, "no LLM judgment is
    involved up to this point"."""
    assert spec("cma_methods").judgment is None
    assert spec("cma_methods").produced_by is Producer.SCRIPT
    assert spec("cma").judgment is not None


def test_schemas_are_strict_and_fully_required():
    """Strict structured outputs need additionalProperties:false and every property required."""
    for name, entry in CONTRACTS.items():
        if entry.judgment is None:
            continue
        schema = json_schema(name, judgment=True)
        for obj in [schema, *schema.get("$defs", {}).values()]:
            if obj.get("type") == "object" and "properties" in obj:
                assert obj.get("additionalProperties") is False, name
                assert set(obj["required"]) == set(obj["properties"]), name


def test_committed_schemas_are_current():
    """`uv run saa-contracts` must have been re-run after any model change."""
    assert check(PROJECT_ROOT / "schemas") == []


def test_judgment_schema_excludes_the_header():
    """The harness writes provenance and token counts; the model must not be able to."""
    judgment = json_schema("macro_view", judgment=True)
    assert "header" not in judgment["properties"]
    assert "provenance" not in judgment["properties"]
    assert "header" in json_schema("macro_view")["properties"]


# ---------------------------------------------------------------------------------- macro
def test_macro_view_round_trips(tmp_path):
    body = MacroViewBody(scores=macro_scores(), judgment=macro_judgment())
    output = AgentOutput[MacroViewBody](header=header(), body=body)
    path = write(output, tmp_path / "macro-view.json")
    reloaded = read("macro_view", path)
    assert reloaded.body.judgment.regime is Regime.LATE_CYCLE
    assert reloaded.body.judgment.recession_probability.high_pct == 35.0


def test_macro_scores_require_all_four_dimensions():
    """§3.2: growth, inflation, monetary policy and financial conditions."""
    with pytest.raises(ValidationError, match="missing dimensions"):
        MacroScores(
            lookback_years=20,
            dimensions=[DimensionScore(dimension="growth", score=0.0, indicators=[indicator()])],
        )


def test_macro_judgment_requires_a_rationale_per_dimension():
    with pytest.raises(ValidationError, match="no rationale given"):
        macro_judgment(dimension_rationales=[DimensionRationale(dimension="growth", rationale="x")])


def test_recession_probability_range_is_ordered():
    with pytest.raises(ValidationError):
        macro_judgment(recession_probability={"low_pct": 40.0, "high_pct": 20.0})


def test_pit_quality_reports_vintage_coverage():
    scores = MacroScores(
        lookback_years=20,
        dimensions=[
            DimensionScore(
                dimension=d,
                score=0.0,
                indicators=[indicator("PAYEMS", pit=True), indicator("UNRATE", pit=False)],
            )
            for d in ("growth", "inflation", "monetary_policy", "financial_conditions")
        ],
        pit_quality=[{"dimension": "growth", "indicators_total": 2, "indicators_point_in_time": 1}],
    )
    assert scores.pit_quality[0].fraction == 0.5


# ------------------------------------------------------------------------------------ cma
def test_cma_methods_must_include_the_auto_blend():
    methods = cma_methods()
    methods.methods = [m for m in methods.methods if m.method != CmaMethodId.AUTO_BLEND]
    with pytest.raises(ValidationError, match="auto-blend"):
        CmaMethodsBody(**methods.model_dump())


def test_cma_method_range_matches_exhibit_8():
    assert cma_methods().method_range == (4.0, 12.5)


def test_judge_estimate_must_lie_within_the_method_range():
    """Exhibit 4: "final estimate MUST be within [min_method, max_method]"."""
    low, high = cma_methods().method_range

    ok = CmaBody(
        asset_id="us_large_cap",
        horizon_years=3,
        expected_return_pct=6.8,  # Exhibit 8's judge selection for US Large Cap
        volatility_pct=15.2,
        method_range=(low, high),
        judgment=cma_judgment(6.8),
    )
    assert ok.expected_return_pct == 6.8

    with pytest.raises(ValidationError, match="outside the candidate range"):
        CmaBody(
            asset_id="us_large_cap",
            horizon_years=3,
            expected_return_pct=14.0,
            volatility_pct=15.2,
            method_range=(low, high),
            judgment=cma_judgment(14.0),
        )


def test_cma_method_weights_must_sum_to_one():
    payload = cma_judgment().model_dump()
    payload["method_weights"] = {CmaMethodId.HISTORICAL_ERP.value: 0.5}
    with pytest.raises(ValidationError, match="method weights sum to 0.5000"):
        CmaJudgment.model_validate(payload)


def test_single_method_selection_must_weight_exactly_one_method():
    """Exhibit 4 step 5 offers three selection modes; the mode and the weights must agree."""
    payload = cma_judgment().model_dump()
    payload["selection"] = SelectionMode.SINGLE_METHOD.value
    with pytest.raises(ValidationError, match="single_method selection has 5"):
        CmaJudgment.model_validate(payload)


def test_dispersion_thresholds_follow_exhibit_4():
    """ "tight <3pp / moderate 3-6pp / wide >6pp"."""
    assert Dispersion.classify(2.9) is Dispersion.TIGHT
    assert Dispersion.classify(3.0) is Dispersion.MODERATE
    assert Dispersion.classify(6.0) is Dispersion.MODERATE
    assert Dispersion.classify(6.1) is Dispersion.WIDE
    # Exhibit 8's US Large Cap spread is 8.5pp.
    low, high = cma_methods().method_range
    assert Dispersion.classify(high - low) is Dispersion.WIDE


def test_correlation_row_rejects_impossible_values():
    with pytest.raises(ValidationError, match=r"outside \[-1, 1\]"):
        CorrelationRowBody(
            asset_id="gold", months={"10y": 120}, correlations={"10y": {"reits": 1.4}}
        )
    with pytest.raises(ValidationError, match="self-correlation"):
        CorrelationRowBody(
            asset_id="gold", months={"10y": 120}, correlations={"10y": {"gold": 0.8}}
        )
    with pytest.raises(ValidationError, match="no month count"):
        CorrelationRowBody(
            asset_id="gold", months={"10y": 120}, correlations={"5y": {"reits": 0.3}}
        )


def test_correlation_row_allows_nulls_for_short_windows():
    """The skill returns null rather than a spurious number when a window lacks history."""
    row = CorrelationRowBody(
        asset_id="gold",
        months={"1y": 12, "10y": 0},
        correlations={"1y": {"reits": 0.31, "gold": 1.0}, "10y": {"reits": None}},
    )
    assert row.correlations["10y"]["reits"] is None


def test_the_skill_builds_these_contracts_rather_than_its_own_models():
    """`saa.skills.historical_analysis` used to carry draft copies of these models, which said
    they "move into the shared output-contract package once the project schemas are agreed".
    They have moved: the skill now constructs the contracts directly, so there is one
    definition and nothing to drift. End-to-end validation lives in test_historical_analysis.py.
    """
    from saa.contracts import CorrelationRowBody, HistoricalStatsBody
    from saa.skills.historical_analysis import analysis as skill

    assert skill.HistoricalStatsBody is HistoricalStatsBody
    assert skill.CorrelationRowBody is CorrelationRowBody
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("saa.skills.historical_analysis.models")


def test_historical_stats_window_keys_must_agree():
    with pytest.raises(ValidationError, match="window keys disagree"):
        HistoricalStatsBody(
            asset_id="gold",
            name="Gold",
            group="real_assets",
            ticker="GLD",
            windows={"10y": WindowStats(window="5y")},
        )


# ------------------------------------------------------------------------------ portfolio
def test_covariance_must_be_square_and_symmetric():
    ok = CovarianceBody(
        asset_ids=["a", "b"],
        method="sample",
        window_years=10,
        matrix=[[0.04, 0.01], [0.01, 0.02]],
        volatilities_pct={"a": 20.0, "b": 14.1},
    )
    assert len(ok.matrix) == 2

    with pytest.raises(ValidationError, match="not symmetric"):
        CovarianceBody(
            asset_ids=["a", "b"],
            method="sample",
            window_years=10,
            matrix=[[0.04, 0.01], [0.03, 0.02]],
            volatilities_pct={"a": 20.0, "b": 14.1},
        )


def test_pc_proposal_must_be_fully_invested():
    with pytest.raises(ValidationError, match="expected 1.0"):
        PcProposalBody(
            agent_id="equal_weight",
            method="Equal weight (1/N)",
            category=PcCategory.HEURISTIC,
            weights={"us_large_cap": 0.5},
            expected_return_pct=6.0,
            expected_volatility_pct=9.0,
            sharpe_ratio=0.4,
            ips_compliance=IpsCompliance(compliant=True),
            rationale="...",
        )


def test_pc_proposal_embeds_a_real_compliance_report(config):
    weights = {
        "us_large_cap": 0.30,
        "intl_developed": 0.20,
        "intermediate_treasuries": 0.30,
        "short_treasuries": 0.10,
        "cash": 0.10,
    }
    report = check_compliance(
        weights, PortfolioMetrics(expected_volatility_pct=9.5), config.ips, config.universe
    )
    proposal = PcProposalBody(
        agent_id="risk_parity",
        method="Risk parity",
        category=PcCategory.RISK_STRUCTURED,
        weights=weights,
        expected_return_pct=6.0,
        expected_volatility_pct=9.5,
        sharpe_ratio=0.4,
        ips_compliance=IpsCompliance.from_report(report),
        rationale="...",
    )
    # us_large_cap at 30% breaches the 25% per-asset cap; the contract carries that verbatim.
    assert proposal.ips_compliance.compliant is False
    assert any(v.rule == "bounds.per_asset" for v in proposal.ips_compliance.violations)


# --------------------------------------------------------------------------------- review
def test_peer_review_kind_must_match_the_categories():
    """§3.5 pairs one intra-category and one inter-category review per agent."""
    with pytest.raises(ValidationError, match="categories say"):
        PeerReviewBody(
            reviewer_agent_id="risk_parity",
            reviewer_category=PcCategory.RISK_STRUCTURED,
            reviewed_agent_id="hrp",
            reviewed_category=PcCategory.RISK_STRUCTURED,
            kind=ReviewKind.INTER_CATEGORY,
            strengths=["..."],
            weaknesses=["..."],
            score=0.7,
            rationale="...",
        )


def test_an_agent_cannot_review_itself():
    with pytest.raises(ValidationError, match="cannot review itself"):
        PeerReviewBody(
            reviewer_agent_id="risk_parity",
            reviewer_category=PcCategory.RISK_STRUCTURED,
            reviewed_agent_id="risk_parity",
            reviewed_category=PcCategory.RISK_STRUCTURED,
            kind=ReviewKind.INTRA_CATEGORY,
            strengths=["..."],
            weaknesses=["..."],
            score=0.7,
            rationale="...",
        )


def test_borda_ballot_awards_5_4_3_2_1_and_minus_2():
    vote = VoteBody(
        voter_agent_id="equal_weight",
        top_five=["max_div", "black_litterman", "risk_parity", "hrp", "tail_risk_parity"],
        bottom_flag="adversarial_diversifier",
        rationale="...",
    )
    points = vote.points()
    assert points["max_div"] == 5
    assert points["tail_risk_parity"] == 1
    assert points["adversarial_diversifier"] == -2


def test_ballot_excludes_the_voter():
    with pytest.raises(ValidationError, match="ranked itself"):
        VoteBody(
            voter_agent_id="max_div",
            top_five=["max_div", "black_litterman", "risk_parity", "hrp", "tail_risk_parity"],
            rationale="...",
        )


def tally_rows():
    """Exhibit 9's top five: max diversification, BL, risk parity, HRP, tail risk parity."""
    data = [
        ("max_div", "Maximum Diversification", PcCategory.RISK_STRUCTURED, 96, 0.553, 1.000, 1),
        ("black_litterman", "Black-Litterman", PcCategory.RETURN_OPTIMIZED, 76, 0.551, 0.936, 2),
        ("risk_parity", "Risk Parity", PcCategory.RISK_STRUCTURED, 42, 0.503, 0.750, 3),
        ("hrp", "Hierarchical Risk Parity", PcCategory.RISK_STRUCTURED, 41, 0.497, 0.737, 4),
        ("tail_risk_parity", "Tail Risk Parity", PcCategory.NON_TRADITIONAL, 22, 0.510, 0.702, 5),
    ]
    return [
        TallyRow(
            agent_id=a, method=m, category=c, vote_points=v, metric_score=s, composite=x, rank=r
        )
        for a, m, c, v, s, x, r in data
    ]


def test_vote_tally_reproduces_exhibit_9_top_five():
    tally = VoteTallyBody(
        rows=tally_rows(),
        shortlist=["max_div", "black_litterman", "risk_parity", "hrp", "tail_risk_parity"],
        regime="late_cycle",
        vote_weight=0.6,
        metric_weight=0.4,
        diversity_categories=3,
    )
    assert len(tally.shortlist) == TOP_N
    assert tally.rows[0].agent_id == "max_div"


def test_diversity_constraint_is_enforced():
    """§3.5: "at least three of the four families"."""
    rows = tally_rows()
    rows[4] = rows[4].model_copy(update={"category": PcCategory.RISK_STRUCTURED})
    with pytest.raises(ValidationError, match="at least 3"):
        VoteTallyBody(
            rows=rows,
            shortlist=["max_div", "black_litterman", "risk_parity", "hrp", "tail_risk_parity"],
            regime="late_cycle",
            vote_weight=0.6,
            metric_weight=0.4,
            diversity_categories=2,
        )


# ------------------------------------------------------------------------------------ cio
def test_cio_composite_must_match_the_section_4_4_rubric():
    assert sum(SCORE_WEIGHTS.values()) == pytest.approx(1.0)
    scores = dict(
        backtest_sharpe=0.6,
        ips_compliance=1.0,
        diversification=0.8,
        regime_fit=0.7,
        estimation_robustness=0.5,
        cma_utilization=0.4,
    )
    composite = sum(scores[k] * w for k, w in SCORE_WEIGHTS.items())
    assert MethodScore(agent_id="a", **scores, composite=composite).composite == composite

    with pytest.raises(ValidationError, match="weighted rubric"):
        MethodScore(agent_id="a", **scores, composite=0.99)


def cio_body(**kw):
    defaults = dict(
        ensemble_method=EnsembleMethod.INVERSE_TRACKING_ERROR,
        ensemble_weights={"max_div": 0.5, "risk_parity": 0.5},
        final_weights={"us_large_cap": 0.6, "intermediate_treasuries": 0.4},
        method_scores=[],
        expected_return_pct=6.87,
        expected_volatility_pct=7.54,
        sharpe_ratio=0.43,
        effective_n=11.2,
        ex_ante_tracking_error_pct=2.41,
        ips_compliance=IpsCompliance(compliant=True),
        invalidation_conditions=["regime shifts to recession"],
        rationale="...",
        board_memo=BoardMemo(
            recommendation="...",
            expected_performance_vs_benchmark="...",
            macro_rationale="...",
            largest_positions="...",
            changes_since_last_review="...",
            key_risks=["..."],
            rebalancing_plan="...",
            ips_compliance_statement="...",
        ),
    )
    return CioDecisionBody(**{**defaults, **kw})


def test_cio_decision_accepts_the_section_4_4_figures():
    body = cio_body()
    assert body.effective_n == 11.2
    assert body.ex_ante_tracking_error_pct == 2.41


def test_cio_may_not_ship_a_non_compliant_allocation():
    """§3.6: IPS compliance "is non-negotiable"."""
    breach = IpsCompliance(
        compliant=False,
        violations=[
            {
                "rule": "objectives.volatility",
                "severity": "hard",
                "message": "expected volatility 7.54% outside the 8.0-12.0% band",
            }
        ],
    )
    with pytest.raises(ValidationError, match="non-negotiable"):
        cio_body(ips_compliance=breach)


def test_board_memo_covers_every_section_the_paper_requires():
    """§3.6 lists the memo's required contents; a missing section must fail, not pass."""
    required = set(BoardMemo.model_fields)
    assert required == {
        "recommendation",
        "expected_performance_vs_benchmark",
        "macro_rationale",
        "largest_positions",
        "changes_since_last_review",
        "key_risks",
        "rebalancing_plan",
        "ips_compliance_statement",
    }
    with pytest.raises(ValidationError):
        BoardMemo(recommendation="only this")


def test_schema_export_covers_every_contract():
    files = schema_files()
    for name, entry in CONTRACTS.items():
        assert f"{name}.schema.json" in files
        assert (f"{name}.judgment.schema.json" in files) is (entry.judgment is not None)

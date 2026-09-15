import pytest

from saa.ips import HARD, SOFT, PortfolioMetrics, check_compliance, real_return_pct

# Ang, Azimbayev & Kim (2026) Exhibit 11: the final allocation from the paper's March 2026 run.
# Weights are reported to one decimal and sum to 99.8%, so tests that are not about the
# fully-invested rule normalise first.
PAPER_PORTFOLIO = {
    "intl_developed": 0.159,
    "intermediate_treasuries": 0.147,
    "us_large_cap": 0.089,
    "long_treasuries": 0.084,
    "cash": 0.081,
    "short_treasuries": 0.073,
    "us_value": 0.072,
    "emerging_markets": 0.049,
    "intl_sovereigns": 0.048,
    "us_growth": 0.044,
    "us_small_cap": 0.036,
    "ig_corporates": 0.024,
    "gold": 0.021,
    "hy_corporates": 0.016,
    "commodities": 0.016,
    "reits": 0.014,
    "intl_corporates": 0.013,
    "usd_em_debt": 0.012,
}

# §4.4: "an expected return of 6.87%, volatility of 7.54% ... The ex-ante tracking error
# versus a 60/40 benchmark is 2.41%" and a backtest "maximum drawdown (-25.6% ...)".
PAPER_METRICS = PortfolioMetrics(
    expected_return_pct=6.87,
    expected_inflation_pct=2.4,  # §4.1: "CPI 2.4%"
    expected_volatility_pct=7.54,
    max_drawdown_pct=-25.6,
    ex_ante_tracking_error_pct=2.41,
)


def normalised(weights):
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


@pytest.fixture
def ips(config):
    return config.ips


@pytest.fixture
def universe(config):
    return config.universe


def rules(report):
    return {v.rule for v in report.violations}


# --------------------------------------------------------------------------- policy loading
def test_ips_loads_and_matches_the_paper(ips):
    assert ips.objectives.return_.min_pct == 3.0
    assert ips.objectives.return_.max_pct == 4.0
    assert (ips.objectives.volatility.min_pct, ips.objectives.volatility.max_pct) == (8.0, 12.0)
    assert ips.objectives.max_drawdown.limit_pct == -25.0
    assert ips.active_risk.tracking_error.max_ex_ante_pct == 6.0
    assert ips.objectives.cma_horizon_years == 3


def test_draft_status_is_visible_to_agents(ips):
    # Agents must be able to say they ran against an unratified policy.
    assert ips.is_draft is (ips.status == "draft")


def test_benchmark_is_a_measuring_stick_not_a_candidate_portfolio(ips, universe):
    """The 60/40 benchmark is deliberately more concentrated than the IPS lets a *portfolio* be.

    A 60% single-asset weight would be a hard violation for a PC agent's proposal, but the
    benchmark is a reference index, not an allocation the IPS governs. Load-time validation
    therefore checks only that it is well-formed, and `check_compliance` is never applied to
    it. Pinned here so nobody "fixes" the per-asset cap to accommodate the benchmark.
    """
    report = check_compliance(ips.active_risk.benchmark.weights, None, ips, universe)
    assert {v.entity for v in report.violations if v.rule == "bounds.per_asset"} == {
        "us_large_cap",
        "intermediate_treasuries",
    }


# ------------------------------------------------------------------------ structural rules
def test_paper_portfolio_satisfies_every_structural_rule(ips, universe):
    report = check_compliance(normalised(PAPER_PORTFOLIO), None, ips, universe)
    assert report.violations == []


def test_rounded_weights_fail_the_fully_invested_check(ips, universe):
    # Exhibit 11 as printed sums to 99.8%.
    report = check_compliance(PAPER_PORTFOLIO, None, ips, universe)
    assert rules(report) == {"universe.fully_invested"}
    assert report.compliant is False


def test_unknown_asset_is_rejected(ips, universe):
    weights = normalised(PAPER_PORTFOLIO) | {"bitcoin": 0.0}
    report = check_compliance(weights, None, ips, universe)
    assert "universe.membership" in rules(report)


def test_short_position_is_rejected_when_long_only(ips, universe):
    weights = normalised(PAPER_PORTFOLIO) | {"gold": -0.02, "cash": 0.102}
    report = check_compliance(weights, None, ips, universe)
    assert "universe.long_only" in rules(report)


def test_short_position_allowed_when_the_ips_permits_it(ips, universe):
    relaxed = ips.model_copy(deep=True)
    relaxed.universe.permitted.long_only = False
    weights = normalised(PAPER_PORTFOLIO) | {"gold": -0.02, "cash": 0.102}
    assert "universe.long_only" not in rules(check_compliance(weights, None, relaxed, universe))


def test_leverage_is_rejected(ips, universe):
    relaxed = ips.model_copy(deep=True)
    relaxed.universe.permitted.long_only = False
    weights = {"us_large_cap": 1.4, "intermediate_treasuries": -0.4}
    report = check_compliance(weights, None, relaxed, universe)
    assert "universe.leverage" in rules(report)


def test_per_asset_cap(ips, universe):
    # Only us_large_cap breaches the 25% cap; every group bound is satisfied.
    weights = {
        "us_large_cap": 0.30,
        "intl_developed": 0.20,
        "intermediate_treasuries": 0.25,
        "short_treasuries": 0.15,
        "cash": 0.10,
    }
    report = check_compliance(weights, None, ips, universe)
    assert rules(report) == {"bounds.per_asset"}
    violation = report.violations[0]
    assert violation.entity == "us_large_cap"
    assert violation.severity == HARD
    assert violation.limit == 0.25


def test_per_group_floor_and_cap(ips, universe):
    # All-equity: breaches the equity cap and every other group's floor.
    report = check_compliance(
        {
            "us_large_cap": 0.2,
            "us_value": 0.2,
            "us_growth": 0.2,
            "us_small_cap": 0.2,
            "intl_developed": 0.2,
        },
        None,
        ips,
        universe,
    )
    entities = {v.entity for v in report.violations if v.rule == "bounds.per_group"}
    assert "equity" in entities and "fixed_income" in entities


# ------------------------------------------------------------- objectives and active risk
def test_real_return_is_fisher_exact():
    assert real_return_pct(6.87, 2.4) == pytest.approx(4.365, abs=1e-3)


def test_return_target_is_soft_and_does_not_disqualify(ips, universe):
    metrics = PortfolioMetrics(
        expected_return_pct=4.0,
        expected_inflation_pct=2.4,
        expected_volatility_pct=10.0,
        max_drawdown_pct=-10.0,
        ex_ante_tracking_error_pct=2.0,
    )
    report = check_compliance(normalised(PAPER_PORTFOLIO), metrics, ips, universe)
    violation = next(v for v in report.violations if v.rule == "objectives.return")
    assert violation.severity == SOFT
    assert report.compliant is True


def test_volatility_band_is_breached_on_both_sides(ips, universe):
    weights = normalised(PAPER_PORTFOLIO)
    for vol in (6.0, 14.0):
        metrics = PortfolioMetrics(expected_volatility_pct=vol)
        report = check_compliance(weights, metrics, ips, universe)
        assert "objectives.volatility" in rules(report)
        assert report.compliant is False


def test_drawdown_and_tracking_error_are_hard(ips, universe):
    metrics = PortfolioMetrics(max_drawdown_pct=-31.0, ex_ante_tracking_error_pct=7.5)
    report = check_compliance(normalised(PAPER_PORTFOLIO), metrics, ips, universe)
    assert {"objectives.max_drawdown", "active_risk.tracking_error"} <= rules(report)
    assert all(v.severity == HARD for v in report.violations)


def test_missing_metrics_are_reported_not_passed(ips, universe):
    report = check_compliance(normalised(PAPER_PORTFOLIO), None, ips, universe)
    assert set(report.not_evaluated) == {
        "objectives.return",
        "objectives.volatility",
        "objectives.max_drawdown",
        "active_risk.tracking_error",
    }
    # No hard violations, but nothing was actually verified either.
    assert report.compliant is True


def test_report_serialises_for_agent_output(ips, universe):
    report = check_compliance(PAPER_PORTFOLIO, PAPER_METRICS, ips, universe)
    payload = report.to_dict()
    assert set(payload) == {"compliant", "violations", "not_evaluated"}
    assert all(set(v) >= {"rule", "severity", "message"} for v in payload["violations"])


# ---------------------------------------------------------------------------------- caveat
def test_the_papers_own_portfolio_breaches_three_of_its_own_limits(ips, universe):
    """Ang et al.'s published allocation fails the IPS stated in the same paper.

    §4 sets a volatility band of 8-12%, a drawdown limit of -25%, and a target real return of
    CPI + 3-4%. §4.4 reports the final portfolio at 7.54% volatility with a -25.6% backtest
    drawdown, and 6.87% nominal against the §4.1 CPI of 2.4% -- 4.37% real. Encoding the
    paper's wording faithfully therefore disqualifies the paper's own result.

    Structurally the portfolio is fine, and tracking error (2.41% vs. a 6% budget) has plenty
    of room. The three breaches are policy questions for faculty, not bugs:

    * Volatility 7.54% is *below* the band. Being less risky than policy contemplates is not
      obviously a fiduciary breach -- a case for making the band's lower bound soft.
    * Drawdown -25.6% breaches -25%, but that is a 1996-2026 backtest figure, not an ex-ante
      estimate. Whether the limit binds ex-ante or on the backtest needs deciding.
    * Real return 4.37% is above the 3-4% band, which conflicts with the below-band
      volatility -- the portfolio is forecast to earn more while risking less.

    See docs/ips.md. Pinned as a test so the tension is visible before the CRO agent (Wk 7)
    starts rejecting candidates on these rules.
    """
    report = check_compliance(normalised(PAPER_PORTFOLIO), PAPER_METRICS, ips, universe)
    assert rules(report) == {
        "objectives.volatility",
        "objectives.max_drawdown",
        "objectives.return",
    }
    assert {v.rule for v in report.hard} == {"objectives.volatility", "objectives.max_drawdown"}
    assert {v.rule for v in report.soft} == {"objectives.return"}
    assert report.compliant is False
    assert "active_risk.tracking_error" not in rules(report)

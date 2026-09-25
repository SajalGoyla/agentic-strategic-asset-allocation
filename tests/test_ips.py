import pytest
from pydantic import ValidationError

from saa.ips import (
    HARD,
    Bound,
    PortfolioMetrics,
    UniverseBounds,
    check_compliance,
    real_return_pct,
)

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


def test_the_policy_is_still_a_draft(ips):
    """Faculty answered the open questions on 2026-09-25 but did not sign the document off.

    Answering individual questions is not ratification, so agents keep recording that they ran
    against a draft until someone explicitly ratifies it.
    """
    assert ips.status == "draft"
    assert ips.ratified_by is None and ips.ratified_on is None
    assert ips.is_draft is True


def test_ratifying_requires_a_signatory_and_a_date(ips):
    payload = ips.model_dump(by_alias=True)
    with pytest.raises(ValidationError, match="needs both ratified_by and ratified_on"):
        type(ips).model_validate({**payload, "status": "ratified"})


def test_benchmark_matches_the_split_faculty_chose(ips):
    """Faculty, 2026-09-25: equity as proposed, bonds 75% Intermediate Treasuries / 25% IG.

    All three legs sit inside the 18-asset universe, so tracking error is computed from the
    same covariance matrix the PC agents use rather than needing a 19th row.
    """
    weights = ips.active_risk.benchmark.weights
    assert weights == {
        "us_large_cap": 0.60,
        "intermediate_treasuries": 0.30,
        "ig_corporates": 0.10,
    }
    bond_sleeve = weights["intermediate_treasuries"] + weights["ig_corporates"]
    assert bond_sleeve == pytest.approx(0.40)
    assert weights["intermediate_treasuries"] / bond_sleeve == pytest.approx(0.75)


def test_benchmark_is_a_measuring_stick_not_a_candidate_portfolio(ips, universe):
    """The benchmark is a reference index, not an allocation the IPS governs.

    Load-time validation checks only that it is well-formed; `check_compliance` is never
    applied to it. Pinned so the distinction survives any future reintroduction of bounds.
    """
    report = check_compliance(ips.active_risk.benchmark.weights, None, ips, universe)
    assert [v.rule for v in report.violations] == []


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


def test_the_policy_sets_no_weight_limits(ips, universe):
    """Faculty, 2026-09-25: "Since the assets are really asset classes, I\'m not sure we need
    weight limits -- why rule out the possibility of going all in on one asset class."

    The binding constraints are the volatility band, the drawdown limit and tracking error.
    """
    assert ips.has_weight_bounds is False
    assert ips.universe.bounds is None
    assert ips.group_bound("equity") is None

    # An all-equity portfolio is structurally legal; only the risk limits can reject it.
    all_equity = {"us_large_cap": 0.5, "intl_developed": 0.5}
    assert check_compliance(all_equity, None, ips, universe).violations == []


def test_bounds_still_bind_if_a_future_policy_reintroduces_them(ips, universe):
    """The machinery is retained, not deleted, so bounds can come back without a code change."""
    bounded = ips.model_copy(deep=True)
    bounded.universe.bounds = UniverseBounds(
        per_asset=Bound(min=0.0, max=0.25),
        per_group={
            "equity": Bound(min=0.30, max=0.70),
            "fixed_income": Bound(min=0.20, max=0.60),
            "real_assets": Bound(min=0.0, max=0.15),
            "cash": Bound(min=0.0, max=0.15),
        },
    )
    report = check_compliance({"us_large_cap": 0.5, "intl_developed": 0.5}, None, bounded, universe)
    assert {v.rule for v in report.violations} == {"bounds.per_asset", "bounds.per_group"}


def test_rebalancing_is_calendar_only(ips):
    """Faculty, 2026-09-25: skip drift triggers, since a trigger needs a stated remedy."""
    assert ips.rebalancing.cadence == "quarterly"
    assert ips.rebalancing.drift_trigger_pct is None


# ------------------------------------------------------------- objectives and active risk
def test_real_return_is_fisher_exact():
    assert real_return_pct(6.87, 2.4) == pytest.approx(4.365, abs=1e-3)


def test_every_ips_limit_is_hard(ips, universe):
    """Faculty, 2026-09-25, asked how strictly the pipeline should hold to the IPS limits:
    "treat them as hard constraints". Every limit binds, the return target included.
    """
    assert ips.objectives.return_.severity == HARD
    assert ips.objectives.volatility.severity == HARD
    assert ips.objectives.max_drawdown.severity == HARD
    assert ips.active_risk.tracking_error.severity == HARD

    metrics = PortfolioMetrics(
        expected_return_pct=4.0,
        expected_inflation_pct=2.4,
        expected_volatility_pct=10.0,
        max_drawdown_pct=-10.0,
        ex_ante_tracking_error_pct=2.0,
    )
    report = check_compliance(normalised(PAPER_PORTFOLIO), metrics, ips, universe)
    violation = next(v for v in report.violations if v.rule == "objectives.return")
    assert violation.severity == HARD
    assert report.compliant is False


def test_the_return_target_binds_from_above_as_well_as_below(ips, universe):
    """A consequence worth seeing: earning MORE than CPI + 4% disqualifies a portfolio too."""
    over = PortfolioMetrics(expected_return_pct=8.0, expected_inflation_pct=2.4)
    under = PortfolioMetrics(expected_return_pct=4.0, expected_inflation_pct=2.4)
    weights = normalised(PAPER_PORTFOLIO)
    for metrics in (over, under):
        report = check_compliance(weights, metrics, ips, universe)
        assert "objectives.return" in rules(report)
        assert report.compliant is False


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
    of room.

    Resolved by faculty on 2026-09-25: "Those look like cases of bad rounding. Let's treat them
    as hard constraints." All three limits therefore bind -- on both sides of each band, and on
    the backtest as well as ex-ante -- and we accept that the paper's own published figures
    would not clear them.

    Kept as a test because it is the clearest statement of what the CRO agent will enforce from
    Week 7, and because relaxing any of the three should have to change a test that says why.
    """
    report = check_compliance(normalised(PAPER_PORTFOLIO), PAPER_METRICS, ips, universe)
    assert rules(report) == {
        "objectives.volatility",
        "objectives.max_drawdown",
        "objectives.return",
    }
    assert {v.rule for v in report.hard} == {
        "objectives.volatility",
        "objectives.max_drawdown",
        "objectives.return",
    }
    assert report.soft == []
    assert report.compliant is False
    assert "active_risk.tracking_error" not in rules(report)

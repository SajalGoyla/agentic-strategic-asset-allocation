"""Tests for the deterministic macro-regime skill.

The scoring runs against a small synthetic lake rather than ingested data, so the suite stays
fast and does not depend on anyone having run `saa-data ingest`.
"""

import numpy as np
import pytest

from saa.contracts.macro import DIMENSIONS, Transform
from saa.macro_scoring_config import Indicator, cross_validate
from saa.skills.macro_regime import apply_transform, classify, score_history, to_score
from tests.conftest import MACRO_MONTHS as MONTHS
from tests.conftest import macro_series as growth_series
from tests.conftest import monthly
from tests.conftest import write_macro_lake as make_store


def indicator(series="PAYEMS", transform=Transform.LEVEL, sign=1, weight=1.0, diff_months=12):
    return Indicator(
        series=series, transform=transform, sign=sign, weight=weight, diff_months=diff_months
    )


# ------------------------------------------------------------------------------- transforms
def test_yoy_is_percent_change_over_twelve_months():
    series = monthly(np.linspace(100, 200, 25))
    out = apply_transform(series, indicator(transform=Transform.YOY))
    assert out.iloc[12] == pytest.approx(50.0)


def test_mom_annualised_compounds_the_monthly_change():
    series = monthly([100.0] + [100.0 * 1.01**i for i in range(1, 13)])
    out = apply_transform(series, indicator(transform=Transform.MOM_ANNUALISED))
    assert out.iloc[1] == pytest.approx((1.01**12 - 1) * 100, abs=1e-6)


def test_diff_uses_its_configured_horizon():
    series = monthly(np.arange(24, dtype=float))
    out = apply_transform(series, indicator(transform=Transform.DIFF, diff_months=6))
    assert out.iloc[6] == pytest.approx(6.0)


def test_level_passes_through():
    series = monthly([1.0, 2.0, 3.0])
    assert apply_transform(series, indicator()).tolist() == [1.0, 2.0, 3.0]


# ----------------------------------------------------------------------------------- scoring
def test_scores_are_bounded_and_centred():
    rng = np.random.default_rng(0)
    series = monthly(rng.normal(0, 1, MONTHS))
    scores = to_score(series, indicator(), lookback_years=20)
    assert scores.between(-1, 1).all()
    assert abs(scores.mean()) < 0.25


def test_sign_flips_the_score():
    series = monthly(np.linspace(0, 10, MONTHS))
    up = to_score(series, indicator(sign=1), lookback_years=20)
    down = to_score(series, indicator(sign=-1), lookback_years=20)
    assert up.iloc[-1] > 0 and down.iloc[-1] < 0
    assert up.iloc[-1] == pytest.approx(-down.iloc[-1])


def test_scoring_is_causal():
    """A score must not move when data after it changes; otherwise a backtest is meaningless."""
    base = monthly(np.linspace(0, 5, MONTHS))
    spiked = base.copy()
    spiked.iloc[-1] = 500.0
    stamp = base.index[MONTHS - 20]
    a = to_score(base, indicator(), lookback_years=20).loc[stamp]
    b = to_score(spiked, indicator(), lookback_years=20).loc[stamp]
    assert a == pytest.approx(b)


def test_an_extreme_print_cannot_dominate():
    rng = np.random.default_rng(1)
    series = monthly(rng.normal(0, 1, MONTHS))
    series.iloc[-1] = 50.0
    assert to_score(series, indicator(), lookback_years=20).iloc[-1] <= 1.0


# ---------------------------------------------------------------------------- classification
def test_classification_follows_the_paper_four_regimes(scoring):
    assert {r.regime for r in scoring.classification.rules} <= {
        "expansion",
        "late_cycle",
        "recession",
        "recovery",
    }


@pytest.mark.parametrize(
    ("scores", "momentum", "expected"),
    [
        (
            {"growth": -0.6, "inflation": 0.2, "monetary_policy": 0.3, "financial_conditions": 0.0},
            -0.2,
            "recession",
        ),
        (
            {"growth": -0.6, "inflation": 0.2, "monetary_policy": 0.5, "financial_conditions": 0.2},
            0.3,
            "recovery",
        ),
        (
            {"growth": 0.4, "inflation": 0.3, "monetary_policy": 0.2, "financial_conditions": 0.3},
            0.1,
            "expansion",
        ),
        # positive but deteriorating growth
        (
            {"growth": 0.3, "inflation": 0.2, "monetary_policy": 0.1, "financial_conditions": 0.1},
            -0.4,
            "late_cycle",
        ),
        # positive growth with an inflation squeeze -> §4.1's late-cycle-with-stagflation shape
        (
            {"growth": 0.3, "inflation": -0.5, "monetary_policy": 0.1, "financial_conditions": 0.1},
            0.05,
            "late_cycle",
        ),
        # positive growth with a policy squeeze
        (
            {"growth": 0.3, "inflation": 0.2, "monetary_policy": -0.6, "financial_conditions": 0.1},
            0.05,
            "late_cycle",
        ),
    ],
)
def test_classification_rules(scoring, scores, momentum, expected):
    assert classify(scores, momentum, scoring) == expected


def test_missing_growth_falls_back_to_the_default(scoring):
    scores = dict.fromkeys(DIMENSIONS, 0.5)
    scores["growth"] = float("nan")
    assert classify(scores, 0.1, scoring) == scoring.classification.default


# ------------------------------------------------------------------------------ integration
def test_score_history_produces_all_four_dimensions(tmp_config, scoring):
    store = make_store(tmp_config, growth_series())
    panel = score_history(store, scoring)
    assert list(panel.scores.columns) == list(DIMENSIONS)
    assert panel.scores["growth"].notna().all()
    assert panel.regimes.isin([r.regime for r in scoring.classification.rules]).all()
    assert panel.confidence.between(0, 1).all()


def test_ragged_edge_is_trimmed_not_defaulted(tmp_config, scoring):
    """Growth releases lag, so the newest months cannot be scored. They must be dropped rather
    than classified from a null growth score."""
    series = growth_series()
    for key in ("PAYEMS", "CFNAI", "INDPRO"):
        series[key] = series[key].iloc[:-3]  # three months of missing growth data
    store = make_store(tmp_config, series)
    panel = score_history(store, scoring)
    # Unclassifiable months are dropped, not defaulted, at both ends of the panel.
    assert panel.scores["growth"].notna().all()
    assert panel.as_of == series["PAYEMS"].index[-1]
    assert panel.as_of < series["CPILFESL"].index[-1]


def test_a_dimension_with_too_few_indicators_scores_null(tmp_config, scoring):
    series = growth_series()
    for key in ("CFNAI", "INDPRO"):
        series.pop(key)  # leaves growth with one live indicator, below min_indicators
    store = make_store(tmp_config, series)
    with pytest.raises(ValueError, match="growth could not be scored"):
        score_history(store, scoring)


def test_weights_renormalise_over_available_indicators(tmp_config, scoring):
    """Dropping one indicator must reweight the rest, not drag the composite toward zero."""
    full = score_history(make_store(tmp_config, growth_series()), scoring)
    assert full.scores["inflation"].abs().max() <= 1.0
    # Only two of the nine configured inflation indicators exist here; the composite still
    # reaches a real magnitude rather than being diluted toward zero by the missing seven.
    assert full.scores["inflation"].abs().iloc[-1] > 0.2


def test_empty_lake_fails_loudly(tmp_config, scoring):
    store = make_store(tmp_config, {"PAYEMS": monthly([1.0, 2.0, 3.0])})
    with pytest.raises(ValueError):
        score_history(store, scoring)


# ----------------------------------------------------------------------------- config checks
def test_shipped_config_is_valid_and_cross_checks(config, scoring):
    cross_validate(scoring, config.macro)
    assert set(scoring.dimensions) == set(DIMENSIONS)
    for dimension in DIMENSIONS:
        assert len(scoring.indicators(dimension)) >= scoring.min_indicators


def test_recession_probability_series_is_not_scored(scoring):
    """RECPROUSM156N is re-estimated after the fact: a label, not a signal."""
    assert "RECPROUSM156N" not in scoring.series_ids
    assert "USREC" not in scoring.series_ids


def test_evaluation_only_series_are_rejected(config, scoring):
    bad = scoring.model_copy(deep=True)
    bad.dimensions["growth"].indicators.append(indicator(series="USREC"))
    with pytest.raises(ValueError, match="evaluation-only"):
        cross_validate(bad, config.macro)


def test_series_must_belong_to_the_dimension_that_scores_it(config, scoring):
    bad = scoring.model_copy(deep=True)
    bad.dimensions["growth"].indicators.append(indicator(series="VIXCLS"))
    with pytest.raises(ValueError, match="assigns elsewhere"):
        cross_validate(bad, config.macro)


def test_unknown_series_is_rejected(config, scoring):
    bad = scoring.model_copy(deep=True)
    bad.dimensions["growth"].indicators.append(indicator(series="NOT_A_SERIES"))
    with pytest.raises(ValueError, match="not in macro_series.yaml"):
        cross_validate(bad, config.macro)

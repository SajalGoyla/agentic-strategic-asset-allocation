import numpy as np
import pandas as pd
import pytest

from saa.contracts.macro import Transform
from saa.data.lake import DataLake
from saa.data.store import DataStore
from saa.skills.macro_inputs import (
    IndicatorRequest,
    dimension_requests,
    indicator,
    indicators,
    pit_quality,
    transforms,
)

MONTHLY = pd.date_range("2000-01-31", "2020-12-31", freq="ME")


# --------------------------------------------------------------------------- transforms
def test_yoy_and_mom_on_a_compounding_index():
    index = pd.Series(100 * 1.01 ** np.arange(len(MONTHLY)), index=MONTHLY)  # +1%/month
    assert transforms.yoy(index).iloc[-1] == pytest.approx(1.01**12 - 1)
    assert transforms.mom_annualised(index).iloc[-1] == pytest.approx(1.01**12 - 1)


def test_diff_is_absolute_change_for_rates():
    rate = pd.Series(np.linspace(1.0, 5.0, len(MONTHLY)), index=MONTHLY)
    step = rate.iloc[1] - rate.iloc[0]
    assert transforms.diff(rate).iloc[-1] == pytest.approx(step * 12)
    assert transforms.diff(rate, months=3).iloc[-1] == pytest.approx(step * 3)


def test_lags_are_taken_by_date_so_quarterly_series_work():
    quarterly = pd.date_range("2000-03-31", "2020-12-31", freq="QE")
    gdp = pd.Series(100 * 1.02 ** np.arange(len(quarterly)), index=quarterly)  # +2%/quarter
    assert transforms.yoy(gdp).iloc[-1] == pytest.approx(1.02**4 - 1)


def test_zscore_and_percentile_use_a_trailing_window():
    flat = pd.Series([1.0] * 200 + [5.0], index=pd.date_range("2000-01-31", periods=201, freq="ME"))
    assert transforms.zscore(flat).iloc[-1] > 3
    assert transforms.percentile(flat).iloc[-1] == pytest.approx(1.0)
    # A flat stretch is all ties, and tied ranks average to the middle of the window.
    assert 0.4 < transforms.percentile(flat).iloc[50] < 0.6


def test_proportional_change_is_undefined_on_a_zero_centred_index():
    """CFNAI and the Sahm gap sit around zero; dividing by that base is meaningless."""
    cfnai = pd.Series(np.linspace(-0.5, 0.5, len(MONTHLY)), index=MONTHLY)
    yoy = transforms.yoy(cfnai)
    prior = transforms.lagged(cfnai, pd.DateOffset(years=1))
    assert yoy[prior <= 0].isna().all()  # no ratio against a zero or negative base
    assert yoy[prior > 0].notna().any()
    # `diff` is the right transform for such a series and stays finite throughout.
    assert np.isfinite(transforms.diff(cfnai).dropna()).all()


def test_apply_dispatches_by_name():
    index = pd.Series(100 * 1.01 ** np.arange(len(MONTHLY)), index=MONTHLY)
    assert transforms.apply(index, "yoy").iloc[-1] == pytest.approx(transforms.yoy(index).iloc[-1])
    assert transforms.apply(index, Transform.LEVEL).iloc[-1] == index.iloc[-1]


# --------------------------------------------------------------------------- indicators
@pytest.fixture
def store(tmp_config):
    """PAYEMS with ALFRED vintages, DGS10 without: the two cases the pit flag distinguishes."""
    lake = DataLake(tmp_config.settings.data_dir)
    payrolls = pd.DataFrame(
        {
            "series_id": "PAYEMS",
            "date": MONTHLY,
            "value": 100_000 * 1.002 ** np.arange(len(MONTHLY)),  # +0.2%/month
            "realtime_start": MONTHLY + pd.Timedelta(days=7),
            "realtime_end": pd.NaT,
            "available_from": MONTHLY + pd.Timedelta(days=7),
        }
    )
    daily = pd.date_range("2000-01-03", "2020-12-31", freq="B")
    rates = pd.DataFrame(
        {
            "series_id": "DGS10",
            "date": daily,
            "value": np.linspace(6.0, 1.0, len(daily)),
            "realtime_start": pd.NaT,
            "realtime_end": pd.NaT,
            "available_from": daily + pd.Timedelta(days=1),
        }
    )
    lake.write_dataset(
        "macro/fred_observations", pd.concat([payrolls, rates]), run_id="r1", source="test"
    )
    return DataStore(tmp_config)


def test_indicator_returns_transformed_and_raw_values(store):
    got = indicator(store, IndicatorRequest("PAYEMS", Transform.YOY), as_of="2020-12-31")
    assert got.dimension == "growth"
    assert got.value == pytest.approx(1.002**12 - 1)
    # December's release is not public on 31 December, so November is the latest observation.
    assert got.observation_date.isoformat() == "2020-11-30"
    assert got.raw_value == pytest.approx(100_000 * 1.002 ** (len(MONTHLY) - 2))
    assert got.transform is Transform.YOY


def test_point_in_time_flag_separates_vintages_from_estimates(store):
    payrolls = indicator(store, "PAYEMS", as_of="2020-12-31")
    rates = indicator(store, "DGS10", as_of="2020-12-31")
    assert payrolls.point_in_time is True
    assert rates.point_in_time is False
    quality = {q.dimension: q for q in pit_quality([payrolls, rates])}
    assert quality["growth"].indicators_point_in_time == 1
    assert quality["rates_and_yields"].indicators_point_in_time == 0
    assert quality["growth"].fraction == 1.0


def test_as_of_excludes_observations_published_later(store):
    early = indicator(store, "PAYEMS", as_of="2005-06-15")
    assert early.observation_date.isoformat() == "2005-05-31"
    assert early.available_from.isoformat() == "2005-06-07"


def test_unknown_series_is_rejected(store):
    with pytest.raises(KeyError, match="macro_series.yaml"):
        indicator(store, "NOT_A_SERIES", as_of="2020-12-31")


def test_indicators_skip_series_without_enough_history(store):
    found = indicators(
        store,
        [IndicatorRequest("PAYEMS", Transform.YOY), IndicatorRequest("DGS10", Transform.ZSCORE)],
        as_of="2000-06-30",  # too early for a 12-month lag or a z-score window
    )
    assert [i.series_id for i in found] == ["DGS10"] or found == []


def test_dimension_requests_exclude_evaluation_only_series(config):
    growth = {r.series_id for r in dimension_requests(config, "growth")}
    assert "PAYEMS" in growth
    reference = {r.series_id for r in dimension_requests(config, "reference")}
    assert "USREC" not in reference  # NBER dates are ex post, never scored

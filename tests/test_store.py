import numpy as np
import pandas as pd
import pytest

from saa.data.lake import DataLake
from saa.data.store import DataStore

NaT = pd.NaT


@pytest.fixture
def store(tmp_config):
    lake = DataLake(tmp_config.settings.data_dir)

    dates = pd.bdate_range("2020-01-01", "2020-03-31")
    prices = pd.concat(
        [
            pd.DataFrame(
                {
                    "date": dates,
                    "ticker": t,
                    "adj_close": np.linspace(100, 100 * growth, len(dates)),
                }
            )
            for t, growth in (("SPY", 1.10), ("TLT", 0.95))
        ]
    )
    for col in ("open", "high", "low", "close", "volume"):
        prices[col] = prices["adj_close"]
    prices[["dividends", "splits", "capital_gains"]] = 0.0
    lake.write_dataset("market/prices_daily", prices, run_id="r1", source="test")

    obs = pd.DataFrame(
        [
            # GDPC1 Q1-2020: advance estimate then revision (ALFRED vintages)
            ("GDPC1", "2020-01-01", 100.0, "2020-04-29", "2020-05-27", "2020-04-29"),
            ("GDPC1", "2020-01-01", 101.0, "2020-05-28", NaT, "2020-05-28"),
            # UNRATE Jan-2020: no vintages, availability estimated
            ("UNRATE", "2020-01-01", 3.5, NaT, NaT, "2020-02-07"),
            ("USREC", "2020-03-01", 1.0, NaT, NaT, "2021-03-31"),
        ],
        columns=["series_id", "date", "value", "realtime_start", "realtime_end", "available_from"],
    )
    lake.write_dataset("macro/fred_observations", obs, run_id="r1", source="test")
    return DataStore(tmp_config)


def test_monthly_returns(store):
    rets = store.returns(["SPY", "TLT"], freq="M")
    assert list(rets.columns) == ["SPY", "TLT"]
    assert len(rets) == 2  # Feb and Mar (Jan is the base period)
    assert (rets["SPY"] > 0).all() and (rets["TLT"] < 0).all()


def test_prices_respect_as_of(store):
    assert store.prices("SPY", as_of="2020-02-14").index.max() == pd.Timestamp("2020-02-14")


def test_macro_point_in_time_uses_vintage_in_force(store):
    def gdp(as_of):
        return store.macro("GDPC1", as_of=as_of)["GDPC1"].tolist()

    assert store.macro("GDPC1", as_of="2020-04-01").empty
    assert gdp("2020-05-01") == [100.0]
    assert gdp("2020-06-01") == [101.0]
    assert store.macro("GDPC1")["GDPC1"].tolist() == [101.0]  # latest vintage


def test_macro_point_in_time_uses_release_lag(store):
    assert store.macro("UNRATE", as_of="2020-02-06").empty
    assert store.macro("UNRATE", as_of="2020-02-07")["UNRATE"].tolist() == [3.5]


def test_evaluation_only_series_blocked_as_of(store):
    with pytest.raises(ValueError):
        store.macro("USREC", as_of="2022-01-01")
    assert "USREC" not in store.macro(as_of="2022-01-01").columns
    assert store.macro("USREC", as_of="2022-01-01", allow_lookahead=True)["USREC"].tolist() == [1.0]


def test_pre_vintage_backfill_rows_cover_early_as_of_dates(tmp_config):
    lake = DataLake(tmp_config.settings.data_dir)
    obs = pd.DataFrame(
        [
            # estimated row from latest values (released before the first ALFRED vintage)
            ("GDPC1", "2019-10-01", 99.0, NaT, NaT, "2020-01-30"),
            # first vintage, clipped to the vintage start
            ("GDPC1", "2019-10-01", 98.0, "2020-03-01", NaT, "2020-03-01"),
        ],
        columns=["series_id", "date", "value", "realtime_start", "realtime_end", "available_from"],
    )
    lake.write_dataset("macro/fred_observations", obs, run_id="r1", source="test")
    store = DataStore(tmp_config)
    assert store.macro("GDPC1", as_of="2020-02-01")["GDPC1"].tolist() == [99.0]
    assert store.macro("GDPC1", as_of="2020-04-01")["GDPC1"].tolist() == [98.0]
    assert store.macro("GDPC1")["GDPC1"].tolist() == [98.0]  # vintage wins over estimate


def test_provenance_pins_versions(store):
    store.prices("SPY")
    assert store.provenance()["market/prices_daily"]["run_id"] == "r1"


def test_wrds_accessors_respect_as_of(tmp_config):
    lake = DataLake(tmp_config.settings.data_dir)
    dates = pd.to_datetime(["2025-11-30", "2025-12-31"])
    lake.write_dataset(
        "wrds/etf_market_caps",
        pd.DataFrame(
            {
                "permno": [84398, 84398],
                "ticker": ["SPY", "SPY"],
                "date": dates,
                "market_cap_musd": [1.0, 2.0],
                "available_from": dates + pd.Timedelta(days=1),
            }
        ),
        run_id="r1",
        source="test",
    )
    lake.write_dataset(
        "wrds/corporate_bond_yields",
        pd.DataFrame(
            {
                "rating_class": ["investment_grade", "high_yield"],
                "date": [dates[1], dates[1]],
                "n_bonds": [10, 5],
                "yield_pct": [5.0, 7.0],
                "duration_years": [6.0, 4.0],
                "available_from": [dates[1] + pd.Timedelta(days=1)] * 2,
            }
        ),
        run_id="r1",
        source="test",
    )
    store = DataStore(tmp_config)
    assert store.etf_market_caps(as_of="2025-12-15")["SPY"].tolist() == [1.0]
    assert store.etf_market_caps()["SPY"].tolist() == [1.0, 2.0]
    assert store.corporate_bond_yields(as_of="2026-01-05").loc[dates[1], "high_yield"] == 7.0
    assert store.corporate_bond_yields(as_of="2025-12-31").empty
    with pytest.raises(FileNotFoundError):
        store.equity_valuation()


# ------------------------------------------------------- as-of coverage (decision 60)
def test_a_lake_that_reaches_the_as_of_is_not_stale():
    from datetime import date

    from saa.data.validation import asof_coverage

    c = asof_coverage(date(2026, 9, 30), date(2026, 10, 1))
    assert not c.stale and c.months_missing == 0


def test_a_missing_month_is_caught_even_though_the_day_count_looks_small():
    """The test is "does the panel reach the last complete month end", not a day threshold: on
    9 November, October has ended and its absence is missing data, not a release lag."""
    from datetime import date

    from saa.data.validation import asof_coverage

    c = asof_coverage(date(2026, 9, 30), date(2026, 11, 9))
    assert c.stale
    assert c.expected_month == date(2026, 10, 31)
    assert c.months_missing == 1
    assert "saa-data ingest" in c.detail
    assert "--as-of 2026-09-30" in c.detail, "it must name the honest alternative"


def test_the_month_just_ended_is_not_expected_within_the_grace_period():
    """Sources publish a month-end over the following days, so 1 October does not yet expect
    September."""
    from datetime import date

    from saa.data.validation import asof_coverage

    assert not asof_coverage(date(2026, 8, 31), date(2026, 9, 2)).stale
    assert asof_coverage(date(2026, 8, 31), date(2026, 10, 20)).stale


def test_an_empty_panel_is_stale_and_says_what_to_run():
    from datetime import date

    from saa.data.validation import asof_coverage

    c = asof_coverage(None, date(2026, 11, 9))
    assert c.stale and "saa-data ingest" in c.detail


def test_check_asof_coverage_refuses_unless_allowed(tmp_config):
    """It raises by default, because a paid run is the worst place to discover stale data."""
    from datetime import date

    import pandas as pd

    from saa.data.validation import StaleLakeError, check_asof_coverage

    class FakeStore:
        def returns(self):
            idx = pd.date_range("2020-01-31", "2026-09-30", freq="ME")
            return pd.DataFrame({"SPY": 0.01, "BIL": 0.001}, index=idx)

    with pytest.raises(StaleLakeError, match="month\\(s\\) missing"):
        check_asof_coverage(FakeStore(), date(2026, 11, 9))
    assert check_asof_coverage(FakeStore(), date(2026, 11, 9), allow_stale=True).stale


def test_coverage_follows_the_shortest_column(tmp_config):
    """A panel is only usable as far as every asset reaches, so the shortest column binds."""
    from datetime import date

    import pandas as pd

    from saa.data.validation import check_asof_coverage

    class RaggedStore:
        def returns(self):
            idx = pd.date_range("2020-01-31", "2026-10-31", freq="ME")
            df = pd.DataFrame({"SPY": 0.01, "GLD": 0.01}, index=idx)
            df.loc[df.index[-1], "GLD"] = None  # gold stops a month early
            return df

    c = check_asof_coverage(RaggedStore(), date(2026, 11, 20), allow_stale=True)
    assert c.latest_month == date(2026, 9, 30)
    assert c.stale

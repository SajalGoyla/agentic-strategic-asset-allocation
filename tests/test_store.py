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

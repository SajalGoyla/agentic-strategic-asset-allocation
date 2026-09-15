import io

import numpy as np
import pandas as pd
import pytest

from saa.data.history import (
    last_complete_month_end,
    monthly_from_daily,
    par_bond_returns,
    splice,
)
from saa.data.sources.worldbank import discover_download_url, parse_worldbank_prices

MONTHS = pd.to_datetime(["2020-01-31", "2020-02-29"])


def test_par_bond_unchanged_yield_earns_coupon():
    r = par_bond_returns(pd.Series([4.0, 4.0], index=MONTHS), 10)
    assert r.iloc[0] == pytest.approx(0.04 / 12)


def test_par_bond_rate_rise_loses_about_duration():
    r = par_bond_returns(pd.Series([4.0, 5.0], index=MONTHS), 10).iloc[0]
    assert -0.085 < r < -0.065  # modified duration ~8 years, less convexity, plus accrual


def test_monthly_from_daily_needs_month_end_prices():
    dates = pd.bdate_range("2020-01-01", "2020-03-15")
    prices = pd.DataFrame(
        {"date": dates, "ticker": "X", "adj_close": np.linspace(100, 110, len(dates))}
    )
    r = monthly_from_daily(prices, "X", tolerance_days=7)
    # January has no prior month; March has no price near month end.
    assert list(r.index) == [pd.Timestamp("2020-02-29")]


def test_splice_prefers_etf_and_fills_earlier_months_from_proxy():
    idx = pd.date_range("2020-01-31", periods=4, freq="ME")
    etf = pd.Series([0.02, 0.03], index=idx[2:])
    proxy = pd.Series([0.01, 0.015, 0.5], index=idx[:3])
    out = splice([etf, proxy])
    assert out["ret"].tolist() == [0.01, 0.015, 0.02, 0.03]
    assert out["priority"].tolist() == [1, 1, 0, 0]


def test_last_complete_month_end():
    assert last_complete_month_end(pd.Timestamp("2026-09-15")) == pd.Timestamp("2026-08-31")
    assert last_complete_month_end(pd.Timestamp("2026-09-30")) == pd.Timestamp("2026-08-31")


def test_worldbank_parser():
    rows = [
        ["World Bank Commodity Price Data", None, None],
        ["monthly prices", None, None],
        [None, "Gold", "Coal, South African **"],
        [None, "($/troy oz)", "($/mt)"],
        ["1960M01", 35.27, "…"],
        ["1960M02", 35.27, 12.5],
    ]
    buffer = io.BytesIO()
    pd.DataFrame(rows).to_excel(buffer, sheet_name="Monthly Prices", header=False, index=False)
    df = parse_worldbank_prices(buffer.getvalue(), 5)
    gold = df[df["series"] == "Gold"]
    assert gold["date"].tolist() == [pd.Timestamp("1960-01-31"), pd.Timestamp("1960-02-29")]
    assert gold["unit"].iloc[0] == "($/troy oz)"
    assert df.loc[df["series"] == "Coal, South African", "value"].tolist() == [12.5]


def test_worldbank_link_discovery():
    page = '<a href="https://thedocs.worldbank.org/en/doc/abc/related/CMO-Historical-Data-Monthly.xlsx">x</a>'
    assert discover_download_url(page).endswith("/abc/related/CMO-Historical-Data-Monthly.xlsx")


def test_fred_yield_returns_roll_monthly_series_to_month_end():
    from saa.config import HistorySource
    from saa.data.history import fred_yield_returns

    fred = pd.DataFrame(
        {
            "series_id": "BAA",
            "date": pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"]),
            "value": [4.0, 4.0, 4.0],
            "realtime_start": pd.NaT,
            "realtime_end": pd.NaT,
            "available_from": pd.to_datetime(["2020-02-01", "2020-03-01", "2020-04-01"]),
        }
    )
    link = HistorySource(source="par_bond", series=["BAA"], maturity_years=10, kind="synthetic")
    r = fred_yield_returns(fred, link, tolerance_days=7, frequencies={"BAA": "m"})
    assert list(r.index) == [pd.Timestamp("2020-02-29"), pd.Timestamp("2020-03-31")]
    assert r.iloc[0] == pytest.approx(0.04 / 12)

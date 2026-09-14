import io
from datetime import date

import pandas as pd
import pytest

from saa.config import MacroSeries
from saa.data.sources.fred import (
    OPEN_ENDED,
    parse_graph_csv,
    parse_observations_json,
    vintage_windows,
)
from saa.data.sources.french import parse_french_csv
from saa.data.sources.shiller import discover_download_url, shiller_dates
from saa.data.sources.spf import parse_spf_workbook
from saa.data.sources.treasury import parse_treasury_csv

FRENCH = """This file was created using the 202607 CRSP database.
Missing data are indicated by -99.99 or -999.

,Mkt-RF,SMB,HML,RF
192607,   2.89,  -2.42,  -2.75,   0.22
192608,   2.64,  -99.99,   4.13,   0.25

 Annual Factors: January-December
,Mkt-RF,SMB,HML,RF
1927,  29.47,  -2.04,  -3.54,   3.12
"""


def test_french_parses_first_monthly_block_only():
    wide = parse_french_csv(FRENCH)
    assert list(wide.columns) == ["Mkt-RF", "SMB", "HML", "RF"]
    assert list(wide.index) == [pd.Timestamp("1926-07-31"), pd.Timestamp("1926-08-31")]
    assert wide.loc["1926-07-31", "Mkt-RF"] == pytest.approx(0.0289)
    assert pd.isna(wide.loc["1926-08-31", "SMB"])


def test_french_handles_padded_bloomberg_layout():
    text = "header\n\n,Mkt-RF,RF\n199007    ,0.77    ,0.68\n199008  ,-10.77   ,0.66\n\n"
    wide = parse_french_csv(text)
    assert wide.shape == (2, 2)
    assert wide.iloc[1, 0] == pytest.approx(-0.1077)


def test_treasury_normalises_tenor_labels():
    text = 'Date,"1 Mo","1.5 Month","10 Yr"\n12/31/2025,3.74,3.75,4.18\n12/30/2025,3.65,,4.14\n'
    df = parse_treasury_csv(text, "nominal")
    assert set(df["tenor"]) == {"1M", "1.5M", "10Y"}
    assert df.loc[df["tenor"] == "10Y", "tenor_months"].iloc[0] == 120
    assert len(df) == 5  # blank 1.5M on 12/30 dropped
    assert parse_treasury_csv("", "real").empty


MONTHLY = MacroSeries(
    id="PAYEMS", name="Payrolls", dimension="growth", frequency="m", release_lag_days=7
)


def test_fred_vintage_rows_keep_realtime_windows():
    pages = [
        {
            "count": 3,
            "observations": [
                {
                    "realtime_start": "2020-02-07",
                    "realtime_end": "2020-03-05",
                    "date": "2020-01-01",
                    "value": "100",
                },
                {
                    "realtime_start": "2020-03-06",
                    "realtime_end": OPEN_ENDED,
                    "date": "2020-01-01",
                    "value": "101",
                },
                {
                    "realtime_start": "2020-03-06",
                    "realtime_end": OPEN_ENDED,
                    "date": "2020-02-01",
                    "value": ".",
                },
            ],
        }
    ]
    df = parse_observations_json(pages, MONTHLY, vintage=True)
    assert len(df) == 2
    assert df["realtime_end"].isna().sum() == 1
    assert (df["available_from"] == df["realtime_start"]).all()


def test_fred_non_vintage_availability_is_period_end_plus_lag():
    text = "observation_date,PAYEMS\n2020-01-01,100\n2020-02-01,.\n"
    df = parse_graph_csv(text, MONTHLY)
    assert len(df) == 1
    assert df["available_from"].iloc[0] == pd.Timestamp("2020-02-07")
    assert df["realtime_start"].isna().all()


def test_fred_graph_csv_rejects_error_pages():
    with pytest.raises(ValueError):
        parse_graph_csv("<html>error</html>\n", MONTHLY)


def test_vintage_windows_tile_to_open_end():
    windows = vintage_windows(date(1990, 1, 1), 5, today=date(2001, 6, 1))
    assert windows == [
        ("1990-01-01", "1994-12-31"),
        ("1995-01-01", "1999-12-31"),
        ("2000-01-01", OPEN_ENDED),
    ]


def test_spf_workbook_horizons():
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame({"YEAR": [2025, 2026], "QUARTER": [1, 1], "STOCK10": [7.0, 6.5]}).to_excel(
            writer, sheet_name="STOCK10", index=False
        )
        pd.DataFrame({"YEAR": [2026], "QUARTER": [3], "TBILL2": [3.7], "TBILLA": [3.6]}).to_excel(
            writer, sheet_name="TBILL", index=False
        )
    df, problems = parse_spf_workbook(buffer.getvalue(), ["STOCK10", "TBILL", "MISSING"], 45)
    assert problems == ["MISSING: sheet not found in SPF workbook"]
    stock = df[df["variable"] == "STOCK10"]
    assert set(stock["horizon"]) == {"point"}
    assert stock["survey_date"].max() == pd.Timestamp("2026-01-01")
    assert set(df.loc[df["variable"] == "TBILL", "horizon"]) == {"2", "A"}
    assert df.loc[df["variable"] == "TBILL", "survey_date"].iloc[0] == pd.Timestamp("2026-07-01")


def test_shiller_decimal_month_codes():
    dates = shiller_dates(pd.Series([1871.01, 1871.1, 2023.12]))
    assert list(dates) == [
        pd.Timestamp("1871-01-31"),
        pd.Timestamp("1871-10-31"),
        pd.Timestamp("2023-12-31"),
    ]


def test_shiller_link_discovery():
    page = '<a href="//img1.wsimg.com/blobby/go/x/downloads/y/ie_data.xls?ver=123">data</a>'
    assert (
        discover_download_url(page)
        == "https://img1.wsimg.com/blobby/go/x/downloads/y/ie_data.xls?ver=123"
    )
    assert discover_download_url("<html></html>") is None

import numpy as np
import pandas as pd
import pytest

from saa.data.equity_valuation import GroupRules, aggregate_equity_valuation

# Tiny universe: large = top 2, style = top 4 (split by book-to-market), small = ranks 5-6.
RULES = GroupRules(large_n=2, style_n=4, small_n=6, lag_months=6, max_age_months=18)
MONTH = pd.Timestamp("2021-06-30")


def firm_panel(month=MONTH):
    caps = [600.0, 500.0, 400.0, 300.0, 200.0, 100.0, 50.0]  # permno 1..7; 7 is below small_n
    rows = [
        {"permno": i + 1, "date": month, "mcap": cap, "issuertype": "CORP"}
        for i, cap in enumerate(caps)
    ]
    rows.append({"permno": 99, "date": month, "mcap": 80.0, "issuertype": "REIT"})
    return pd.DataFrame(rows)


def links(permnos=(*range(1, 8), 99)):
    return pd.DataFrame(
        {
            "gvkey": [f"g{p}" for p in permnos],
            "permno": list(permnos),
            "linkdt": pd.Timestamp("1990-01-01"),
            "linkenddt": pd.NaT,
        }
    )


def fundamentals(datadate="2020-12-31", **overrides):
    """Every firm: dividends 2% of a cap-100 firm, buybacks 3, issuance 1, earnings 5."""
    rows = []
    for p, be in zip((*range(1, 8), 99), (60, 250, 40, 300, 50, 100, 10, 40), strict=True):
        row = {
            "gvkey": f"g{p}",
            "datadate": pd.Timestamp(datadate),
            "dvc": 2.0,
            "prstkc": 3.0,
            "sstk": 1.0,
            "ib": 5.0,
            "ceq": float(be),
            "txditc": np.nan,
        }
        row.update(overrides.get(p, {}))
        rows.append(row)
    return pd.DataFrame(rows)


def by_group(out):
    return out.set_index("group")


def test_groups_follow_the_rank_rules():
    out = by_group(aggregate_equity_valuation(firm_panel(), fundamentals(), links(), rules=RULES))
    assert out.loc["us_large_cap", "market_cap_musd"] == 1100.0  # permnos 1 and 2
    assert out.loc["us_small_cap", "market_cap_musd"] == 300.0  # ranks 5 and 6, not 7
    assert out.loc["reits", "market_cap_musd"] == 80.0  # REITs never enter the ranking
    # Top 4 by book-to-market: 2 (0.5) and 4 (1.0) above the median, 1 (0.1) and 3 (0.1) below.
    assert out.loc["us_value", "market_cap_musd"] == 800.0
    assert out.loc["us_growth", "market_cap_musd"] == 1000.0


def test_yields_are_aggregate_ratios_in_percent():
    out = by_group(aggregate_equity_valuation(firm_panel(), fundamentals(), links(), rules=RULES))
    large = out.loc["us_large_cap"]
    assert large["dividend_yield_pct"] == pytest.approx(100 * 4 / 1100)
    assert large["buyback_yield_pct"] == pytest.approx(100 * 6 / 1100)
    assert large["net_payout_yield_pct"] == pytest.approx(100 * (4 + 6 - 2) / 1100)
    assert large["earnings_yield_pct"] == pytest.approx(100 * 10 / 1100)
    assert large["book_to_price"] == pytest.approx((60 + 250) / 1100)
    assert large["fundamentals_coverage_pct"] == 100.0


def test_fundamentals_wait_for_the_publication_lag():
    """A fiscal year ending 2021-03-31 is public from 2021-09-30, not in June 2021."""
    out = by_group(
        aggregate_equity_valuation(firm_panel(), fundamentals("2021-03-31"), links(), rules=RULES)
    )
    assert out.loc["us_large_cap", "fundamentals_coverage_pct"] == 0.0
    assert np.isnan(out.loc["us_large_cap", "dividend_yield_pct"])


def test_stale_fundamentals_are_dropped():
    out = by_group(
        aggregate_equity_valuation(firm_panel(), fundamentals("2019-06-30"), links(), rules=RULES)
    )
    assert out.loc["us_large_cap", "fundamentals_coverage_pct"] == 0.0


def test_a_link_must_be_active_at_the_fiscal_year_end():
    stale_link = links()
    stale_link.loc[stale_link["permno"] == 1, "linkenddt"] = pd.Timestamp("2015-01-01")
    out = by_group(
        aggregate_equity_valuation(firm_panel(), fundamentals(), stale_link, rules=RULES)
    )
    assert out.loc["us_large_cap", "fundamentals_coverage_pct"] == pytest.approx(100 * 500 / 1100)
    # Yields use only the covered cap, so a missing firm does not dilute them.
    assert out.loc["us_large_cap", "dividend_yield_pct"] == pytest.approx(100 * 2 / 500)


def test_long_term_growth_is_cap_weighted_over_covered_firms():
    ltg = pd.DataFrame({"permno": [1, 2], "date": [MONTH, MONTH], "ltg_pct": [10.0, 20.0]})
    out = by_group(
        aggregate_equity_valuation(firm_panel(), fundamentals(), links(), ltg, rules=RULES)
    )
    assert out.loc["us_large_cap", "ltg_pct"] == pytest.approx((600 * 10 + 500 * 20) / 1100)
    assert out.loc["us_large_cap", "ltg_coverage_pct"] == 100.0
    assert np.isnan(out.loc["us_small_cap", "ltg_pct"])

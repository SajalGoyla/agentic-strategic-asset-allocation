"""End-to-end checks against the real data lake (plan, Week 3: integration testing).

These run only where an ingested lake exists: a fresh clone or CI has no `data/`, and building
one needs network access and, for five assets, WRDS credentials. Everything here is read-only;
outputs go to a temporary run directory.

    uv run saa-data ingest      # populate the lake first
    uv run pytest tests/test_integration.py
"""

from __future__ import annotations

import pandas as pd
import pytest

from saa.config import load_config
from saa.contracts.registry import read
from saa.data.lake import DataLake
from saa.data.store import DataStore
from saa.data.validation import FAIL, validate_lake
from saa.run import RunContext
from saa.skills.historical_analysis import run_historical_analysis, write_outputs
from saa.skills.macro_inputs import IndicatorRequest, indicator

AS_OF = "2020-04-01"  # a month after the COVID crash: point-in-time behaviour is visible

CONFIG = load_config()
LAKE = DataLake(CONFIG.settings.data_dir)
REQUIRED = ("market/asset_returns_monthly", "macro/fred_observations", "market/prices_daily")
pytestmark = pytest.mark.skipif(
    not all(LAKE.has_dataset(name) for name in REQUIRED),
    reason="no ingested data lake; run `uv run saa-data ingest`",
)


@pytest.fixture(scope="module")
def store():
    return DataStore(CONFIG)


def test_data_layer_validates_without_failures():
    report = validate_lake(CONFIG, LAKE)
    failures = [
        f"{c.dataset} {c.entity or ''} {c.check}: {c.detail}"
        for c in report.checks
        if c.status == FAIL
    ]
    assert not failures, failures


def test_every_asset_has_history_covering_the_backtest_window(store):
    returns = store.asset_returns()
    assert list(returns.columns) == [a.id for a in CONFIG.universe.assets]
    backtest_start = pd.Timestamp(CONFIG.settings.history.backtest_start)
    for asset_id in returns.columns:
        first = returns[asset_id].first_valid_index()
        assert first <= backtest_start, (
            f"{asset_id} starts {first.date()}, after the backtest start"
        )


def test_historical_analysis_writes_valid_contracts_point_in_time(store, tmp_path):
    analysis = run_historical_analysis(store, as_of=AS_OF)
    run = RunContext.create(CONFIG, as_of=analysis.as_of, root=tmp_path / "run")
    written = write_outputs(analysis, run)
    assert len(analysis.stats) == 18

    # Nothing published after as_of may appear.
    assert analysis.data_end < pd.Timestamp(AS_OF).date()
    for path in run.root.glob("cma/*/historical_stats.json"):
        stats = read("historical_stats", path)
        assert stats.header.as_of.isoformat() == AS_OF
        assert stats.body.data_end <= analysis.data_end
        assert stats.header.provenance, "header must record which dataset versions were read"
    for path in run.root.glob("cma/*/correlation_row.json"):
        read("correlation_row", path)
    assert len(written) == 18 * 3 + 1  # stats, correlations and a report per asset, plus summary

    # The COVID drawdown is visible in equities at this date, and not yet recovered.
    equity = analysis.stats["us_large_cap"].windows["3y"]
    assert equity.current_drawdown < -0.10
    assert equity.max_drawdown_recovery is None


def test_macro_indicator_is_point_in_time(store):
    payrolls = indicator(store, IndicatorRequest("PAYEMS", "yoy"), as_of=AS_OF, config=CONFIG)
    # March payrolls were published on 3 April 2020, so as of 1 April the latest is February.
    # FRED stamps a monthly observation at the start of its period, hence 2020-02-01.
    assert payrolls.observation_date.isoformat() == "2020-02-01"
    assert payrolls.available_from <= pd.Timestamp(AS_OF).date()
    assert payrolls.value > 0  # employment was still growing year-over-year in February 2020


def test_wrds_derived_history_is_not_required(store):
    """Assets whose pre-ETF history comes from CRSP still resolve; without WRDS credentials the
    public fallbacks in config/universe.yaml take over."""
    sources = store.asset_returns(field="source")
    assert sources["intl_developed"].dropna().nunique() >= 1
    assert sources["gold"].dropna().nunique() >= 2

import pandas as pd
import pytest
from pydantic import ValidationError

from saa.config import HistorySource
from saa.data import pipeline
from saa.data.history import crsp_fund_returns, crsp_treasury_returns
from saa.data.lake import DataLake
from saa.data.sources.base import FetchResult, Source
from saa.data.sources.wrds import WrdsSource
from saa.data.validation import FAIL, validate_lake

MONTHS = pd.to_datetime(["2000-01-31", "2000-02-29"])


def test_crsp_treasury_link_averages_columns_and_requires_all():
    indexes = pd.DataFrame(
        {
            "series": ["b7ret", "b7ret", "b10ret"],
            "date": [MONTHS[0], MONTHS[1], MONTHS[0]],
            "ret": [0.01, 0.02, 0.03],
        }
    )
    link = HistorySource(source="crsp_treasury", columns=["b7ret", "b10ret"], kind="index")
    r = crsp_treasury_returns(indexes, link)
    assert list(r.index) == [MONTHS[0]]
    assert r.iloc[0] == pytest.approx(0.02)


def test_crsp_fund_link_selects_ticker():
    funds = pd.DataFrame({"ticker": ["A", "B"], "date": [MONTHS[0], MONTHS[0]], "ret": [0.1, 0.2]})
    link = HistorySource(source="crsp_fund", ticker="B", kind="active_fund")
    assert crsp_fund_returns(funds, link).tolist() == [0.2]
    assert link.licensed and link.label == "crsp_fund:B"


def test_crsp_stock_link_requires_permno():
    with pytest.raises(ValidationError):
        HistorySource(source="crsp_stock", kind="closed_end_fund")


def test_wrds_source_skips_without_credentials(config, monkeypatch):
    monkeypatch.delenv("WRDS_USERNAME", raising=False)
    result = WrdsSource(config).fetch()
    assert result.skipped and "WRDS_USERNAME" in result.skipped
    assert not result.tables


class _SkippedSource(Source):
    name = "skipper"

    def fetch(self):
        return FetchResult(self.name, skipped="no credentials")


def test_pipeline_reports_skipped_source_without_failing(tmp_config, monkeypatch):
    monkeypatch.setattr(pipeline, "SOURCE_REGISTRY", {"skipper": _SkippedSource})
    summary, _ = pipeline.run_ingestion(tmp_config, validate=False)
    run = summary["sources"][0]
    assert run["status"] == "skipped"
    assert run["warnings"] == ["skipped: no credentials"]


def test_missing_optional_wrds_datasets_do_not_fail_validation(tmp_config):
    report = validate_lake(tmp_config, DataLake(tmp_config.settings.data_dir))
    failed = {c.dataset for c in report.checks if c.status == FAIL}
    assert not any(name.startswith("wrds/") for name in failed)
    assert "wrds/crsp_treasury_indexes" in report.info["optional_not_ingested"]

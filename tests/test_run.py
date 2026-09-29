from datetime import date

import pytest

from saa.contracts.asset_class import CorrelationRowBody
from saa.contracts.base import Producer
from saa.contracts.registry import read
from saa.run import RunContext


@pytest.fixture
def run(config, tmp_path):
    return RunContext.create(config, as_of="2026-03-31", run_id="20260331T120000Z", root=tmp_path)


def test_paths_follow_the_documented_layout(run):
    assert run.path("macro_view").relative_to(run.root).as_posix() == "macro/macro-view.json"
    assert (
        run.path("historical_stats", asset_id="us_large_cap").relative_to(run.root).as_posix()
        == "cma/us_large_cap/historical_stats.json"
    )
    assert run.path("covariance").relative_to(run.root).as_posix() == "pc/covariance.json"
    assert (
        run.path("pc_proposal", agent_id="risk_parity").relative_to(run.root).as_posix()
        == "pc/risk_parity/pc_proposal.json"
    )
    assert (
        run.path("peer_review", agent_id="risk_parity", reviewed="black_litterman")
        .relative_to(run.root)
        .as_posix()
        == "review/risk_parity/peer_review-black_litterman.json"
    )
    assert run.path("vote_tally").relative_to(run.root).as_posix() == "review/vote_tally.json"
    assert run.path("cio_decision").relative_to(run.root).as_posix() == "cio/cio_decision.json"


def test_missing_scope_is_rejected(run):
    with pytest.raises(ValueError, match="per asset"):
        run.path("historical_stats")
    with pytest.raises(ValueError, match="per agent"):
        run.path("cro_report")
    with pytest.raises(ValueError, match="only to peer_review"):
        run.path("vote", agent_id="risk_parity", reviewed="equal_weight")


def test_header_is_machine_written_from_the_run_and_ips(run, config):
    header = run.header(
        "correlation_row",
        "us-large-cap",
        Producer.SCRIPT,
        provenance={"market/asset_returns_monthly": {"run_id": "r1", "sha256": "abc"}},
    )
    assert header.pipeline_run_id == "20260331T120000Z"
    assert header.as_of == date(2026, 3, 31)
    assert header.ips_version == config.ips.version and header.ips_status == config.ips.status
    assert header.provenance["market/asset_returns_monthly"].sha256 == "abc"
    assert header.report_path is None


def test_write_validates_and_round_trips(run):
    body = CorrelationRowBody(
        asset_id="gold",
        end=date(2026, 2, 28),
        months={"5y": 60},
        correlations={"5y": {"us_large_cap": 0.13, "cash": None}},
    )
    report = run.write_report("# gold\n", "analysis.md", asset_id="gold")
    path = run.write("correlation_row", "gold", body, asset_id="gold", report_path=report)
    reloaded = read("correlation_row", path)
    assert reloaded.body.correlations["5y"]["us_large_cap"] == 0.13
    assert reloaded.header.report_path == "cma/gold/analysis.md"
    assert reloaded.header.produced_by is Producer.SCRIPT


def test_input_ref_is_relative_to_the_run(run):
    ref = run.input_ref("macro_view", run.path("macro_view"), sha256="deadbeef")
    assert ref.path == "macro/macro-view.json" and ref.sha256 == "deadbeef"

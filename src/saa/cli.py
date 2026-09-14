"""Command line entry point: ``uv run saa-data {ingest,validate,status}``."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime

from saa.config import load_config
from saa.data.lake import DataLake
from saa.data.validation import PASS, ValidationReport


def _print_run(summary: dict) -> None:
    print(f"\nIngestion run {summary['run_id']} (FRED mode: {summary['fred_mode']})")
    for run in summary["sources"]:
        datasets = ", ".join(f"{k}={v:,}" for k, v in run["datasets"].items()) or "-"
        print(
            f"  {run['source']:<9} {run['status']:<17} {run.get('seconds', 0):>6.1f}s  {datasets}"
        )
        if run["error"]:
            print(f"      error: {run['error']}")
        for warning in run["warnings"]:
            print(f"      warning: {warning}")


def _print_validation(report: ValidationReport) -> None:
    s = report.summary()
    print(f"\nValidation: {s['PASS']} pass, {s['WARN']} warn, {s['FAIL']} fail")
    if "common_etf_history_start" in report.info:
        print(
            f"  All 18 ETFs available from {report.info['common_etf_history_start']} "
            f"(limited by {report.info['common_etf_history_limited_by']})"
        )
    for c in report.checks:
        if c.status != PASS:
            entity = f" {c.entity}" if c.entity else ""
            print(f"  [{c.status}] {c.dataset}{entity} {c.check}: {c.detail}")


def _print_status(lake: DataLake) -> None:
    datasets = lake.load_catalog()["datasets"]
    if not datasets:
        print("No datasets ingested yet. Run: uv run saa-data ingest")
        return
    print(f"{'dataset':<30} {'latest run':<17} {'rows':>10} {'entities':>8}  range")
    for name, entry in sorted(datasets.items()):
        v = next(x for x in entry["versions"] if x["run_id"] == entry["latest"])
        span = f"{v.get('min_date', '')} .. {v.get('max_date', '')}"
        print(f"{name:<30} {v['run_id']:<17} {v['rows']:>10,} {v.get('entities', ''):>8}  {span}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="saa-data", description="Agentic SAA data layer")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    from saa.data.sources import SOURCE_REGISTRY

    ingest = sub.add_parser("ingest", help="fetch sources into the data lake")
    ingest.add_argument(
        "--sources", nargs="+", choices=list(SOURCE_REGISTRY), help="subset of sources"
    )
    ingest.add_argument("--no-validate", action="store_true", help="skip data-quality checks")
    sub.add_parser("validate", help="run data-quality checks on the latest datasets")
    sub.add_parser("status", help="show ingested dataset versions")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    config = load_config()
    lake = DataLake(config.settings.data_dir)

    if args.command == "ingest":
        from saa.data.pipeline import run_ingestion

        summary, report = run_ingestion(config, args.sources, validate=not args.no_validate)
        _print_run(summary)
        if report is not None:
            _print_validation(report)
        return 0 if all(r["status"] != "failed" for r in summary["sources"]) else 1

    if args.command == "validate":
        from saa.data.validation import validate_lake

        report = validate_lake(config, lake)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = lake.write_json(f"reports/validation_{stamp}.json", report.to_dict())
        _print_validation(report)
        print(f"\nReport written to {path}")
        return 0 if report.ok else 1

    _print_status(lake)
    return 0


if __name__ == "__main__":
    sys.exit(main())

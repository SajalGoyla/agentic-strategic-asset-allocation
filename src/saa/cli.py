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
    if "history" in summary:
        _print_history(summary["history"])


def _print_history(run: dict) -> None:
    datasets = ", ".join(f"{k}={v:,}" for k, v in run["datasets"].items()) or "-"
    print(f"  {'history':<9} {run['status']:<17} {run.get('seconds', 0):>6.1f}s  {datasets}")
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
    if "common_history_start" in report.info:
        print(
            f"  All 18 asset return histories (ETF + proxies) available from "
            f"{report.info['common_history_start']} (limited by {report.info['common_history_limited_by']})"
        )
    for c in report.checks:
        if c.status != PASS:
            entity = f" {c.entity}" if c.entity else ""
            print(f"  [{c.status}] {c.dataset}{entity} {c.check}: {c.detail}")


def _print_wrds(result: dict) -> None:
    print(f"\nWRDS account {result['username']}: {result['library_count']} libraries visible")
    print("Relevant libraries: " + (", ".join(result["relevant_libraries"]) or "-"))
    print(f"\n{'table':<38} {'status':<10} improves")
    for t in result["tables"]:
        print(f"{t['library'] + '.' + t['table']:<38} {t['status']:<10} {t['improves']}")


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
    sub.add_parser("build-history", help="rebuild spliced monthly asset returns from the lake")
    sub.add_parser("validate", help="run data-quality checks on the latest datasets")
    sub.add_parser("status", help="show ingested dataset versions")
    sub.add_parser("wrds-login", help="save your WRDS password to the PostgreSQL password file")
    sub.add_parser("wrds-check", help="test which relevant WRDS tables this account can read")
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

    if args.command == "build-history":
        from saa.data.lake import new_run_id
        from saa.data.pipeline import build_history_datasets

        run = build_history_datasets(config, lake, new_run_id())
        _print_history(run)
        return 0 if run["status"] in ("ok", "ok_with_warnings") else 1

    if args.command == "validate":
        from saa.data.validation import validate_lake

        report = validate_lake(config, lake)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = lake.write_json(f"reports/validation_{stamp}.json", report.to_dict())
        _print_validation(report)
        print(f"\nReport written to {path}")
        return 0 if report.ok else 1

    if args.command == "wrds-login":
        import getpass
        import os

        from saa.data.wrds_client import WrdsClient, save_password

        username = os.getenv("WRDS_USERNAME") or input("WRDS username: ").strip()
        password = getpass.getpass(f"WRDS password for {username} (not shown): ")
        print("Connecting (approve the Duo prompt if one appears)...")
        try:
            with WrdsClient(username, password=password) as client:
                client.query("select 1")
        except Exception as exc:
            print(f"Login failed: {str(exc).strip().splitlines()[0]}")
            return 1
        print(f"Login OK. Password saved to {save_password(username, password)}")
        if not os.getenv("WRDS_USERNAME"):
            print(f"Add WRDS_USERNAME={username} to .env")
        return 0

    if args.command == "wrds-check":
        from saa.data.wrds_access import run_check

        try:
            result = run_check(config)
        except RuntimeError as exc:
            print(f"WRDS check not run: {exc}")
            return 1
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = lake.write_json(f"reports/wrds_access_{stamp}.json", result)
        _print_wrds(result)
        print(f"\nReport written to {path}")
        return 0

    _print_status(lake)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command line entry point for deterministic skills: ``uv run saa-skill <skill>``."""

from __future__ import annotations

import argparse
import logging
import sys

from saa.config import load_config
from saa.data.store import DataStore
from saa.run import RunContext


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="saa-skill", description="Agentic SAA deterministic skills"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    ha = sub.add_parser(
        "historical-analysis", help="per-asset return, risk and correlation statistics"
    )
    ha.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    ha.add_argument("--run-id", help="write into an existing pipeline run instead of a new one")
    ha.add_argument("--run-dir", help="override the run directory entirely")

    mi = sub.add_parser(
        "macro-inputs", help="point-in-time macro indicator values for the macro agent"
    )
    mi.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    mi.add_argument("--dimension", help="one macro dimension (default: all four scored ones)")
    mi.add_argument(
        "--transform", default="level", help="level, yoy, mom_annualised, diff, zscore, percentile"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    )
    config = load_config()

    if args.command == "historical-analysis":
        from saa.skills.historical_analysis import (
            render_summary,
            run_historical_analysis,
            write_outputs,
        )

        analysis = run_historical_analysis(DataStore(config), as_of=args.as_of)
        run = RunContext.create(config, as_of=analysis.as_of, run_id=args.run_id, root=args.run_dir)
        written = write_outputs(analysis, run)
        print(render_summary(analysis))
        print(f"Wrote {len(written)} files for {len(analysis.stats)} assets to {run.root}")

    if args.command == "macro-inputs":
        from saa.contracts.macro import DIMENSIONS
        from saa.skills.macro_inputs import dimension_requests, indicators, pit_quality, to_frame

        store = DataStore(config)
        dimensions = [args.dimension] if args.dimension else list(DIMENSIONS)
        requests = [
            request
            for dimension in dimensions
            for request in dimension_requests(config, dimension, transform=args.transform)
        ]
        found = indicators(store, requests, as_of=args.as_of)
        print(to_frame(found).to_string(index=False))
        for quality in pit_quality(found):
            print(
                f"{quality.dimension}: {quality.indicators_point_in_time}/"
                f"{quality.indicators_total} indicators from an ALFRED vintage"
            )
        missing = {r.series_id for r in requests} - {i.series_id for i in found}
        if missing:
            print(f"insufficient history at this date: {sorted(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

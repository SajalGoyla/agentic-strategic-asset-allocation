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
    return 0


if __name__ == "__main__":
    sys.exit(main())

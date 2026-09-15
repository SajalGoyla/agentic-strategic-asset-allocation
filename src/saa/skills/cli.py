"""Command line entry point for deterministic skills: ``uv run saa-skill <skill>``."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from saa.config import load_config
from saa.data.store import DataStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="saa-skill", description="Agentic SAA deterministic skills"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    ha = sub.add_parser(
        "historical-analysis", help="per-asset return, risk and correlation statistics"
    )
    ha.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    ha.add_argument(
        "--out", help="output directory (default: data/skills/historical_analysis/<as_of>)"
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
        out = (
            Path(args.out)
            if args.out
            else (
                config.settings.data_dir
                / "skills"
                / "historical_analysis"
                / analysis.as_of.isoformat()
            )
        )
        write_outputs(analysis, out)
        print(render_summary(analysis))
        print(f"Wrote {len(analysis.assets)} asset reports to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

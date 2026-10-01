"""Command line entry point for agents: ``uv run saa-agent <agent>``.

``--no-llm`` runs only the deterministic half of a stage: no API key, no spend. ``macro
--no-llm`` is the mode the regime backtest uses and the quickest way to check a change to
``config/macro_scoring.yaml``; ``pc --no-llm`` produces every candidate portfolio and its
statistics without writing a rationale.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from saa.config import load_config
from saa.data.store import DataStore


def _add_macro(sub) -> None:
    macro = sub.add_parser("macro", help="classify the current macro regime (stage 1)")
    macro.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    macro.add_argument("--out", help="output directory (default: data/runs/<run_id>/macro)")
    macro.add_argument("--run-id", help="pipeline run id to record in every header")
    macro.add_argument(
        "--history-start", default="1995-01-31", help="first month to score (default: 1995-01-31)"
    )
    macro.add_argument(
        "--point-in-time",
        action="store_true",
        help="re-score every month on its own vintage (slow; for backtests)",
    )
    macro.add_argument(
        "--no-llm",
        action="store_true",
        help="deterministic scoring only: no API key needed, no spend, no judgment written",
    )
    macro.add_argument("--cap-usd", type=float, help="stop the run at this spend")
    macro.add_argument("--seed", type=int, help="recorded in every header")


def _run_macro(args, config) -> int:
    from saa.agents.macro import agent as macro_agent

    store = DataStore(config)

    if args.no_llm:
        from saa.skills.macro_regime import score_history

        scoring = macro_agent.load_scoring_config(config)
        panel = score_history(
            store,
            scoring,
            as_of=args.as_of,
            start=args.history_start,
            point_in_time=args.point_in_time,
        )
        latest = panel.latest()
        print(f"\nMacro regime as of {panel.as_of.date()} (deterministic scoring only)\n")
        for dimension, score in latest.items():
            print(f"  {dimension:<22} {score:+.3f}")
        print(f"\n  regime                 {panel.regimes.iloc[-1]}")
        print(f"  confidence             {panel.confidence.iloc[-1]:.2f}")
        print(f"  months scored          {len(panel.scores)}")
        print(f"  point-in-time          {'yes' if panel.point_in_time else 'no'}\n")
        print(panel.regimes.value_counts().to_string())
        return 0

    from saa.llm import Budget, LlmClient

    result = macro_agent.run(
        as_of=args.as_of,
        config=config,
        store=store,
        llm=LlmClient(budget=Budget(cap_usd=args.cap_usd)),
        out_dir=Path(args.out) if args.out else None,
        pipeline_run_id=args.run_id,
        history_start=args.history_start,
        point_in_time=args.point_in_time,
        seed=args.seed,
    )
    print(result.report)
    for name, path in result.paths.items():
        print(f"  {name:<8} {path}")
    print(f"\n  cost     ${result.cost_usd:.4f}")
    return 0


def _add_cma_judge(sub) -> None:
    judge = sub.add_parser("cma-judge", help="select the final CMA per asset (stage 2)")
    judge.add_argument("--run-id", help="the pipeline run holding cma_methods.json", required=True)
    judge.add_argument("--run-dir", help="override the run directory entirely")
    judge.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    judge.add_argument("--assets", nargs="+", help="asset ids (default: all 18)")
    judge.add_argument("--workers", type=int, default=4, help="assets judged concurrently")
    judge.add_argument("--cap-usd", type=float, help="stop the stage at this spend")


def _add_pc(sub) -> None:
    pc = sub.add_parser("pc", help="portfolio-construction agents (stage 4)")
    pc.add_argument("--run-id", help="the pipeline run holding covariance.json", required=True)
    pc.add_argument("--run-dir", help="override the run directory entirely")
    pc.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    pc.add_argument("--methods", nargs="+", help="method ids (default: every implemented method)")
    pc.add_argument("--workers", type=int, default=4, help="agents run concurrently")
    pc.add_argument(
        "--no-llm",
        action="store_true",
        help="weights and statistics only: no API key needed, no spend, no rationale",
    )
    pc.add_argument("--cap-usd", type=float, help="stop the stage at this spend")


def _run_cma_judge(args, config) -> int:
    from saa.agents.cma_judge import render_summary, run_cma_judge, write_summary
    from saa.llm import Budget, LlmClient
    from saa.run import RunContext

    run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
    result = run_cma_judge(
        run,
        config=config,
        llm=LlmClient(budget=Budget(cap_usd=args.cap_usd)),
        assets=args.assets,
        workers=args.workers,
    )
    print(render_summary(result))
    print(f"  summary  {write_summary(result, run)}")
    print(f"  cost     ${result.cost_usd:.4f}")
    return 0 if result.judged and not result.failed else 1


def _run_pc(args, config) -> int:
    from saa.agents.pc import render_summary, run_pc_agents, write_summary
    from saa.llm import Budget, LlmClient
    from saa.run import RunContext

    run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
    llm = None if args.no_llm else LlmClient(budget=Budget(cap_usd=args.cap_usd))
    result = run_pc_agents(
        run, DataStore(config), config=config, llm=llm, methods=args.methods, workers=args.workers
    )
    print(render_summary(result))
    print(f"  summary  {write_summary(result, run)}")
    print(f"  cost     ${result.cost_usd:.4f}")
    return 0 if result.proposals else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="saa-agent", description="Agentic SAA pipeline agents")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_macro(sub)
    _add_cma_judge(sub)
    _add_pc(sub)
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    config = load_config()

    if args.command == "macro":
        return _run_macro(args, config)
    if args.command == "cma-judge":
        return _run_cma_judge(args, config)
    if args.command == "pc":
        return _run_pc(args, config)
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""Command line entry point for agents: ``uv run saa-agent <agent>``.

``--no-llm`` runs only the deterministic half of a stage: no API key, no spend. ``macro
--no-llm`` is the mode the regime backtest uses and the quickest way to check a change to
``config/macro_scoring.yaml``; ``pc --no-llm`` produces every candidate portfolio and its
statistics without writing a rationale, and ``cro --no-llm`` every risk metric and risk score
without writing an assessment.
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
    pc.add_argument(
        "--methods",
        nargs="+",
        help="agent ids (default: the whole roster, including pc_researcher and "
        "adversarial_diversifier)",
    )
    pc.add_argument("--workers", type=int, default=4, help="agents run concurrently")
    pc.add_argument(
        "--no-llm",
        action="store_true",
        help="weights and statistics only: no API key needed, no spend, no rationale",
    )
    pc.add_argument("--cap-usd", type=float, help="stop the stage at this spend")


def _add_cro(sub) -> None:
    cro = sub.add_parser("cro", help="chief risk officer: one risk report per candidate (stage 5)")
    cro.add_argument("--run-id", help="the pipeline run holding the PC proposals", required=True)
    cro.add_argument("--run-dir", help="override the run directory entirely")
    cro.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    cro.add_argument(
        "--agents", nargs="+", help="PC agent ids (default: every proposal in the run)"
    )
    cro.add_argument("--workers", type=int, default=4, help="portfolios assessed concurrently")
    cro.add_argument(
        "--no-llm",
        action="store_true",
        help="metrics and risk scores only: no API key needed, no spend, no assessment",
    )
    cro.add_argument("--cap-usd", type=float, help="stop the stage at this spend")

    pr = sub.add_parser("peer-review", help="each PC agent reviews two peers (stage 5, §3.5)")
    pr.add_argument("--run-id", help="the run holding proposals and CRO reports", required=True)
    pr.add_argument("--run-dir", help="override the run directory entirely")
    pr.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    pr.add_argument("--seed", type=int, help="override the seed derived from the run id")
    pr.add_argument("--workers", type=int, default=4, help="reviews written concurrently")
    pr.add_argument(
        "--no-llm",
        action="store_true",
        help="metric-based reviews only: no API key needed, no spend, no judgment",
    )
    pr.add_argument("--cap-usd", type=float, help="stop the stage at this spend")

    vt = sub.add_parser("vote", help="modified-Borda ballots and the tally (stage 5, §3.5)")
    vt.add_argument(
        "--run-id", help="the run holding proposals, CRO reports and reviews", required=True
    )
    vt.add_argument("--run-dir", help="override the run directory entirely")
    vt.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    vt.add_argument("--workers", type=int, default=4, help="ballots cast concurrently")
    vt.add_argument(
        "--no-llm",
        action="store_true",
        help="metric-ranked ballots only: no API key needed, no spend, no judgment",
    )
    vt.add_argument("--cap-usd", type=float, help="stop the stage at this spend")

    rv = sub.add_parser("revise", help="the shortlisted five revise their proposals (§3.5)")
    rv.add_argument("--run-id", help="the run holding the vote tally", required=True)
    rv.add_argument("--run-dir", help="override the run directory entirely")
    rv.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    rv.add_argument("--workers", type=int, default=4, help="revisions written concurrently")
    rv.add_argument(
        "--no-llm",
        action="store_true",
        help="keep every portfolio unchanged: no API key needed, no spend, no judgment",
    )
    rv.add_argument("--cap-usd", type=float, help="stop the stage at this spend")

    ci = sub.add_parser("cio", help="the recommended allocation and the board memo (stage 6)")
    ci.add_argument("--run-id", help="the run holding the tally and the revisions", required=True)
    ci.add_argument("--run-dir", help="override the run directory entirely")
    ci.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    ci.add_argument(
        "--no-llm",
        action="store_true",
        help="deterministic choice and a templated memo: no API key needed, no spend",
    )
    ci.add_argument("--cap-usd", type=float, help="stop the stage at this spend")


def _run_cro(args, config) -> int:
    from saa.agents.cro import render_summary, run_cro, write_summary
    from saa.llm import Budget, LlmClient
    from saa.run import RunContext

    run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
    llm = None if args.no_llm else LlmClient(budget=Budget(cap_usd=args.cap_usd))
    result = run_cro(
        run, DataStore(config), config=config, llm=llm, agents=args.agents, workers=args.workers
    )
    print(render_summary(result))
    print(f"  summary  {write_summary(result, run)}")
    print(f"  cost     ${result.cost_usd:.4f}")
    return 0 if result.reports else 1


def _run_peer_review(args, config) -> int:
    from saa.agents.peer_review import render_summary, run_peer_reviews, write_summary
    from saa.llm import Budget, LlmClient
    from saa.run import RunContext

    run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
    store = DataStore(config)
    llm = None if args.no_llm else LlmClient(budget=Budget(cap_usd=args.cap_usd))
    labels = None
    if llm is None:
        # The free reviews are scored with the six-dimension metric, whose regime fit needs the
        # regime history; scored here as the method-scores skill does.
        from saa.agents.macro.agent import load_scoring_config
        from saa.skills.macro_regime import score_history

        labels = score_history(store, load_scoring_config(config), as_of=run.as_of).regimes
    result = run_peer_reviews(
        run,
        store,
        config=config,
        llm=llm,
        seed=args.seed,
        workers=args.workers,
        regime_labels=labels,
    )
    print(render_summary(result))
    print(f"  summary  {write_summary(result, run)}")
    print(f"  cost     ${result.cost_usd:.4f}")
    return 0 if result.reviews and not result.skipped else 1


def _regime_labels(store, config, as_of):
    """Month-end regime labels, scored as the method-scores skill does, for the metric score."""
    from saa.agents.macro.agent import load_scoring_config
    from saa.skills.macro_regime import score_history

    return score_history(store, load_scoring_config(config), as_of=as_of).regimes


def _run_vote(args, config) -> int:
    from saa.agents.vote import render_summary, run_vote, write_summary
    from saa.llm import Budget, LlmClient
    from saa.run import RunContext

    run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
    store = DataStore(config)
    llm = None if args.no_llm else LlmClient(budget=Budget(cap_usd=args.cap_usd))
    result = run_vote(
        run,
        store,
        config=config,
        llm=llm,
        workers=args.workers,
        regime_labels=_regime_labels(store, config, run.as_of),
    )
    print(render_summary(result))
    print(f"  summary  {write_summary(result, run)}")
    print(f"  cost     ${result.cost_usd:.4f}")
    return 0 if result.ballots and not result.skipped else 1


def _run_revise(args, config) -> int:
    from saa.agents.revision import render_summary, run_revisions, write_summary
    from saa.llm import Budget, LlmClient
    from saa.run import RunContext

    run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
    llm = None if args.no_llm else LlmClient(budget=Budget(cap_usd=args.cap_usd))
    result = run_revisions(run, DataStore(config), config=config, llm=llm, workers=args.workers)
    print(render_summary(result))
    print(f"  summary  {write_summary(result, run)}")
    print(f"  cost     ${result.cost_usd:.4f}")
    return 0 if result.revisions and not result.skipped else 1


def _run_cio(args, config) -> int:
    from saa.agents.cio import render_summary, run_cio
    from saa.llm import Budget, LlmClient
    from saa.run import RunContext

    run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
    store = DataStore(config)
    llm = None if args.no_llm else LlmClient(budget=Budget(cap_usd=args.cap_usd))
    result = run_cio(
        run, store, config=config, llm=llm, regime_labels=_regime_labels(store, config, run.as_of)
    )
    print(render_summary(result))
    print(f"  memo     {run.report_path('board_memo.md')}")
    print(f"  cost     ${result.cost_usd:.4f}")
    return 0


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
    _add_cro(sub)
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
    if args.command == "cro":
        return _run_cro(args, config)
    if args.command == "peer-review":
        return _run_peer_review(args, config)
    if args.command == "vote":
        return _run_vote(args, config)
    if args.command == "revise":
        return _run_revise(args, config)
    if args.command == "cio":
        return _run_cio(args, config)
    return 1


if __name__ == "__main__":
    sys.exit(main())

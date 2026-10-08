"""Command line entry point for deterministic skills: ``uv run saa-skill <skill>``."""

from __future__ import annotations

import argparse
import logging
import sys

from saa.config import load_config
from saa.data.store import DataStore
from saa.run import RunContext


def _regime_panel(store, config, run, regime_history: str | None):
    """The macro skill's month-end labels and dimension scores, from a file or scored now."""
    if regime_history:
        from saa.contracts.registry import read

        body = read("regime_history", regime_history).body
        import pandas as pd

        months = [pd.Timestamp(m.date) for m in body.months]
        labels = pd.Series([m.regime.value for m in body.months], index=months)
        scores = pd.DataFrame(
            [
                {
                    d: getattr(m, d)
                    for d in ("growth", "inflation", "monetary_policy", "financial_conditions")
                }
                for m in body.months
            ],
            index=months,
        )
        return labels, scores

    from saa.agents.macro.agent import load_scoring_config
    from saa.skills.macro_regime import score_history

    panel = score_history(store, load_scoring_config(config), as_of=run.as_of)
    return panel.regimes, panel.scores


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

    cv = sub.add_parser("covariance", help="annualised covariance matrix for the 18 assets")
    cv.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    cv.add_argument(
        "--method",
        choices=["sample", "ledoit_wolf", "exponential", "regime_conditional"],
        help="estimator written to covariance.json (default: ledoit_wolf)",
    )
    cv.add_argument("--window-years", type=float, help="estimation window (default: all history)")
    cv.add_argument("--halflife-months", type=float, help="exponential half-life (default: 60)")
    cv.add_argument("--regime-history", help="regime_history.json from a macro-agent run")
    cv.add_argument("--regime", help="regime to condition on (default: the latest label)")
    cv.add_argument("--run-id", help="write into an existing pipeline run instead of a new one")
    cv.add_argument("--run-dir", help="override the run directory entirely")

    sg = sub.add_parser("signals", help="asset-level macro, technical and valuation signals")
    sg.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    sg.add_argument("--assets", nargs="+", help="asset ids (default: all 18)")
    sg.add_argument(
        "--regime-history",
        help="regime_history.json from a macro-agent run (default: score the history now)",
    )
    sg.add_argument("--run-id", help="write into an existing pipeline run instead of a new one")
    sg.add_argument("--run-dir", help="override the run directory entirely")

    cm = sub.add_parser("cma-methods", help="every CMA candidate per asset (cma_methods.json)")
    cm.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
    cm.add_argument("--assets", nargs="+", help="asset ids (default: all 18)")
    cm.add_argument(
        "--regime-history",
        help="regime_history.json from a macro-agent run (default: score the history now)",
    )
    cm.add_argument("--run-id", help="write into an existing pipeline run instead of a new one")
    cm.add_argument("--run-dir", help="override the run directory entirely")

    cv_ = sub.add_parser("cma-validate", help="check the CMA layer against expected ranges")
    cv_.add_argument("--run-id", required=True, help="the pipeline run holding cma_methods.json")
    cv_.add_argument("--run-dir", help="override the run directory entirely")
    cv_.add_argument("--as-of", help="information date YYYY-MM-DD (default: today)")
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

    if args.command == "covariance":
        from dataclasses import replace

        from saa.contracts.portfolio import CovarianceMethod
        from saa.skills.covariance import (
            CovarianceSettings,
            compare_estimators,
            regime_labels_from,
            render_report,
            write_outputs,
        )

        settings = CovarianceSettings()
        if args.method:
            settings = replace(settings, method=CovarianceMethod(args.method))
        if args.window_years:
            settings = replace(settings, window_years=args.window_years)
        if args.halflife_months:
            settings = replace(settings, halflife_months=args.halflife_months)
        labels = regime_labels_from(args.regime_history) if args.regime_history else None
        regime = args.regime or (str(labels.iloc[-1]) if labels is not None else None)

        store = DataStore(config)
        estimates = compare_estimators(
            store, as_of=args.as_of, settings=settings, regime=regime, regime_labels=labels
        )
        if settings.method not in estimates:
            parser.error("regime_conditional needs --regime-history")
        run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
        written = write_outputs(settings.method, estimates, run, store.provenance())
        print(render_report(settings.method, estimates, run.as_of))
        print(f"Wrote {', '.join(str(p) for p in written)}")

    if args.command == "signals":
        from saa.skills.signals import render_report, run_signals, write_outputs

        store = DataStore(config)
        run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
        labels, scores = _regime_panel(store, config, run, args.regime_history)
        result = run_signals(
            store,
            as_of=run.as_of,
            regime_labels=labels,
            dimension_scores=scores,
            assets=args.assets,
        )
        written = write_outputs(result, run)
        print(render_report(result))
        print(f"Wrote {len(written)} files for {len(result.bodies)} assets to {run.root}")

    if args.command == "cma-methods":
        from saa.contracts.portfolio import COVARIANCE_CONTRACT
        from saa.contracts.registry import read
        from saa.skills.cma_methods import render_report, run_cma_methods, write_outputs
        from saa.skills.covariance import regime_labels_from

        store = DataStore(config)
        run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
        if args.regime_history:
            labels = regime_labels_from(args.regime_history)
        else:
            from saa.agents.macro.agent import load_scoring_config
            from saa.skills.macro_regime import score_history

            labels = score_history(store, load_scoring_config(config), as_of=run.as_of).regimes
        # Use the run's covariance when the covariance skill already wrote one, so the
        # Black-Litterman candidates and the PC stage see the same matrix.
        covariance, inputs = None, []
        cov_path = run.path(COVARIANCE_CONTRACT)
        if cov_path.exists():
            covariance = read(COVARIANCE_CONTRACT, cov_path).body
            inputs.append(run.input_ref(COVARIANCE_CONTRACT, cov_path))
        result = run_cma_methods(
            store,
            as_of=run.as_of,
            covariance=covariance,
            regime_labels=labels,
            assets=args.assets,
            inputs=inputs,
        )
        written = write_outputs(result, run)
        print(render_report(result).split("## Rationales")[0])
        print(f"Wrote {len(written)} files for {len(result.bodies)} assets to {run.root}")

    if args.command == "cma-validate":
        from saa.skills.cma_methods.validation import (
            Status,
            render_report,
            summary_counts,
            validate_run,
            write_report,
        )

        run = RunContext.create(config, as_of=args.as_of, run_id=args.run_id, root=args.run_dir)
        result = validate_run(run, config)
        print(render_report(result, run.as_of).split("## Every check")[0])
        print(f"Assets: {summary_counts(result)}. Report: {write_report(result, run)}")
        return 1 if result.status is Status.FAIL else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

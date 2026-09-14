"""Ingestion orchestration: fetch -> archive raw -> merge -> write curated -> validate."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

import pandas as pd

from saa.config import Config, load_config
from saa.data.datasets import DATASETS, DatasetSpec
from saa.data.lake import DataLake, new_run_id
from saa.data.sources import SOURCE_REGISTRY
from saa.data.validation import ValidationReport, validate_lake

log = logging.getLogger(__name__)


def merge_with_previous(
    spec: DatasetSpec,
    new: pd.DataFrame,
    previous: pd.DataFrame | None,
    expected: set[str] | None,
) -> tuple[pd.DataFrame, list[str]]:
    """Accumulate snapshot tables, and carry forward entities a source failed to deliver so one
    flaky ticker or series never silently disappears from the latest dataset version."""
    notes: list[str] = []
    if previous is None or previous.empty:
        return new, notes
    if spec.accumulate:
        combined = pd.concat([previous, new], ignore_index=True)
        return combined.drop_duplicates(list(spec.keys), keep="last"), notes
    if spec.entity_col and expected:
        missing = expected - set(new[spec.entity_col].dropna().astype(str))
        carried = previous[previous[spec.entity_col].astype(str).isin(missing)]
        if not carried.empty:
            names = sorted(carried[spec.entity_col].astype(str).unique())
            notes.append(f"{spec.name}: carried forward previous data for {names}")
            new = pd.concat([new, carried], ignore_index=True)
    return new, notes


def run_ingestion(
    config: Config | None = None,
    sources: list[str] | None = None,
    validate: bool = True,
) -> tuple[dict, ValidationReport | None]:
    config = config or load_config()
    lake = DataLake(config.settings.data_dir)
    run_id = new_run_id()
    started_at = datetime.now(UTC)
    source_runs = []

    for name in sources or list(SOURCE_REGISTRY):
        t0 = time.monotonic()
        log.info("ingesting %s", name)
        run = {"source": name, "status": "ok", "datasets": {}, "warnings": [], "error": None}
        try:
            result = SOURCE_REGISTRY[name](config).fetch()
        except Exception as exc:
            log.exception("source %s failed", name)
            run.update(status="failed", error=repr(exc), seconds=round(time.monotonic() - t0, 1))
            source_runs.append(run)
            continue

        run["warnings"].extend(result.warnings)
        if config.settings.keep_raw:
            for filename, payload in result.raw.items():
                lake.write_raw(name, run_id, filename, payload)

        for dataset, frame in result.tables.items():
            spec = DATASETS[dataset]
            previous = lake.read_dataset(dataset) if lake.has_dataset(dataset) else None
            frame, notes = merge_with_previous(
                spec, frame, previous, result.expected_entities.get(dataset)
            )
            run["warnings"].extend(notes)
            version = lake.write_dataset(dataset, frame, run_id=run_id, source=name)
            run["datasets"][dataset] = version["rows"]

        for dataset in sorted(set(result.expected_entities) - set(result.tables)):
            run["warnings"].append(f"{dataset}: source returned no data; previous version kept")
        if not run["datasets"]:
            run["status"] = "failed"
        elif run["warnings"]:
            run["status"] = "ok_with_warnings"
        run["seconds"] = round(time.monotonic() - t0, 1)
        source_runs.append(run)

    summary = {
        "run_id": run_id,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "fred_mode": "api" if config.fred_api_key else "graph_csv",
        "sources": source_runs,
    }
    report = None
    if validate:
        report = validate_lake(config, lake)
        lake.write_json(f"reports/validation_{run_id}.json", report.to_dict())
        summary["validation"] = report.summary()
    lake.write_json(f"runs/{run_id}.json", summary)
    return summary, report

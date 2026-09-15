"""Versioned on-disk data lake.

Layout (under ``data_dir``)::

    raw/<source>/<run_id>/<payload>           exact bytes returned by the source (audit trail)
    curated/<dataset>/<run_id>.parquet        schema-conformed table, one file per ingestion run
    catalog.json                              dataset -> versions (rows, date range, sha256)
    runs/<run_id>.json                        ingestion run log
    reports/validation_<run_id>.json          data-quality report

Curated versions are immutable, so a pipeline run can pin exact dataset versions and be
reproduced later even after newer data has been ingested.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from saa.data.datasets import DATASETS, conform


def new_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, path)


class DataLake:
    def __init__(self, root: Path | str):
        self.root = Path(root)

    # ------------------------------------------------------------------ catalog
    @property
    def catalog_path(self) -> Path:
        return self.root / "catalog.json"

    def load_catalog(self) -> dict:
        if not self.catalog_path.exists():
            return {"datasets": {}}
        return json.loads(self.catalog_path.read_text(encoding="utf-8"))

    def _save_catalog(self, catalog: dict) -> None:
        _atomic_write_bytes(self.catalog_path, json.dumps(catalog, indent=2).encode("utf-8"))

    def version(self, name: str, run_id: str | None = None) -> dict | None:
        entry = self.load_catalog()["datasets"].get(name)
        if not entry:
            return None
        run_id = run_id or entry["latest"]
        for version in entry["versions"]:
            if version["run_id"] == run_id:
                return version
        raise KeyError(f"dataset {name!r} has no version for run {run_id!r}")

    def has_dataset(self, name: str) -> bool:
        return self.version(name) is not None

    # ------------------------------------------------------------------ writes
    def write_raw(self, source: str, run_id: str, filename: str, payload: bytes) -> Path:
        path = self.root / "raw" / source / run_id / filename
        _atomic_write_bytes(path, payload)
        return path

    def write_dataset(self, name: str, df: pd.DataFrame, *, run_id: str, source: str) -> dict:
        spec = DATASETS[name]
        df = conform(df, spec)
        path = self.root / "curated" / name / f"{run_id}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)

        version = {
            "run_id": run_id,
            "source": source,
            "path": path.relative_to(self.root).as_posix(),
            "rows": len(df),
            "sha256": _sha256(path),
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        if spec.date_col and len(df):
            version["min_date"] = df[spec.date_col].min().date().isoformat()
            version["max_date"] = df[spec.date_col].max().date().isoformat()
        if spec.entity_col:
            version["entities"] = int(df[spec.entity_col].nunique())

        catalog = self.load_catalog()
        entry = catalog["datasets"].setdefault(name, {"versions": []})
        entry["description"] = spec.description
        entry["versions"].append(version)
        entry["latest"] = run_id
        self._save_catalog(catalog)
        return version

    def write_json(self, relpath: str, obj: dict) -> Path:
        path = self.root / relpath
        _atomic_write_bytes(path, json.dumps(obj, indent=2, default=str).encode("utf-8"))
        return path

    # ------------------------------------------------------------------ reads
    def read_dataset(self, name: str, run_id: str | None = None) -> pd.DataFrame:
        version = self.version(name, run_id)
        if version is None:
            raise FileNotFoundError(
                f"dataset {name!r} has not been ingested yet; run `uv run saa-data ingest`"
            )
        return pd.read_parquet(self.root / version["path"])

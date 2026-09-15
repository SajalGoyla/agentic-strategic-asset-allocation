"""Export every contract's JSON Schema to ``schemas/`` -- ``uv run saa-contracts``.

Two schemas per contract that has an LLM step:

* ``<name>.schema.json`` -- the whole file, header included. What a reader validates against.
* ``<name>.judgment.schema.json`` -- the model handed to
  ``client.messages.parse(output_format=...)``. Header fields are absent by design: the
  harness writes those, not the model.

The generated files are committed so a schema change shows up as a reviewable diff rather than
as a downstream agent breaking. ``--check`` fails when they are stale, which is what CI runs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from saa.config import PROJECT_ROOT
from saa.contracts.registry import CONTRACTS, json_schema


def schema_files() -> dict[str, dict]:
    """Map output filename -> schema, for every registered contract."""
    out: dict[str, dict] = {}
    for name, spec in sorted(CONTRACTS.items()):
        out[f"{name}.schema.json"] = json_schema(name)
        if spec.judgment is not None:
            out[f"{name}.judgment.schema.json"] = json_schema(name, judgment=True)
    return out


def _serialise(schema: dict) -> str:
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def export(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for filename, schema in schema_files().items():
        path = out_dir / filename
        path.write_text(_serialise(schema), encoding="utf-8")
        written.append(path)
    return written


def check(out_dir: Path) -> list[str]:
    """Return a list of problems; empty means the committed schemas are current."""
    problems = []
    expected = schema_files()
    for filename, schema in expected.items():
        path = out_dir / filename
        if not path.exists():
            problems.append(f"{filename}: missing (run `uv run saa-contracts`)")
        elif path.read_text(encoding="utf-8") != _serialise(schema):
            problems.append(f"{filename}: stale (run `uv run saa-contracts`)")
    for path in sorted(out_dir.glob("*.schema.json")):
        if path.name not in expected:
            problems.append(f"{path.name}: no longer registered; delete it")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="saa-contracts", description="Export agent output-contract JSON Schemas"
    )
    parser.add_argument(
        "--out", type=Path, default=PROJECT_ROOT / "schemas", help="output directory"
    )
    parser.add_argument(
        "--check", action="store_true", help="verify the committed schemas are up to date"
    )
    parser.add_argument("--list", action="store_true", help="list registered contracts")
    args = parser.parse_args(argv)

    if args.list:
        print(f"{'contract':<18} {'stage':<8} {'produced by':<12} file")
        for name, spec in sorted(CONTRACTS.items(), key=lambda kv: (kv[1].stage, kv[0])):
            print(f"{name:<18} {spec.stage:<8} {spec.produced_by.value:<12} {spec.filename}")
        return 0

    if args.check:
        problems = check(args.out)
        for problem in problems:
            print(f"  {problem}")
        print(f"{len(schema_files())} schemas, {len(problems)} problems")
        return 1 if problems else 0

    written = export(args.out)
    print(f"Wrote {len(written)} schemas to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

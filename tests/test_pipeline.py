import pandas as pd

from saa.data import pipeline
from saa.data.datasets import DATASETS
from saa.data.lake import DataLake
from saa.data.pipeline import merge_with_previous
from saa.data.sources.base import FetchResult, Source

CURVE = DATASETS["rates/treasury_par_curve"]


def _curve(curve, value):
    return pd.DataFrame(
        {
            "curve": [curve],
            "date": [pd.Timestamp("2026-01-02")],
            "tenor": ["10Y"],
            "tenor_months": [120.0],
            "yield_pct": [value],
        }
    )


def test_missing_entities_are_carried_forward():
    previous = pd.concat([_curve("nominal", 4.0), _curve("real", 2.0)])
    merged, notes = merge_with_previous(
        CURVE, _curve("nominal", 4.1), previous, {"nominal", "real"}
    )
    assert sorted(merged["curve"]) == ["nominal", "real"]
    assert merged.loc[merged["curve"] == "nominal", "yield_pct"].item() == 4.1
    assert notes and "real" in notes[0]


def test_snapshot_tables_accumulate():
    spec = DATASETS["market/fund_snapshot"]
    row = {c: [None] for c in spec.columns}
    old = pd.DataFrame(
        {
            **row,
            "snapshot_date": [pd.Timestamp("2026-09-01")],
            "ticker": ["SPY"],
            "trailing_pe": [24.0],
        }
    )
    new = pd.DataFrame(
        {
            **row,
            "snapshot_date": [pd.Timestamp("2026-09-14")],
            "ticker": ["SPY"],
            "trailing_pe": [25.0],
        }
    )
    merged, _ = merge_with_previous(spec, new, old, None)
    assert len(merged) == 2


class _FakeTreasury(Source):
    name = "fake"
    calls = 0

    def fetch(self):
        type(self).calls += 1
        result = FetchResult(self.name, expected_entities={CURVE.name: {"nominal", "real"}})
        if self.calls == 1:
            result.tables[CURVE.name] = pd.concat([_curve("nominal", 4.0), _curve("real", 2.0)])
        else:  # second run: the real curve fails
            result.tables[CURVE.name] = _curve("nominal", 4.1)
            result.warnings.append("real: failed")
        result.raw["payload.csv"] = b"x"
        return result


def test_run_ingestion_versions_and_carry_forward(tmp_config, monkeypatch):
    monkeypatch.setattr(pipeline, "SOURCE_REGISTRY", {"fake": _FakeTreasury})
    monkeypatch.setattr(pipeline, "new_run_id", iter(["run1", "run2"]).__next__)

    first, _ = pipeline.run_ingestion(tmp_config, validate=False)
    second, _ = pipeline.run_ingestion(tmp_config, validate=False)

    assert first["sources"][0]["status"] == "ok"
    assert second["sources"][0]["status"] == "ok_with_warnings"
    lake = DataLake(tmp_config.settings.data_dir)
    latest = lake.read_dataset(CURVE.name)
    assert sorted(latest["curve"]) == ["nominal", "real"]
    assert len(lake.read_dataset(CURVE.name, run_id="run1")) == 2
    assert (lake.root / "raw" / "fake" / "run2" / "payload.csv").exists()
    assert (lake.root / "runs" / "run2.json").exists()

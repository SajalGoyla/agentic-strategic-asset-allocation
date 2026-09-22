import dataclasses

import numpy as np
import pandas as pd
import pytest
import yaml

from saa.config import PROJECT_ROOT, load_config
from saa.data.lake import DataLake
from saa.data.store import DataStore
from saa.macro_scoring_config import MacroScoringConfig


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture
def tmp_config(config, tmp_path):
    settings = config.settings.model_copy(update={"data_dir": tmp_path / "data"})
    return dataclasses.replace(config, settings=settings)


@pytest.fixture(scope="session")
def scoring():
    path = PROJECT_ROOT / "config" / "macro_scoring.yaml"
    return MacroScoringConfig.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


# --------------------------------------------------------------- synthetic macro lake
# A small in-memory FRED dataset, so the macro tests stay fast and do not need an ingest.
MACRO_MONTHS = 360


def monthly(values, start="1996-01-31"):
    index = pd.date_range(start, periods=len(values), freq="ME")
    return pd.Series(values, index=index, dtype="float64")


def macro_series(n=MACRO_MONTHS, start="1996-01-31"):
    """Enough indicators per dimension to clear `min_indicators`."""
    rng = np.random.default_rng(7)
    trend = np.linspace(100, 260, n) + rng.normal(0, 1.5, n)
    return {
        "PAYEMS": monthly(trend, start),
        "CFNAI": monthly(rng.normal(0.1, 0.4, n), start),
        "INDPRO": monthly(trend * 0.9, start),
        "CPILFESL": monthly(np.linspace(150, 230, n), start),
        "PCEPILFE": monthly(np.linspace(150, 225, n), start),
        "DFF": monthly(np.abs(rng.normal(2.5, 1.0, n)), start),
        "T10Y3M": monthly(rng.normal(1.2, 0.6, n), start),
        "NFCI": monthly(rng.normal(-0.2, 0.3, n), start),
        "VIXCLS": monthly(np.abs(rng.normal(18, 5, n)), start),
    }


def write_macro_lake(tmp_config, series: dict[str, pd.Series]) -> DataStore:
    frames = [
        pd.DataFrame(
            {
                "series_id": series_id,
                "date": values.index,
                "value": values.to_numpy(dtype="float64"),
                "realtime_start": pd.NaT,
                "realtime_end": pd.NaT,
                "available_from": values.index,
            }
        )
        for series_id, values in series.items()
    ]
    lake = DataLake(tmp_config.settings.data_dir)
    lake.write_dataset(
        "macro/fred_observations", pd.concat(frames, ignore_index=True), run_id="r1", source="test"
    )
    return DataStore(tmp_config)


@pytest.fixture
def macro_store(tmp_config):
    return write_macro_lake(tmp_config, macro_series())

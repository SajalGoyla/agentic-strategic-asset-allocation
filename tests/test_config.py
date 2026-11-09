from collections import Counter

import pytest
import yaml

from saa.data.datasets import DATASETS


def test_universe_matches_ips(config):
    groups = Counter(a.group for a in config.universe.assets)
    assert len(config.universe.assets) == 18
    assert groups == {"equity": 6, "fixed_income": 8, "real_assets": 3, "cash": 1}


def test_macro_catalog_covers_regime_dimensions(config):
    for dimension in ("growth", "inflation", "monetary_policy", "financial_conditions"):
        assert config.macro.by_dimension(dimension), dimension


def test_cma_inputs_reference_known_datasets(config):
    spec = yaml.safe_load((config.config_dir / "cma_inputs.yaml").read_text(encoding="utf-8"))
    for name, item in spec["inputs"].items():
        for dataset in item["datasets"]:
            assert dataset in DATASETS, (name, dataset)
    for method in spec["methods"].values():
        for input_name in method["inputs"]:
            assert input_name in spec["inputs"]


def test_ips_deflator_is_a_declared_macro_series(config):
    """The deflator is the one IPS figure whose absence fails silently: `expected_inflation_pct`
    logs a warning and falls back to trailing CPI, a different quantity worth 1.22pp on the
    return test (decision 55). `load_config` must reject it instead."""
    from saa.config import _cross_validate_ips

    assert config.ips.objectives.return_.expected_inflation_series in set(config.macro.ids)

    broken = config.ips.model_copy(deep=True)
    broken.objectives.return_.expected_inflation_series = "NOT_A_FRED_SERIES"
    with pytest.raises(ValueError, match="expected_inflation_series"):
        _cross_validate_ips(broken, config.universe, config.macro)


def test_ips_deflator_horizon_matches_the_cma_horizon(config):
    """EXPINF3YR is a 3-year expectation and the CMAs are 3-year forecasts (Exhibit 8). If the
    CMA horizon ever moves, the deflator has to move with it."""
    assert config.ips.objectives.cma_horizon_years == 3
    assert config.ips.objectives.return_.expected_inflation_series == "EXPINF3YR"

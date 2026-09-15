from collections import Counter

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

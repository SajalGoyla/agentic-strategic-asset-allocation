import dataclasses

import pytest

from saa.config import load_config


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture
def tmp_config(config, tmp_path):
    settings = config.settings.model_copy(update={"data_dir": tmp_path / "data"})
    return dataclasses.replace(config, settings=settings)

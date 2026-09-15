"""Source connector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd
import requests

from saa.config import Config
from saa.data.http import build_session


@dataclass
class FetchResult:
    source: str
    # dataset name -> frame matching the DatasetSpec columns
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    # dataset name -> entities the source was asked for (drives carry-forward on partial failure)
    expected_entities: dict[str, set[str]] = field(default_factory=dict)
    # filename -> exact payload bytes, archived under raw/<source>/<run_id>/
    raw: dict[str, bytes] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    # reason the source deliberately did not run (e.g. no WRDS credentials); not a failure
    skipped: str | None = None


class Source(ABC):
    name: str

    def __init__(self, config: Config, session: requests.Session | None = None):
        self.config = config
        self.settings = config.settings
        self.session = session or build_session(config.settings.http)

    @abstractmethod
    def fetch(self) -> FetchResult:
        """Download everything this source is configured for. Per-item failures should be
        recorded in ``FetchResult.warnings`` rather than raised."""

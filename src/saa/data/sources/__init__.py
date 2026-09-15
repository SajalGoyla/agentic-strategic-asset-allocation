"""Source connectors. Add a new source by subclassing ``Source`` and registering it here."""

from saa.data.sources.base import FetchResult, Source
from saa.data.sources.fred import FredSource
from saa.data.sources.french import FrenchSource
from saa.data.sources.shiller import ShillerSource
from saa.data.sources.spf import SpfSource
from saa.data.sources.treasury import TreasurySource
from saa.data.sources.worldbank import WorldBankSource
from saa.data.sources.wrds import WrdsSource
from saa.data.sources.yahoo import YahooSource

SOURCE_REGISTRY: dict[str, type[Source]] = {
    "fred": FredSource,
    "yahoo": YahooSource,
    "french": FrenchSource,
    "treasury": TreasurySource,
    "shiller": ShillerSource,
    "spf": SpfSource,
    "worldbank": WorldBankSource,
    "wrds": WrdsSource,  # licensed; skipped without WRDS credentials
}

__all__ = ["SOURCE_REGISTRY", "FetchResult", "Source"]

"""WRDS access check: which subscribed libraries/tables this account can read.

Run before building WRDS connectors, because readable tables depend on the institution's
subscription.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import yaml

from saa.config import Config
from saa.data.wrds_client import WrdsClient


@dataclass
class TableAccess:
    library: str
    table: str
    status: str  # ok | no_access | missing | error
    purpose: str
    improves: str
    detail: str = ""


def classify_error(exc: Exception) -> str:
    message = str(exc).lower()
    if "permission denied" in message or "insufficient" in message:
        return "no_access"
    if "does not exist" in message:
        return "missing"
    return "error"


def check_tables(client, tables: list[dict]) -> list[TableAccess]:
    results = []
    for spec in tables:
        status, detail = "ok", ""
        try:
            client.query(f"select 1 from {spec['library']}.{spec['table']} limit 1")
        except Exception as exc:
            status, detail = classify_error(exc), str(exc).strip().splitlines()[0][:200]
        results.append(
            TableAccess(
                library=spec["library"],
                table=spec["table"],
                status=status,
                purpose=spec.get("purpose", ""),
                improves=spec.get("improves", ""),
                detail=detail,
            )
        )
    return results


def relevant_libraries(libraries: list[str], keywords: list[str]) -> list[str]:
    """Libraries with a name token starting with a keyword ('ice' matches 'ice_bofa', not 'price')."""
    keywords = [k.lower() for k in keywords]
    return sorted(
        lib
        for lib in libraries
        if any(token.startswith(k) for token in lib.lower().split("_") for k in keywords)
    )


def run_check(config: Config) -> dict:
    spec = yaml.safe_load((config.config_dir / "wrds.yaml").read_text(encoding="utf-8"))
    with WrdsClient() as client:
        libraries = client.list_libraries()
        results = check_tables(client, spec["tables"])
        username = client.username
    return {
        "username": username,
        "library_count": len(libraries),
        "relevant_libraries": relevant_libraries(libraries, spec.get("library_keywords", [])),
        "libraries": libraries,
        "tables": [asdict(r) for r in results],
    }

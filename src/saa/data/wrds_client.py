"""Minimal WRDS PostgreSQL client built on psycopg2.

The official ``wrds`` package pins SQLAlchemy < 2, which pandas >= 2.2 cannot use, so queries go
through psycopg2 directly. libpq reads the password from the PostgreSQL password file (created by
``saa-data wrds-login``) or ``PGPASSWORD``; nothing ever prompts, so pipelines cannot hang.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

WRDS_HOST = "wrds-pgdata.wharton.upenn.edu"
WRDS_PORT = 9737
WRDS_DB = "wrds"


def pgpass_path() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", "")) / "postgresql" / "pgpass.conf"
    return Path.home() / ".pgpass"


def credentials_problem() -> str | None:
    """Why a non-interactive WRDS login would fail, or None."""
    if not os.getenv("WRDS_USERNAME"):
        return "WRDS_USERNAME is not set in .env"
    if not os.getenv("PGPASSWORD") and not pgpass_path().exists():
        return f"no saved WRDS password at {pgpass_path()}; run `uv run saa-data wrds-login`"
    return None


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:")


def save_password(username: str, password: str, path: Path | None = None) -> Path:
    """Add or replace this account's WRDS line in the PostgreSQL password file."""
    path = path or pgpass_path()
    prefix = f"{WRDS_HOST}:{WRDS_PORT}:{WRDS_DB}:{_escape(username)}:"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    lines = [line for line in lines if not line.startswith(prefix)] + [prefix + _escape(password)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if os.name != "nt":
        path.chmod(0o600)
    return path


class WrdsClient:
    """Read-only query helper. Each statement autocommits, so one failed query cannot
    poison the next."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        connect_timeout: int = 30,
    ):
        import psycopg2
        import psycopg2.extensions as ext

        self.username = username or os.getenv("WRDS_USERNAME")
        if not self.username:
            raise RuntimeError("WRDS_USERNAME is not set in .env")
        if password is None:
            problem = credentials_problem()
            if problem:
                raise RuntimeError(problem)
        self.conn = psycopg2.connect(
            host=WRDS_HOST,
            port=WRDS_PORT,
            dbname=WRDS_DB,
            user=self.username,
            password=password,
            sslmode="require",
            connect_timeout=connect_timeout,
        )
        self.conn.autocommit = True
        # NUMERIC columns arrive as Decimal by default; return floats for pandas.
        to_float = ext.new_type(
            ext.DECIMAL.values, "DEC2FLOAT", lambda v, _cur: float(v) if v is not None else None
        )
        ext.register_type(to_float, self.conn)

    def query(self, sql: str, params: dict | tuple | None = None) -> pd.DataFrame:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [d.name for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=columns)

    def list_libraries(self) -> list[str]:
        df = self.query(
            "select nspname from pg_namespace "
            "where has_schema_privilege(nspname, 'USAGE') "
            "and nspname not like 'pg\\_%%' and nspname <> 'information_schema' order by 1"
        )
        return df["nspname"].tolist()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> WrdsClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

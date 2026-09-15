import pytest

from saa.data import wrds_access, wrds_client
from saa.data.wrds_access import check_tables, classify_error, relevant_libraries
from saa.data.wrds_client import credentials_problem, save_password


class _FakeClient:
    def __init__(self, errors):
        self.errors = errors

    def query(self, sql):
        for name, error in self.errors.items():
            if name in sql:
                raise error


def test_check_tables_classifies_access():
    client = _FakeClient(
        {
            "comp.funda": RuntimeError("permission denied for schema comp"),
            "ibes.statsum_epsus": RuntimeError('relation "ibes.statsum_epsus" does not exist'),
        }
    )
    tables = [
        {"library": "crsp", "table": "msf"},
        {"library": "comp", "table": "funda"},
        {"library": "ibes", "table": "statsum_epsus"},
    ]
    assert [r.status for r in check_tables(client, tables)] == ["ok", "no_access", "missing"]


def test_classify_unknown_error():
    assert classify_error(RuntimeError("server closed the connection")) == "error"


def test_relevant_libraries_match_name_tokens():
    libs = ["crsp_a_stock", "comp", "wrdsapps_price", "ice_bofa", "optionm"]
    assert relevant_libraries(libs, ["crsp", "comp", "ice"]) == ["comp", "crsp_a_stock", "ice_bofa"]


def test_credentials_problem(monkeypatch, tmp_path):
    monkeypatch.delenv("WRDS_USERNAME", raising=False)
    monkeypatch.delenv("PGPASSWORD", raising=False)
    assert "WRDS_USERNAME" in credentials_problem()

    monkeypatch.setenv("WRDS_USERNAME", "someone")
    monkeypatch.setattr(wrds_client, "pgpass_path", lambda: tmp_path / "pgpass.conf")
    assert "no saved WRDS password" in credentials_problem()

    (tmp_path / "pgpass.conf").write_text("host:9737:wrds:someone:secret\n")
    assert credentials_problem() is None


def test_save_password_escapes_and_replaces_existing_line(tmp_path):
    path = tmp_path / "pg" / "pgpass.conf"
    path.parent.mkdir()
    path.write_text("other.host:5432:db:me:keep\n")
    save_password("me", "old", path)
    save_password("me", "a:b\\c", path)
    lines = path.read_text().splitlines()
    assert lines[0] == "other.host:5432:db:me:keep"
    assert lines[1:] == ["wrds-pgdata.wharton.upenn.edu:9737:wrds:me:a\\:b\\\\c"]


def test_run_check_never_prompts_without_credentials(monkeypatch, config):
    monkeypatch.delenv("WRDS_USERNAME", raising=False)
    with pytest.raises(RuntimeError, match="WRDS_USERNAME"):
        wrds_access.run_check(config)

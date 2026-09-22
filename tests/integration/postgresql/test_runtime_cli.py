"""Integration tests for PostgreSQL runtime inspection CLI."""

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [pytest.mark.integration, pytest.mark.postgresql, pytest.mark.runtime]

runner = CliRunner()


def _host() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_HOST", "127.0.0.1")


def _port() -> int:
    return int(os.getenv("PYDBADMIN_TEST_POSTGRES_PORT", "5432"))


def _database() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_DATABASE", "pydbadmin_test")


def _user() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_USER", "postgres")


def _password() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", "postgres")


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
[connections.local]
engine = "postgresql"
host = "{_host()}"
port = {_port()}
database = "{_database()}"
username = "{_user()}"
environment = "testing"
ssl_mode = "disable"
connect_timeout_seconds = 5

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_TEST_POSTGRES_PASSWORD"
""".strip(),
        encoding="utf-8",
    )
    return path


def _base_args(config: Path) -> list[str]:
    return [
        "--connection",
        "local",
        "--config",
        str(config),
    ]


def test_session_list_includes_current_session_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "session", "list", "--include-self"],
    )

    assert result.exit_code == 0, result.output
    assert "PID\tDATABASE\tUSER" in result.stdout
    assert _database() in result.stdout
    assert _user() in result.stdout


def test_query_list_json_exposes_current_query_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "--output",
            "json",
            "query",
            "list",
            "--include-self",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed
    assert parsed[0]["database"] == _database()
    assert parsed[0]["state"] == "active"


def test_transaction_list_includes_current_transaction_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "transaction", "list", "--include-self"],
    )

    assert result.exit_code == 0, result.output
    assert "PID\tDATABASE\tUSER\tSTATE\tELAPSED_MS" in result.stdout
    assert _database() in result.stdout

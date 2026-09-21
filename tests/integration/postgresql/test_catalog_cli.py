"""Integration tests for PostgreSQL server and database CLI slices."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [pytest.mark.integration, pytest.mark.postgresql]

runner = CliRunner()


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
[connections.local]
engine = "postgresql"
host = "{os.getenv("PYDBADMIN_TEST_POSTGRES_HOST", "127.0.0.1")}"
port = {int(os.getenv("PYDBADMIN_TEST_POSTGRES_PORT", "5432"))}
database = "{os.getenv("PYDBADMIN_TEST_POSTGRES_DATABASE", "pydbadmin_test")}"
username = "{os.getenv("PYDBADMIN_TEST_POSTGRES_USER", "postgres")}"
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


def test_server_info_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "PYDBADMIN_TEST_POSTGRES_PASSWORD",
        os.getenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", "postgres"),
    )
    config = _config(tmp_path)

    result = runner.invoke(app, [*_base_args(config), "server", "info"])

    assert result.exit_code == 0, result.output
    assert "Engine: postgresql" in result.stdout
    assert "Version: 18" in result.stdout
    assert "Database: pydbadmin_test" in result.stdout


def test_database_list_and_describe_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "PYDBADMIN_TEST_POSTGRES_PASSWORD",
        os.getenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", "postgres"),
    )
    config = _config(tmp_path)

    listing = runner.invoke(app, [*_base_args(config), "database", "list"])
    detail = runner.invoke(
        app,
        [*_base_args(config), "database", "describe", "pydbadmin_test"],
    )

    assert listing.exit_code == 0, listing.output
    assert "NAME\tOWNER\tENCODING" in listing.stdout
    assert "pydbadmin_test" in listing.stdout

    assert detail.exit_code == 0, detail.output
    assert "Name: pydbadmin_test" in detail.stdout
    assert "Owner: postgres" in detail.stdout
    assert "Encoding: UTF8" in detail.stdout


def test_database_describe_missing_returns_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "PYDBADMIN_TEST_POSTGRES_PASSWORD",
        os.getenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", "postgres"),
    )
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "database", "describe", "__missing_database__"],
    )

    assert result.exit_code == 5
    assert "was not found or is not visible" in result.output


def test_capability_cli() -> None:
    listing = runner.invoke(app, ["capability", "list"])
    detail = runner.invoke(app, ["capability", "get", "server.info"])

    assert listing.exit_code == 0
    assert "server.info\tavailable" in listing.stdout
    assert "catalog.table.list\tunknown" in listing.stdout
    assert detail.exit_code == 0
    assert "Available: yes" in detail.stdout

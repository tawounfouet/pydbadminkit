"""Integration tests for the first PostgreSQL vertical slice."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pydbadminkit.adapters.postgresql import (
    PostgreSQLConnectionFactory,
    PostgreSQLConnectionTester,
)
from pydbadminkit.cli.app import app
from pydbadminkit.domain.common import DatabaseEngine, EnvironmentName
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SecretValue,
    SSLConfig,
    SSLMode,
    TimeoutConfig,
)

pytestmark = [pytest.mark.integration, pytest.mark.postgresql]


def _password() -> str:
    value = os.getenv("PYDBADMIN_TEST_POSTGRES_PASSWORD")
    if value is None:
        pytest.skip("PYDBADMIN_TEST_POSTGRES_PASSWORD is not configured")
    return value


def _resolved_config() -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("integration"),
        engine=DatabaseEngine.POSTGRESQL,
        host=os.getenv("PYDBADMIN_TEST_POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("PYDBADMIN_TEST_POSTGRES_PORT", "5432")),
        database=os.getenv("PYDBADMIN_TEST_POSTGRES_DATABASE", "pydbadmin_test"),
        username=os.getenv("PYDBADMIN_TEST_POSTGRES_USER", "postgres"),
        password=SecretValue(_password()),
        environment=EnvironmentName.TESTING,
        read_only=False,
        ssl=SSLConfig(mode=SSLMode.DISABLE),
        timeouts=TimeoutConfig(connect_seconds=5),
    )


def test_postgresql_connection_tester() -> None:
    tester = PostgreSQLConnectionTester(PostgreSQLConnectionFactory())

    result = tester.test(_resolved_config())

    assert result.engine is DatabaseEngine.POSTGRESQL
    assert result.version.major == 18
    assert result.current_database == "pydbadmin_test"
    assert result.current_user == "postgres"
    assert result.latency_ms >= 0


def test_connection_test_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    password = _password()
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", password)

    config = tmp_path / "config.toml"
    config.write_text(
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

    result = CliRunner().invoke(
        app,
        [
            "--connection",
            "local",
            "--config",
            str(config),
            "connection",
            "test",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Connection OK" in result.stdout
    assert "Engine: postgresql" in result.stdout
    assert "Database: pydbadmin_test" in result.stdout

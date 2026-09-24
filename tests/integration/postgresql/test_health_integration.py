"""Integration tests for the PostgreSQL health vertical slice."""

import json
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


def test_health_check_json_runs_against_real_postgresql(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "PYDBADMIN_TEST_POSTGRES_PASSWORD",
        os.getenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", "postgres"),
    )
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--config",
            str(_config(tmp_path)),
            "--output",
            "json",
            "health",
            "check",
            "--connection-warning-ratio",
            "0.99",
            "--connection-critical-ratio",
            "1.50",
            "--query-warning-seconds",
            "3600",
            "--query-critical-seconds",
            "7200",
            "--transaction-warning-seconds",
            "3600",
            "--transaction-critical-seconds",
            "7200",
            "--idle-transaction-warning-seconds",
            "3600",
            "--idle-transaction-critical-seconds",
            "7200",
            "--lock-warning-count",
            "100",
            "--lock-critical-count",
            "200",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["overall_status"] == "ok"
    assert [check["name"] for check in parsed["checks"]] == [
        "connectivity",
        "connection_usage",
        "long_queries",
        "long_transactions",
        "idle_transactions",
        "waiting_locks",
    ]
    assert all(check["captured_at"] for check in parsed["checks"])

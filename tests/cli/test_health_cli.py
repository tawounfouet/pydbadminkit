"""Unit tests for the health CLI."""

import json
from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

import pydbadminkit.cli.commands.health as health_module
from pydbadminkit.cli.app import app
from pydbadminkit.domain.monitoring import HealthCheckResult, HealthReport, HealthStatus

pytestmark = [pytest.mark.unit, pytest.mark.cli]

runner = CliRunner()


class FakeHealthService:
    def __init__(self, status: HealthStatus) -> None:
        self.status = status

    def check(self) -> HealthReport:
        captured_at = datetime(2026, 9, 24, tzinfo=UTC)
        check = HealthCheckResult(
            name="connection_usage",
            status=self.status,
            message="observation",
            details={"utilization_ratio": 0.82},
            captured_at=captured_at,
        )
        return HealthReport.from_checks((check,), captured_at=captured_at)


def test_health_check_requires_profile() -> None:
    result = runner.invoke(app, ["health", "check"])

    assert result.exit_code == 2
    assert "Select a profile with --connection" in result.output


def test_health_check_json_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        health_module,
        "build_health_service",
        lambda *args, **kwargs: FakeHealthService(HealthStatus.WARNING),
    )

    result = runner.invoke(
        app,
        ["--connection", "local", "--output", "json", "health", "check"],
    )

    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert list(parsed) == ["overall_status", "checks", "captured_at"]
    assert parsed["overall_status"] == "warning"
    assert parsed["checks"][0]["name"] == "connection_usage"
    assert parsed["checks"][0]["status"] == "warning"
    assert parsed["checks"][0]["details"]["utilization_ratio"] == 0.82


def test_health_check_fail_on_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        health_module,
        "build_health_service",
        lambda *args, **kwargs: FakeHealthService(HealthStatus.WARNING),
    )

    result = runner.invoke(
        app,
        ["--connection", "local", "health", "check", "--fail-on-warning"],
    )

    assert result.exit_code == 1
    assert "Overall status: warning" in result.stdout


def test_health_check_critical_fails_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        health_module,
        "build_health_service",
        lambda *args, **kwargs: FakeHealthService(HealthStatus.CRITICAL),
    )

    result = runner.invoke(app, ["--connection", "local", "health", "check"])

    assert result.exit_code == 1
    assert "Overall status: critical" in result.stdout


def test_health_check_rejects_invalid_thresholds() -> None:
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "health",
            "check",
            "--connection-warning-ratio",
            "0.99",
            "--connection-critical-ratio",
            "0.95",
        ],
    )

    assert result.exit_code == 2
    assert "warning threshold must be lower" in result.output

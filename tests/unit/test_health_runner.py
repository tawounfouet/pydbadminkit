"""Unit tests for HealthCheckRunner."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.application.monitoring.runner import HealthCheckRunner
from pydbadminkit.domain.monitoring import (
    HealthCheckCategory,
    HealthCheckResult,
    HealthStatus,
)
from pydbadminkit.errors import InternalError

pytestmark = pytest.mark.unit


class StaticCheck:
    category = HealthCheckCategory.CONNECTIONS

    def __init__(self, name: str, status: HealthStatus) -> None:
        self.name = name
        self.status = status

    def run(self) -> HealthCheckResult:
        return HealthCheckResult(
            name=self.name,
            status=self.status,
            message="observation",
            captured_at=datetime(2026, 9, 24, tzinfo=UTC),
        )


class FailingCheck:
    category = HealthCheckCategory.QUERIES

    def __init__(self, name: str) -> None:
        self.name = name

    def run(self) -> HealthCheckResult:
        raise InternalError("metric unavailable")


def test_runner_aggregates_results() -> None:
    report = HealthCheckRunner(
        (
            StaticCheck("ok", HealthStatus.OK),
            StaticCheck("warning", HealthStatus.WARNING),
        )
    ).run()

    assert report.overall_status is HealthStatus.WARNING
    assert len(report.checks) == 2


def test_runner_isolates_non_connectivity_failure_as_unknown() -> None:
    report = HealthCheckRunner(
        (
            StaticCheck("ok", HealthStatus.OK),
            FailingCheck("long_queries"),
        )
    ).run()

    assert report.overall_status is HealthStatus.OK
    assert report.checks[1].status is HealthStatus.UNKNOWN
    assert report.checks[1].details == {"error_type": "InternalError"}


def test_runner_treats_connectivity_failure_as_critical() -> None:
    report = HealthCheckRunner((FailingCheck("connectivity"),)).run()

    assert report.overall_status is HealthStatus.CRITICAL
    assert report.checks[0].status is HealthStatus.CRITICAL

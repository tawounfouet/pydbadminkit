"""Release-contract qualification for the complete 0.6.x feature line."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.application.monitoring import HealthCheckConfig
from pydbadminkit.domain.monitoring import (
    CORE_METRIC_REGISTRY,
    HealthCheckEvidence,
    HealthCheckResult,
    HealthReport,
    HealthStatus,
    MetricType,
)
from pydbadminkit.output.serialization import to_machine_value
from pydbadminkit.ports import MetricExporterPort

pytestmark = pytest.mark.unit

CAPTURED_AT = datetime(2026, 9, 24, 10, 0, tzinfo=UTC)


def _result(name: str, status: HealthStatus) -> HealthCheckResult:
    return HealthCheckResult(
        name=name,
        status=status,
        message=f"{name} observation",
        captured_at=CAPTURED_AT,
    )


def test_stable_health_aggregation_contract() -> None:
    critical = HealthReport.from_checks(
        (_result("ok", HealthStatus.OK), _result("critical", HealthStatus.CRITICAL)),
        captured_at=CAPTURED_AT,
    )
    warning = HealthReport.from_checks(
        (_result("unknown", HealthStatus.UNKNOWN), _result("warning", HealthStatus.WARNING)),
        captured_at=CAPTURED_AT,
    )
    mixed_ok_unknown = HealthReport.from_checks(
        (_result("ok", HealthStatus.OK), _result("unknown", HealthStatus.UNKNOWN)),
        captured_at=CAPTURED_AT,
    )
    all_unknown = HealthReport.from_checks(
        (_result("one", HealthStatus.UNKNOWN), _result("two", HealthStatus.UNKNOWN)),
        captured_at=CAPTURED_AT,
    )

    assert critical.overall_status is HealthStatus.CRITICAL
    assert warning.overall_status is HealthStatus.WARNING
    assert mixed_ok_unknown.overall_status is HealthStatus.OK
    assert all_unknown.overall_status is HealthStatus.UNKNOWN


def test_stable_threshold_configuration_defaults() -> None:
    config = HealthCheckConfig()

    assert (config.connection_usage.warning, config.connection_usage.critical) == (0.80, 0.95)
    assert (config.long_queries_seconds.warning, config.long_queries_seconds.critical) == (
        30.0,
        300.0,
    )
    assert (
        config.long_transactions_seconds.warning,
        config.long_transactions_seconds.critical,
    ) == (60.0, 600.0)
    assert (
        config.idle_transactions_seconds.warning,
        config.idle_transactions_seconds.critical,
    ) == (60.0, 300.0)
    assert (config.waiting_locks.warning, config.waiting_locks.critical) == (1, 10)


def test_stable_machine_health_report_contract() -> None:
    check = HealthCheckResult(
        name="connection_usage",
        status=HealthStatus.WARNING,
        message="connection utilization reached warning threshold",
        details={"utilization_ratio": 0.82},
        captured_at=CAPTURED_AT,
        evidence=(
            HealthCheckEvidence(
                metric="connections.utilization_ratio",
                observed=0.82,
                warning_threshold=0.80,
                critical_threshold=0.95,
            ),
        ),
    )
    report = HealthReport.from_checks((check,), captured_at=CAPTURED_AT)

    assert to_machine_value(report) == {
        "overall_status": "warning",
        "checks": [
            {
                "name": "connection_usage",
                "status": "warning",
                "message": "connection utilization reached warning threshold",
                "details": {"utilization_ratio": 0.82},
                "captured_at": "2026-09-24T10:00:00+00:00",
                "evidence": [
                    {
                        "metric": "connections.utilization_ratio",
                        "observed": 0.82,
                        "warning_threshold": 0.8,
                        "critical_threshold": 0.95,
                    }
                ],
            }
        ],
        "captured_at": "2026-09-24T10:00:00+00:00",
    }


def test_stable_observability_core_contract() -> None:
    descriptor = CORE_METRIC_REGISTRY["connections.total"]

    assert descriptor.metric_type is MetricType.GAUGE
    assert descriptor.unit == "count"
    assert MetricExporterPort.__name__ == "MetricExporterPort"

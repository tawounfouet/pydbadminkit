"""Unit tests for Monitoring Core domain models."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.monitoring import (
    ConnectionStatistics,
    DatabaseSizeMetric,
    HealthCheckResult,
    HealthReport,
    HealthStatus,
    IndexStatistics,
    Metric,
    TableStatistics,
    Threshold,
)

pytestmark = pytest.mark.unit


def test_metric_requires_name_and_aware_timestamp() -> None:
    captured_at = datetime(2026, 9, 24, tzinfo=UTC)
    metric = Metric(
        name="connections.total",
        value=4,
        unit="count",
        labels={"database": "postgres"},
        captured_at=captured_at,
    )

    assert metric.value == 4
    assert metric.labels["database"] == "postgres"

    with pytest.raises(ValueError):
        Metric(" ", 1, "count", {}, captured_at)

    with pytest.raises(ValueError):
        Metric("connections.total", 1, "count", {}, datetime(2026, 9, 24))


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ((HealthStatus.OK, HealthStatus.OK), HealthStatus.OK),
        ((HealthStatus.OK, HealthStatus.UNKNOWN), HealthStatus.OK),
        ((HealthStatus.UNKNOWN, HealthStatus.UNKNOWN), HealthStatus.UNKNOWN),
        ((HealthStatus.OK, HealthStatus.WARNING), HealthStatus.WARNING),
        ((HealthStatus.WARNING, HealthStatus.CRITICAL), HealthStatus.CRITICAL),
        ((), HealthStatus.UNKNOWN),
    ],
)
def test_health_report_aggregates_statuses(
    statuses: tuple[HealthStatus, ...],
    expected: HealthStatus,
) -> None:
    captured_at = datetime(2026, 9, 24, tzinfo=UTC)
    checks = tuple(
        HealthCheckResult(
            name=f"check-{index}",
            status=status,
            message="observation",
            captured_at=captured_at,
        )
        for index, status in enumerate(statuses)
    )

    report = HealthReport.from_checks(checks, captured_at=captured_at)

    assert report.overall_status is expected


def test_threshold_validates_warning_before_critical() -> None:
    assert Threshold(warning=0.8, critical=0.95).warning == 0.8

    with pytest.raises(ValueError):
        Threshold(warning=0.95, critical=0.8)

    with pytest.raises(ValueError):
        Threshold(warning=1, critical=1)

    with pytest.raises(TypeError):
        Threshold(warning=True, critical=2)


def test_statistics_validate_values_and_preserve_identity() -> None:
    table = QualifiedName(schema="public", name="events")
    index = QualifiedName(schema="public", name="events_pkey")

    connections = ConnectionStatistics(4, 1, 2, 1, 100, 0.04)
    database = DatabaseSizeMetric("postgres", 1024)
    table_stats = TableStatistics(table=table, live_tuples=10, dead_tuples=2)
    index_stats = IndexStatistics(index=index, table=table, scans=3, size_bytes=8192)

    assert connections.utilization_ratio == 0.04
    assert database.size_bytes == 1024
    assert table_stats.table == table
    assert index_stats.index == index

    with pytest.raises(ValueError):
        DatabaseSizeMetric("postgres", -1)

    with pytest.raises(ValueError):
        TableStatistics(table=table, dead_tuples=-1)

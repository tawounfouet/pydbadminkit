"""Unit tests for LOT-19 observability foundations."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.application.monitoring import MetricExportService, MonitoringSnapshotService
from pydbadminkit.domain.monitoring import (
    CORE_METRIC_REGISTRY,
    HealthReport,
    HealthStatus,
    Metric,
    MetricCardinalityPolicy,
    MetricDescriptor,
    MetricType,
    MonitoringSnapshot,
    internal_metric_name,
    prometheus_metric_name,
)

pytestmark = pytest.mark.unit

CAPTURED_AT = datetime(2026, 9, 24, tzinfo=UTC)


class RecordingExporter:
    def __init__(self) -> None:
        self.metrics: tuple[Metric, ...] | None = None

    def export(self, metrics: tuple[Metric, ...]) -> None:
        self.metrics = metrics


class FakeMonitoringService:
    def collect_metrics(self) -> tuple[Metric, ...]:
        return (Metric("connections.total", 4, "count", {}, CAPTURED_AT),)


class FakeHealthService:
    def check(self) -> HealthReport:
        return HealthReport(
            overall_status=HealthStatus.OK,
            checks=(),
            captured_at=CAPTURED_AT,
        )


def test_metric_name_rules_and_external_mapping_are_deterministic() -> None:
    assert prometheus_metric_name("connections.total") == "pydbadmin_connections_total"
    assert internal_metric_name("operation.duration_ms") == "pydbadmin.operation.duration_ms"

    with pytest.raises(ValueError):
        Metric("Connections Total", 1, "count", {}, CAPTURED_AT)


def test_metric_descriptor_captures_exporter_semantics() -> None:
    descriptor = MetricDescriptor(
        name="database.size_bytes",
        unit="bytes",
        metric_type=MetricType.GAUGE,
        description="Logical database size.",
        label_names=("database",),
    )

    assert descriptor.metric_type is MetricType.GAUGE
    assert descriptor.label_names == ("database",)
    assert CORE_METRIC_REGISTRY["connections.total"].unit == "count"


def test_default_cardinality_policy_accepts_low_cardinality_labels() -> None:
    metric = Metric(
        "database.size_bytes",
        1024,
        "bytes",
        {"database": "analytics", "environment": "test"},
        CAPTURED_AT,
    )

    MetricCardinalityPolicy().validate(metric)


@pytest.mark.parametrize("label", ["pid", "query_text", "client_address"])
def test_default_cardinality_policy_rejects_forbidden_labels(label: str) -> None:
    metric = Metric("connections.total", 4, "count", {label: "unsafe"}, CAPTURED_AT)

    with pytest.raises(ValueError, match="forbidden exporter labels"):
        MetricCardinalityPolicy().validate(metric)


def test_default_cardinality_policy_rejects_unapproved_labels() -> None:
    metric = Metric(
        "database.size_bytes",
        1024,
        "bytes",
        {"table": "events"},
        CAPTURED_AT,
    )

    with pytest.raises(ValueError, match="unsupported exporter labels"):
        MetricCardinalityPolicy().validate(metric)


def test_metric_export_service_validates_before_export() -> None:
    exporter = RecordingExporter()
    metric = Metric("connections.total", 4, "count", {}, CAPTURED_AT)

    MetricExportService(exporter).export((metric,))

    assert exporter.metrics == (metric,)


def test_metric_export_service_does_not_export_invalid_batch() -> None:
    exporter = RecordingExporter()
    metric = Metric("connections.total", 4, "count", {"pid": "123"}, CAPTURED_AT)

    with pytest.raises(ValueError):
        MetricExportService(exporter).export((metric,))

    assert exporter.metrics is None


def test_monitoring_snapshot_is_machine_serializable_execution_window() -> None:
    health = FakeHealthService().check()
    metric = Metric("connections.total", 4, "count", {}, CAPTURED_AT)
    snapshot = MonitoringSnapshot(
        metrics=(metric,),
        health_report=health,
        captured_at=CAPTURED_AT,
    )

    assert snapshot.metrics == (metric,)
    assert snapshot.health_report.overall_status is HealthStatus.OK

    with pytest.raises(ValueError):
        MonitoringSnapshot(
            metrics=(metric,),
            health_report=health,
            captured_at=datetime(2026, 9, 24),
        )


def test_snapshot_service_composes_metrics_and_health() -> None:
    snapshot = MonitoringSnapshotService(
        FakeMonitoringService(),  # type: ignore[arg-type]
        FakeHealthService(),  # type: ignore[arg-type]
    ).capture()

    assert snapshot.metrics[0].name == "connections.total"
    assert snapshot.health_report.overall_status is HealthStatus.OK
    assert snapshot.captured_at.tzinfo is not None

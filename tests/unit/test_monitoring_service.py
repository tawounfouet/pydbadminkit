"""Unit tests for MonitoringService."""

import pytest

from pydbadminkit.application.monitoring import MonitoringService
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.monitoring import (
    ConnectionStatistics,
    DatabaseSizeMetric,
    IndexStatistics,
    TableStatistics,
)

pytestmark = pytest.mark.unit


class FakeMonitoringPort:
    def get_connection_statistics(self) -> ConnectionStatistics:
        return ConnectionStatistics(8, 2, 5, 1, 10, 0.8)

    def get_database_sizes(self) -> tuple[DatabaseSizeMetric, ...]:
        return (
            DatabaseSizeMetric("analytics", 2048),
            DatabaseSizeMetric("postgres", 1024),
        )

    def get_table_statistics(
        self,
        table: QualifiedName | None = None,
    ) -> tuple[TableStatistics, ...]:
        return (
            TableStatistics(
                table=table or QualifiedName(schema="public", name="events"),
                live_tuples=12,
            ),
        )

    def get_index_statistics(
        self,
        index: QualifiedName | None = None,
    ) -> tuple[IndexStatistics, ...]:
        return (
            IndexStatistics(
                index=index or QualifiedName(schema="public", name="events_pkey"),
                table=QualifiedName(schema="public", name="events"),
                scans=3,
            ),
        )


def test_monitoring_service_exposes_raw_statistics() -> None:
    service = MonitoringService(FakeMonitoringPort())
    table = QualifiedName(schema="public", name="events")
    index = QualifiedName(schema="public", name="events_pkey")

    assert service.get_connection_statistics().total == 8
    assert len(service.get_database_sizes()) == 2
    assert service.get_table_statistics(table)[0].table == table
    assert service.get_index_statistics(index)[0].index == index


def test_collect_metrics_builds_low_cardinality_snapshot() -> None:
    metrics = MonitoringService(FakeMonitoringPort()).collect_metrics()
    by_name = {metric.name: metric for metric in metrics}

    assert by_name["connections.total"].value == 8
    assert by_name["connections.utilization_ratio"].value == 0.8
    database_metrics = [metric for metric in metrics if metric.name == "database.size_bytes"]
    assert [metric.labels["database"] for metric in database_metrics] == [
        "analytics",
        "postgres",
    ]
    assert all(metric.captured_at.tzinfo is not None for metric in metrics)

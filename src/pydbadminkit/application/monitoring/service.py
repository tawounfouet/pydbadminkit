"""Monitoring application service."""

from datetime import UTC, datetime

from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.monitoring import (
    ConnectionStatistics,
    DatabaseSizeMetric,
    IndexStatistics,
    Metric,
    TableStatistics,
)
from pydbadminkit.ports.monitoring import MonitoringPort


class MonitoringService:
    """Collect read-only point-in-time monitoring facts."""

    def __init__(self, monitoring_port: MonitoringPort) -> None:
        self._monitoring_port = monitoring_port

    def get_connection_statistics(self) -> ConnectionStatistics:
        return self._monitoring_port.get_connection_statistics()

    def get_database_sizes(self) -> tuple[DatabaseSizeMetric, ...]:
        return self._monitoring_port.get_database_sizes()

    def get_table_statistics(
        self,
        table: QualifiedName | None = None,
    ) -> tuple[TableStatistics, ...]:
        return self._monitoring_port.get_table_statistics(table)

    def get_index_statistics(
        self,
        index: QualifiedName | None = None,
    ) -> tuple[IndexStatistics, ...]:
        return self._monitoring_port.get_index_statistics(index)

    def collect_metrics(self) -> tuple[Metric, ...]:
        """Collect the initial low-cardinality monitoring metric set."""

        captured_at = datetime.now(UTC)
        connections = self.get_connection_statistics()
        metrics = [
            Metric("connections.total", connections.total, "count", {}, captured_at),
            Metric("connections.active", connections.active, "count", {}, captured_at),
            Metric("connections.idle", connections.idle, "count", {}, captured_at),
            Metric(
                "connections.idle_in_transaction",
                connections.idle_in_transaction,
                "count",
                {},
                captured_at,
            ),
        ]
        if connections.utilization_ratio is not None:
            metrics.append(
                Metric(
                    "connections.utilization_ratio",
                    connections.utilization_ratio,
                    "ratio",
                    {},
                    captured_at,
                )
            )

        metrics.extend(
            Metric(
                "database.size_bytes",
                size.size_bytes,
                "bytes",
                {"database": size.database},
                captured_at,
            )
            for size in self.get_database_sizes()
        )
        return tuple(metrics)

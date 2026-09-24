"""Database monitoring port."""

from typing import Protocol

from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.monitoring import (
    ConnectionStatistics,
    DatabaseSizeMetric,
    IndexStatistics,
    TableStatistics,
)


class MonitoringPort(Protocol):
    """Engine-neutral boundary for point-in-time monitoring facts."""

    def get_connection_statistics(self) -> ConnectionStatistics:
        """Return current connection utilization facts."""
        ...

    def get_database_sizes(self) -> tuple[DatabaseSizeMetric, ...]:
        """Return visible logical database sizes."""
        ...

    def get_table_statistics(
        self,
        table: QualifiedName | None = None,
    ) -> tuple[TableStatistics, ...]:
        """Return user-table statistics, optionally for one table."""
        ...

    def get_index_statistics(
        self,
        index: QualifiedName | None = None,
    ) -> tuple[IndexStatistics, ...]:
        """Return user-index statistics, optionally for one index."""
        ...

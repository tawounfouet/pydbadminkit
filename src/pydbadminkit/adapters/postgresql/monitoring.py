"""PostgreSQL MonitoringPort implementation."""

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.monitoring import (
    map_connection_statistics,
    map_database_size,
    map_index_statistics,
    map_table_statistics,
)
from pydbadminkit.adapters.postgresql.queries.monitoring import (
    GET_CONNECTION_STATISTICS,
    GET_CONNECTION_STATISTICS_QUERY_ID,
    LIST_DATABASE_SIZES,
    LIST_DATABASE_SIZES_QUERY_ID,
    LIST_INDEX_STATISTICS,
    LIST_INDEX_STATISTICS_QUERY_ID,
    LIST_TABLE_STATISTICS,
    LIST_TABLE_STATISTICS_QUERY_ID,
)
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.monitoring import (
    ConnectionStatistics,
    DatabaseSizeMetric,
    IndexStatistics,
    TableStatistics,
)
from pydbadminkit.errors import CapabilityNotAvailableError, InternalError


class PostgreSQLMonitoringAdapter:
    """Collect point-in-time PostgreSQL monitoring facts."""

    def __init__(self, executor: PostgreSQLExecutor) -> None:
        self._executor = executor

    def get_connection_statistics(self) -> ConnectionStatistics:
        row = self._executor.fetch_one(
            GET_CONNECTION_STATISTICS,
            query_id=GET_CONNECTION_STATISTICS_QUERY_ID,
        )
        if row is None:
            raise InternalError("PostgreSQL connection statistics query returned no row.")
        return map_connection_statistics(row)

    def get_database_sizes(self) -> tuple[DatabaseSizeMetric, ...]:
        rows = self._executor.fetch_all(
            LIST_DATABASE_SIZES,
            query_id=LIST_DATABASE_SIZES_QUERY_ID,
        )
        return tuple(map_database_size(row) for row in rows)

    def get_table_statistics(
        self,
        table: QualifiedName | None = None,
    ) -> tuple[TableStatistics, ...]:
        schema, name = self._local_filter(table, "table")
        rows = self._executor.fetch_all(
            LIST_TABLE_STATISTICS,
            (schema, schema, name, name),
            query_id=LIST_TABLE_STATISTICS_QUERY_ID,
        )
        return tuple(map_table_statistics(row) for row in rows)

    def get_index_statistics(
        self,
        index: QualifiedName | None = None,
    ) -> tuple[IndexStatistics, ...]:
        schema, name = self._local_filter(index, "index")
        rows = self._executor.fetch_all(
            LIST_INDEX_STATISTICS,
            (schema, schema, name, name),
            query_id=LIST_INDEX_STATISTICS_QUERY_ID,
        )
        return tuple(map_index_statistics(row) for row in rows)

    @staticmethod
    def _local_filter(
        value: QualifiedName | None,
        resource: str,
    ) -> tuple[str | None, str | None]:
        if value is None:
            return None, None
        if value.database is not None:
            raise CapabilityNotAvailableError(
                f"Cross-database {resource} monitoring is not supported by a PostgreSQL session."
            )
        return value.schema or "public", value.name

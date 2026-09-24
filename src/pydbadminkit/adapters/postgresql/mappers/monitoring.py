"""Map PostgreSQL monitoring rows to public domain models."""

from collections.abc import Mapping
from datetime import datetime

from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.monitoring import (
    ConnectionStatistics,
    DatabaseSizeMetric,
    IndexStatistics,
    TableStatistics,
)
from pydbadminkit.errors import InternalError


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid integer value")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError("expected integer-compatible value")


def _required_int(value: object) -> int:
    result = _optional_int(value)
    if result is None:
        raise TypeError("integer value is required")
    return result


def _optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError("datetime value is required")
    return value


def map_connection_statistics(row: Mapping[str, object]) -> ConnectionStatistics:
    """Map one pg_stat_activity aggregate."""

    try:
        total = _required_int(row["total"])
        maximum = _optional_int(row.get("max_connections"))
        utilization = None if maximum is None or maximum <= 0 else total / maximum
        return ConnectionStatistics(
            total=total,
            active=_required_int(row["active"]),
            idle=_required_int(row["idle"]),
            idle_in_transaction=_required_int(row["idle_in_transaction"]),
            max_connections=maximum,
            utilization_ratio=utilization,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL connection statistics mapping failed.") from error


def map_database_size(row: Mapping[str, object]) -> DatabaseSizeMetric:
    """Map one logical database size."""

    try:
        return DatabaseSizeMetric(
            database=str(row["database"]),
            size_bytes=_required_int(row["size_bytes"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL database size mapping failed.") from error


def map_table_statistics(row: Mapping[str, object]) -> TableStatistics:
    """Map one pg_stat_user_tables observation."""

    try:
        table = QualifiedName(
            schema=str(row["schema_name"]),
            name=str(row["table_name"]),
        )
        return TableStatistics(
            table=table,
            estimated_rows=_optional_int(row.get("estimated_rows")),
            sequential_scans=_optional_int(row.get("sequential_scans")),
            index_scans=_optional_int(row.get("index_scans")),
            live_tuples=_optional_int(row.get("live_tuples")),
            dead_tuples=_optional_int(row.get("dead_tuples")),
            inserted_rows=_optional_int(row.get("inserted_rows")),
            updated_rows=_optional_int(row.get("updated_rows")),
            deleted_rows=_optional_int(row.get("deleted_rows")),
            last_vacuum=_optional_datetime(row.get("last_vacuum")),
            last_autovacuum=_optional_datetime(row.get("last_autovacuum")),
            last_analyze=_optional_datetime(row.get("last_analyze")),
            last_autoanalyze=_optional_datetime(row.get("last_autoanalyze")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL table statistics mapping failed.") from error


def map_index_statistics(row: Mapping[str, object]) -> IndexStatistics:
    """Map one pg_stat_user_indexes observation."""

    try:
        schema = str(row["schema_name"])
        return IndexStatistics(
            index=QualifiedName(schema=schema, name=str(row["index_name"])),
            table=QualifiedName(schema=schema, name=str(row["table_name"])),
            scans=_optional_int(row.get("scans")),
            tuples_read=_optional_int(row.get("tuples_read")),
            tuples_fetched=_optional_int(row.get("tuples_fetched")),
            size_bytes=_optional_int(row.get("size_bytes")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL index statistics mapping failed.") from error

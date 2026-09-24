"""Unit tests for PostgreSQL monitoring adapter."""

from datetime import UTC, datetime
from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.mappers.monitoring import (
    map_connection_statistics,
    map_database_size,
    map_index_statistics,
    map_table_statistics,
)
from pydbadminkit.adapters.postgresql.monitoring import PostgreSQLMonitoringAdapter
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.errors import CapabilityNotAvailableError, InternalError

pytestmark = [pytest.mark.unit, pytest.mark.postgresql]


class FakeExecutor:
    def __init__(
        self,
        *,
        one_by_id: dict[str, dict[str, Any] | None] | None = None,
        many_by_id: dict[str, tuple[dict[str, Any], ...]] | None = None,
    ) -> None:
        self.one_by_id = one_by_id or {}
        self.many_by_id = many_by_id or {}
        self.calls: list[tuple[tuple[object, ...] | None, str]] = []

    def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> dict[str, Any] | None:
        del query
        self.calls.append((params, query_id))
        return self.one_by_id.get(query_id)

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> tuple[dict[str, Any], ...]:
        del query
        self.calls.append((params, query_id))
        return self.many_by_id.get(query_id, ())


def test_monitoring_mappers() -> None:
    observed_at = datetime(2026, 9, 24, tzinfo=UTC)
    connections = map_connection_statistics(
        {
            "total": 8,
            "active": 2,
            "idle": 5,
            "idle_in_transaction": 1,
            "max_connections": 10,
        }
    )
    database = map_database_size({"database": "analytics", "size_bytes": 2048})
    table = map_table_statistics(
        {
            "schema_name": "public",
            "table_name": "events",
            "estimated_rows": 12,
            "sequential_scans": 4,
            "index_scans": 5,
            "live_tuples": 12,
            "dead_tuples": 1,
            "inserted_rows": 12,
            "updated_rows": 0,
            "deleted_rows": 0,
            "last_vacuum": observed_at,
            "last_autovacuum": None,
            "last_analyze": observed_at,
            "last_autoanalyze": None,
        }
    )
    index = map_index_statistics(
        {
            "schema_name": "public",
            "table_name": "events",
            "index_name": "events_pkey",
            "scans": 3,
            "tuples_read": 3,
            "tuples_fetched": 3,
            "size_bytes": 8192,
        }
    )

    assert connections.utilization_ratio == 0.8
    assert database.database == "analytics"
    assert table.table == QualifiedName(schema="public", name="events")
    assert table.last_vacuum == observed_at
    assert index.index == QualifiedName(schema="public", name="events_pkey")


def test_monitoring_mappers_reject_invalid_rows() -> None:
    with pytest.raises(InternalError):
        map_connection_statistics({"total": "bad"})

    with pytest.raises(InternalError):
        map_database_size({"database": "postgres", "size_bytes": True})

    with pytest.raises(InternalError):
        map_table_statistics({"schema_name": "public"})

    with pytest.raises(InternalError):
        map_index_statistics({"schema_name": "public"})


def test_adapter_collects_monitoring_facts_and_filters() -> None:
    executor = FakeExecutor(
        one_by_id={
            "PG_MONITORING_CONNECTION_STATISTICS": {
                "total": 2,
                "active": 1,
                "idle": 1,
                "idle_in_transaction": 0,
                "max_connections": 100,
            }
        },
        many_by_id={
            "PG_MONITORING_DATABASE_SIZES": (
                {"database": "postgres", "size_bytes": 4096},
            ),
            "PG_MONITORING_TABLE_STATISTICS": (
                {
                    "schema_name": "public",
                    "table_name": "events",
                    "estimated_rows": 10,
                    "sequential_scans": 1,
                    "index_scans": 2,
                    "live_tuples": 10,
                    "dead_tuples": 0,
                    "inserted_rows": 10,
                    "updated_rows": 0,
                    "deleted_rows": 0,
                    "last_vacuum": None,
                    "last_autovacuum": None,
                    "last_analyze": None,
                    "last_autoanalyze": None,
                },
            ),
            "PG_MONITORING_INDEX_STATISTICS": (
                {
                    "schema_name": "public",
                    "table_name": "events",
                    "index_name": "events_pkey",
                    "scans": 2,
                    "tuples_read": 2,
                    "tuples_fetched": 2,
                    "size_bytes": 8192,
                },
            ),
        },
    )
    adapter = PostgreSQLMonitoringAdapter(executor)  # type: ignore[arg-type]
    table = QualifiedName(name="events")
    index = QualifiedName(schema="public", name="events_pkey")

    assert adapter.get_connection_statistics().total == 2
    assert adapter.get_database_sizes()[0].size_bytes == 4096
    assert adapter.get_table_statistics(table)[0].table.name == "events"
    assert adapter.get_index_statistics(index)[0].index.name == "events_pkey"
    assert ((("public", "public", "events", "events"), "PG_MONITORING_TABLE_STATISTICS")) in executor.calls


def test_adapter_rejects_empty_connection_result_and_cross_database_filter() -> None:
    adapter = PostgreSQLMonitoringAdapter(FakeExecutor())  # type: ignore[arg-type]

    with pytest.raises(InternalError):
        adapter.get_connection_statistics()

    with pytest.raises(CapabilityNotAvailableError):
        adapter.get_table_statistics(
            QualifiedName(database="other", schema="public", name="events")
        )

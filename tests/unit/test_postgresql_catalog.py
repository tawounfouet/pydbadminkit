"""Unit tests for PostgreSQL server and catalog adapters."""

from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.capabilities import PostgreSQLCapabilityAdapter
from pydbadminkit.adapters.postgresql.catalog import PostgreSQLCatalogAdapter
from pydbadminkit.adapters.postgresql.mappers.database import map_database_info
from pydbadminkit.adapters.postgresql.mappers.server import map_server_info
from pydbadminkit.adapters.postgresql.server import PostgreSQLServerAdapter
from pydbadminkit.domain.common import CapabilityAvailability
from pydbadminkit.errors import (
    CapabilityNotAvailableError,
    InternalError,
    ResourceNotFoundError,
)

pytestmark = pytest.mark.unit


class FakeExecutor:
    def __init__(
        self,
        *,
        one: dict[str, Any] | None = None,
        many: tuple[dict[str, Any], ...] = (),
    ) -> None:
        self.one = one
        self.many = many
        self.calls: list[tuple[str, tuple[object, ...] | None, str]] = []

    def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> dict[str, Any] | None:
        self.calls.append((query, params, query_id))
        return self.one

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> tuple[dict[str, Any], ...]:
        self.calls.append((query, params, query_id))
        return self.many


def test_map_server_info() -> None:
    info = map_server_info(
        {
            "server_version_num": 180001,
            "current_database": "postgres",
            "current_user": "postgres",
        }
    )
    assert info.version.major == 18
    assert info.version.minor == 1
    assert info.current_database == "postgres"


def test_map_server_info_rejects_invalid_row() -> None:
    with pytest.raises(InternalError):
        map_server_info({"server_version_num": "not-an-int"})


def test_map_database_info() -> None:
    info = map_database_info(
        {
            "name": "analytics",
            "owner": "postgres",
            "encoding": "UTF8",
            "collation": "C.UTF-8",
            "allow_connections": True,
            "connection_limit": -1,
            "size_bytes": 1024,
        }
    )
    assert info.name == "analytics"
    assert info.allow_connections is True
    assert info.size_bytes == 1024


def test_map_database_info_rejects_invalid_bool() -> None:
    with pytest.raises(InternalError):
        map_database_info({"name": "analytics", "allow_connections": "yes"})


def test_server_adapter_maps_executor_result() -> None:
    executor = FakeExecutor(
        one={
            "server_version_num": 180000,
            "current_database": "postgres",
            "current_user": "postgres",
        }
    )
    adapter = PostgreSQLServerAdapter(executor)  # type: ignore[arg-type]

    info = adapter.get_info()

    assert info.version.major == 18
    assert executor.calls[0][2] == "PG_SERVER_INFO"


def test_server_adapter_rejects_empty_result() -> None:
    adapter = PostgreSQLServerAdapter(FakeExecutor())  # type: ignore[arg-type]

    with pytest.raises(InternalError):
        adapter.get_info()


def test_catalog_adapter_lists_databases() -> None:
    executor = FakeExecutor(
        many=(
            {
                "name": "analytics",
                "owner": "postgres",
                "encoding": "UTF8",
                "collation": "C.UTF-8",
                "allow_connections": True,
                "connection_limit": -1,
                "size_bytes": 2048,
            },
        )
    )
    adapter = PostgreSQLCatalogAdapter(executor)  # type: ignore[arg-type]

    databases = adapter.list_databases()

    assert [database.name for database in databases] == ["analytics"]
    assert executor.calls[0][2] == "PG_LIST_DATABASES"


def test_catalog_adapter_get_database_and_missing() -> None:
    row = {
        "name": "analytics",
        "owner": "postgres",
        "encoding": "UTF8",
        "collation": "C.UTF-8",
        "allow_connections": True,
        "connection_limit": -1,
        "size_bytes": 2048,
    }
    adapter = PostgreSQLCatalogAdapter(FakeExecutor(one=row))  # type: ignore[arg-type]
    assert adapter.get_database("analytics").name == "analytics"

    missing = PostgreSQLCatalogAdapter(FakeExecutor(one=None))  # type: ignore[arg-type]
    with pytest.raises(ResourceNotFoundError):
        missing.get_database("missing")


def test_unimplemented_catalog_capabilities_fail_explicitly() -> None:
    adapter = PostgreSQLCatalogAdapter(FakeExecutor())  # type: ignore[arg-type]

    with pytest.raises(CapabilityNotAvailableError):
        adapter.list_schemas()
    with pytest.raises(CapabilityNotAvailableError):
        adapter.list_tables()
    with pytest.raises(CapabilityNotAvailableError):
        adapter.describe_table(None)  # type: ignore[arg-type]


def test_postgresql_capability_adapter() -> None:
    adapter = PostgreSQLCapabilityAdapter()

    available = adapter.get_capability("catalog.database.list")
    planned = adapter.get_capability("catalog.table.list")
    unknown = adapter.get_capability("future.unknown")

    assert available.availability is CapabilityAvailability.AVAILABLE
    assert available.available is True
    assert planned.availability is CapabilityAvailability.UNKNOWN
    assert planned.reason is not None
    assert unknown.availability is CapabilityAvailability.UNKNOWN
    assert [item.name for item in adapter.list_capabilities()] == sorted(
        item.name for item in adapter.list_capabilities()
    )

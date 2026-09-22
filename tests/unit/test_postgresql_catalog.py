"""Unit tests for PostgreSQL server and catalog adapters."""

from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.capabilities import PostgreSQLCapabilityAdapter
from pydbadminkit.adapters.postgresql.catalog import PostgreSQLCatalogAdapter
from pydbadminkit.adapters.postgresql.mappers.database import map_database_info
from pydbadminkit.adapters.postgresql.mappers.schema import map_schema_info
from pydbadminkit.adapters.postgresql.mappers.server import map_server_info
from pydbadminkit.adapters.postgresql.mappers.table import (
    build_table_description,
    map_column_info,
    map_constraint_info,
    map_table_info,
)
from pydbadminkit.adapters.postgresql.server import PostgreSQLServerAdapter
from pydbadminkit.domain.catalog import ConstraintType, TableKind
from pydbadminkit.domain.common import (
    CapabilityAvailability,
    QualifiedName,
)
from pydbadminkit.domain.operations import ExternalTool
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
        one_by_id: dict[str, dict[str, Any] | None] | None = None,
        many_by_id: dict[str, tuple[dict[str, Any], ...]] | None = None,
    ) -> None:
        self.one_by_id = one_by_id or {}
        self.many_by_id = many_by_id or {}
        self.calls: list[tuple[str, tuple[object, ...] | None, str]] = []

    def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> dict[str, Any] | None:
        self.calls.append((query, params, query_id))
        return self.one_by_id.get(query_id)

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> tuple[dict[str, Any], ...]:
        self.calls.append((query, params, query_id))
        return self.many_by_id.get(query_id, ())


def _database_row(name: str = "analytics") -> dict[str, Any]:
    return {
        "name": name,
        "owner": "postgres",
        "encoding": "UTF8",
        "collation": "C.UTF-8",
        "allow_connections": True,
        "connection_limit": -1,
        "size_bytes": 2048,
    }


def _table_row(name: str = "customers") -> dict[str, Any]:
    return {
        "schema_name": "public",
        "name": name,
        "owner": "postgres",
        "relkind": "r",
        "estimated_rows": 42,
        "size_bytes": 8192,
    }


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
    info = map_database_info(_database_row())
    assert info.name == "analytics"
    assert info.allow_connections is True
    assert info.size_bytes == 2048


def test_map_database_info_rejects_invalid_bool() -> None:
    with pytest.raises(InternalError):
        map_database_info({"name": "analytics", "allow_connections": "yes"})


def test_schema_table_column_and_constraint_mappers() -> None:
    schema = map_schema_info(
        {
            "name": "public",
            "owner": "postgres",
            "is_system": False,
        }
    )
    table = map_table_info(_table_row())
    column = map_column_info(
        {
            "name": "id",
            "position": 1,
            "data_type": "bigint",
            "nullable": False,
            "default_expression": None,
            "identity": False,
            "generated": False,
            "comment": "identifier",
        }
    )
    constraint = map_constraint_info(
        {
            "name": "customers_pkey",
            "constraint_type": "p",
            "columns": ["id"],
            "definition": "PRIMARY KEY (id)",
        }
    )

    assert schema.name == "public"
    assert schema.is_system is False
    assert table.kind is TableKind.TABLE
    assert table.name == QualifiedName(schema="public", name="customers")
    assert column.position == 1
    assert column.comment == "identifier"
    assert constraint.constraint_type is ConstraintType.PRIMARY_KEY
    assert constraint.columns == ("id",)


@pytest.mark.parametrize(
    "row",
    [
        {"name": "public", "is_system": "no"},
        {"schema_name": "public", "name": "x", "relkind": "?"},
    ],
)
def test_schema_and_table_mappers_reject_invalid_rows(row: dict[str, Any]) -> None:
    with pytest.raises(InternalError):
        if "schema_name" in row:
            map_table_info(row)
        else:
            map_schema_info(row)


def test_column_and_constraint_mappers_reject_invalid_rows() -> None:
    with pytest.raises(InternalError):
        map_column_info(
            {
                "name": "id",
                "position": True,
                "data_type": "bigint",
                "nullable": False,
                "identity": False,
                "generated": False,
            }
        )

    with pytest.raises(InternalError):
        map_constraint_info(
            {
                "name": "broken",
                "constraint_type": "?",
                "columns": [],
            }
        )


def test_build_table_description() -> None:
    description = build_table_description(
        _table_row(),
        (
            {
                "name": "id",
                "position": 1,
                "data_type": "bigint",
                "nullable": False,
                "default_expression": None,
                "identity": False,
                "generated": False,
                "comment": None,
            },
        ),
        (
            {
                "name": "customers_pkey",
                "constraint_type": "p",
                "columns": ["id"],
                "definition": "PRIMARY KEY (id)",
            },
        ),
    )

    assert description.table.name.name == "customers"
    assert description.columns[0].name == "id"
    assert description.constraints[0].name == "customers_pkey"


def test_server_adapter_maps_executor_result() -> None:
    executor = FakeExecutor(
        one_by_id={
            "PG_SERVER_INFO": {
                "server_version_num": 180000,
                "current_database": "postgres",
                "current_user": "postgres",
            }
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


def test_catalog_adapter_lists_and_gets_databases() -> None:
    executor = FakeExecutor(
        one_by_id={"PG_GET_DATABASE": _database_row()},
        many_by_id={"PG_LIST_DATABASES": (_database_row(),)},
    )
    adapter = PostgreSQLCatalogAdapter(executor)  # type: ignore[arg-type]

    assert [database.name for database in adapter.list_databases()] == ["analytics"]
    assert adapter.get_database("analytics").name == "analytics"

    missing = PostgreSQLCatalogAdapter(FakeExecutor())  # type: ignore[arg-type]
    with pytest.raises(ResourceNotFoundError):
        missing.get_database("missing")


def test_catalog_adapter_lists_and_gets_schemas() -> None:
    schema_row = {
        "name": "public",
        "owner": "postgres",
        "is_system": False,
    }
    executor = FakeExecutor(
        one_by_id={"PG_GET_SCHEMA": schema_row},
        many_by_id={"PG_LIST_SCHEMAS": (schema_row,)},
    )
    adapter = PostgreSQLCatalogAdapter(executor)  # type: ignore[arg-type]

    schemas = adapter.list_schemas()
    schema = adapter.get_schema("public")

    assert schemas[0].name == "public"
    assert schema.owner == "postgres"
    assert executor.calls[0][1] == (False,)

    with pytest.raises(ResourceNotFoundError):
        PostgreSQLCatalogAdapter(FakeExecutor()).get_schema("missing")  # type: ignore[arg-type]


def test_catalog_adapter_lists_tables() -> None:
    executor = FakeExecutor(many_by_id={"PG_LIST_TABLES": (_table_row(),)})
    adapter = PostgreSQLCatalogAdapter(executor)  # type: ignore[arg-type]

    tables = adapter.list_tables(schema="public")

    assert tables[0].name == QualifiedName(schema="public", name="customers")
    assert executor.calls[0][1] == (False, "public", "public")


def test_catalog_adapter_describes_table() -> None:
    executor = FakeExecutor(
        one_by_id={"PG_GET_TABLE": _table_row()},
        many_by_id={
            "PG_GET_TABLE_COLUMNS": (
                {
                    "name": "id",
                    "position": 1,
                    "data_type": "bigint",
                    "nullable": False,
                    "default_expression": None,
                    "identity": False,
                    "generated": False,
                    "comment": None,
                },
            ),
            "PG_GET_TABLE_CONSTRAINTS": (
                {
                    "name": "customers_pkey",
                    "constraint_type": "p",
                    "columns": ["id"],
                    "definition": "PRIMARY KEY (id)",
                },
            ),
        },
    )
    adapter = PostgreSQLCatalogAdapter(executor)  # type: ignore[arg-type]

    description = adapter.describe_table(QualifiedName(schema="public", name="customers"))

    assert description.table.name.name == "customers"
    assert description.columns[0].data_type == "bigint"
    assert description.constraints[0].constraint_type is ConstraintType.PRIMARY_KEY
    assert [call[2] for call in executor.calls] == [
        "PG_GET_TABLE",
        "PG_GET_TABLE_COLUMNS",
        "PG_GET_TABLE_CONSTRAINTS",
    ]


def test_catalog_adapter_defaults_table_schema_to_public() -> None:
    executor = FakeExecutor(one_by_id={"PG_GET_TABLE": _table_row()})
    adapter = PostgreSQLCatalogAdapter(executor)  # type: ignore[arg-type]

    description = adapter.describe_table(QualifiedName(name="customers"))

    assert description.table.name.schema == "public"
    assert executor.calls[0][1] == ("public", "customers")


def test_catalog_adapter_table_not_found_and_cross_database() -> None:
    adapter = PostgreSQLCatalogAdapter(FakeExecutor())  # type: ignore[arg-type]

    with pytest.raises(ResourceNotFoundError):
        adapter.describe_table(QualifiedName(schema="public", name="missing"))

    with pytest.raises(CapabilityNotAvailableError):
        adapter.describe_table(
            QualifiedName(
                database="other",
                schema="public",
                name="customers",
            )
        )


def test_postgresql_capability_adapter() -> None:
    adapter = PostgreSQLCapabilityAdapter()

    database = adapter.get_capability("catalog.database.list")
    table = adapter.get_capability("catalog.table.list")
    view = adapter.get_capability("catalog.view.list")
    index = adapter.get_capability("catalog.index.list")
    runtime_session = adapter.get_capability("runtime.session.list")
    runtime_transaction = adapter.get_capability("runtime.transaction.list")
    runtime_wait = adapter.get_capability("runtime.wait.list")
    runtime_lock = adapter.get_capability("runtime.lock.list")
    runtime_blocking = adapter.get_capability("runtime.blocking.list")
    runtime_cancel = adapter.get_capability("runtime.query.cancel")
    runtime_terminate = adapter.get_capability("runtime.session.terminate")
    restore = adapter.get_capability("backup.restore")
    unknown = adapter.get_capability("future.unknown")

    assert database.availability is CapabilityAvailability.AVAILABLE
    assert table.availability is CapabilityAvailability.AVAILABLE
    assert view.availability is CapabilityAvailability.AVAILABLE
    assert index.availability is CapabilityAvailability.AVAILABLE
    assert runtime_session.availability is CapabilityAvailability.AVAILABLE
    assert runtime_transaction.availability is CapabilityAvailability.AVAILABLE
    assert runtime_wait.availability is CapabilityAvailability.AVAILABLE
    assert runtime_lock.availability is CapabilityAvailability.AVAILABLE
    assert runtime_blocking.availability is CapabilityAvailability.AVAILABLE
    assert runtime_cancel.availability is CapabilityAvailability.AVAILABLE
    assert runtime_terminate.availability is CapabilityAvailability.AVAILABLE
    assert restore.availability is CapabilityAvailability.AVAILABLE
    assert unknown.availability is CapabilityAvailability.UNKNOWN
    assert [item.name for item in adapter.list_capabilities()] == sorted(
        item.name for item in adapter.list_capabilities()
    )


def test_backup_create_capability_reports_missing_pg_dump() -> None:
    class MissingToolResolver:
        def resolve(self, name: str) -> ExternalTool:
            return ExternalTool(
                name=name,
                path=None,
                version=None,
                available=False,
            )

    adapter = PostgreSQLCapabilityAdapter(tool_resolver=MissingToolResolver())

    status = adapter.get_capability("backup.create")

    assert status.availability is CapabilityAvailability.UNAVAILABLE_TOOL
    assert status.reason == "Required tool 'pg_dump' was not found."



def test_backup_restore_capability_reports_missing_native_tools() -> None:
    class PartialToolResolver:
        def resolve(self, name: str) -> ExternalTool:
            if name == "pg_restore":
                return ExternalTool(
                    name=name,
                    path="/usr/bin/pg_restore",
                    version="pg_restore (PostgreSQL) 18.1",
                    available=True,
                )
            return ExternalTool(
                name=name,
                path=None,
                version=None,
                available=False,
            )

    adapter = PostgreSQLCapabilityAdapter(tool_resolver=PartialToolResolver())

    status = adapter.get_capability("backup.restore")

    assert status.availability is CapabilityAvailability.UNAVAILABLE_TOOL
    assert "psql" in (status.reason or "")

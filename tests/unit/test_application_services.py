"""Unit tests for initial application services."""

import pytest

from pydbadminkit.application.catalog import CatalogService
from pydbadminkit.application.server import ServerService
from pydbadminkit.domain.catalog import (
    DatabaseInfo,
    SchemaInfo,
    ServerInfo,
    TableDescription,
    TableInfo,
)
from pydbadminkit.domain.common import DatabaseEngine, DatabaseVersion, QualifiedName

pytestmark = pytest.mark.unit


class FakeServerPort:
    def get_info(self) -> ServerInfo:
        return ServerInfo(
            engine=DatabaseEngine.POSTGRESQL,
            version=DatabaseVersion(18),
            current_database="postgres",
            current_user="postgres",
        )


class FakeCatalogPort:
    def list_databases(self) -> tuple[DatabaseInfo, ...]:
        return (
            DatabaseInfo(name="analytics"),
            DatabaseInfo(name="postgres"),
        )

    def get_database(self, name: str) -> DatabaseInfo:
        return DatabaseInfo(name=name)

    def list_schemas(
        self,
        *,
        include_system: bool = False,
    ) -> tuple[SchemaInfo, ...]:
        if include_system:
            return (
                SchemaInfo(name="pg_catalog", is_system=True),
                SchemaInfo(name="public"),
            )
        return (SchemaInfo(name="public"),)

    def get_schema(self, name: str) -> SchemaInfo:
        return SchemaInfo(name=name)

    def list_tables(
        self,
        *,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[TableInfo, ...]:
        del include_system
        if schema not in (None, "public"):
            return ()
        return (TableInfo(name=QualifiedName(schema="public", name="customers")),)

    def describe_table(self, name: QualifiedName) -> TableDescription:
        return TableDescription(table=TableInfo(name=name), columns=())


def test_server_service_delegates_to_port() -> None:
    service = ServerService(FakeServerPort())
    assert service.get_info().version == DatabaseVersion(18)


def test_catalog_service_delegates_to_port() -> None:
    service = CatalogService(FakeCatalogPort())

    assert [item.name for item in service.list_databases()] == ["analytics", "postgres"]
    assert service.get_database("analytics").name == "analytics"
    assert service.list_schemas()[0].name == "public"
    assert service.list_schemas(include_system=True)[0].is_system is True
    assert service.get_schema("public").name == "public"
    assert service.list_tables(schema="public")[0].name.name == "customers"

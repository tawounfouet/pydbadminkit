"""Catalog application service."""

from pydbadminkit.domain.catalog.database import DatabaseInfo
from pydbadminkit.domain.catalog.index import IndexDescription, IndexInfo
from pydbadminkit.domain.catalog.schema import SchemaInfo
from pydbadminkit.domain.catalog.table import TableDescription, TableInfo
from pydbadminkit.domain.catalog.view import ViewDescription, ViewInfo
from pydbadminkit.domain.common.names import QualifiedName
from pydbadminkit.ports.catalog import CatalogPort


class CatalogService:
    """Application boundary for catalog inspection."""

    def __init__(self, catalog_port: CatalogPort) -> None:
        self._catalog_port = catalog_port

    def list_databases(self) -> tuple[DatabaseInfo, ...]:
        return self._catalog_port.list_databases()

    def get_database(self, name: str) -> DatabaseInfo:
        return self._catalog_port.get_database(name)

    def list_schemas(
        self,
        *,
        include_system: bool = False,
    ) -> tuple[SchemaInfo, ...]:
        return self._catalog_port.list_schemas(include_system=include_system)

    def get_schema(self, name: str) -> SchemaInfo:
        return self._catalog_port.get_schema(name)

    def list_tables(
        self,
        *,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[TableInfo, ...]:
        return self._catalog_port.list_tables(
            schema=schema,
            include_system=include_system,
        )

    def describe_table(self, name: QualifiedName) -> TableDescription:
        return self._catalog_port.describe_table(name)

    def list_views(
        self,
        *,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[ViewInfo, ...]:
        return self._catalog_port.list_views(
            schema=schema,
            include_system=include_system,
        )

    def describe_view(self, name: QualifiedName) -> ViewDescription:
        return self._catalog_port.describe_view(name)

    def list_indexes(
        self,
        *,
        schema: str | None = None,
        table: str | None = None,
        include_system: bool = False,
    ) -> tuple[IndexInfo, ...]:
        return self._catalog_port.list_indexes(
            schema=schema,
            table=table,
            include_system=include_system,
        )

    def describe_index(self, name: QualifiedName) -> IndexDescription:
        return self._catalog_port.describe_index(name)

"""Database catalog inspection port."""

from typing import Protocol

from pydbadminkit.domain.catalog.database import DatabaseInfo
from pydbadminkit.domain.catalog.index import IndexDescription, IndexInfo
from pydbadminkit.domain.catalog.schema import SchemaInfo
from pydbadminkit.domain.catalog.table import TableDescription, TableInfo
from pydbadminkit.domain.catalog.view import ViewDescription, ViewInfo
from pydbadminkit.domain.common.names import QualifiedName


class CatalogPort(Protocol):
    """Engine-independent database catalog inspection contract."""

    def list_databases(self) -> tuple[DatabaseInfo, ...]:
        """Return visible databases in deterministic name order."""
        ...

    def get_database(self, name: str) -> DatabaseInfo:
        """Return one visible database by exact name."""
        ...

    def list_schemas(
        self,
        *,
        include_system: bool = False,
    ) -> tuple[SchemaInfo, ...]:
        """Return visible schemas in deterministic name order."""
        ...

    def get_schema(self, name: str) -> SchemaInfo:
        """Return one visible schema by exact name."""
        ...

    def list_tables(
        self,
        *,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[TableInfo, ...]:
        """Return visible tables in deterministic schema/name order."""
        ...

    def describe_table(self, name: QualifiedName) -> TableDescription:
        """Return a detailed table description."""
        ...

    def list_views(
        self,
        *,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[ViewInfo, ...]:
        """Return visible views in deterministic schema/name order."""
        ...

    def describe_view(self, name: QualifiedName) -> ViewDescription:
        """Return a detailed view description."""
        ...

    def list_indexes(
        self,
        *,
        schema: str | None = None,
        table: str | None = None,
        include_system: bool = False,
    ) -> tuple[IndexInfo, ...]:
        """Return visible indexes in deterministic schema/name order."""
        ...

    def describe_index(self, name: QualifiedName) -> IndexDescription:
        """Return a detailed index description."""
        ...

"""PostgreSQL CatalogPort implementation."""

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.database import map_database_info
from pydbadminkit.adapters.postgresql.queries.databases import (
    GET_DATABASE,
    GET_DATABASE_QUERY_ID,
    LIST_DATABASES,
    LIST_DATABASES_QUERY_ID,
)
from pydbadminkit.domain.catalog import DatabaseInfo, SchemaInfo, TableDescription, TableInfo
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.errors import CapabilityNotAvailableError, ResourceNotFoundError


class PostgreSQLCatalogAdapter:
    """Initial PostgreSQL catalog adapter.

    This slice implements database discovery only. Later slices extend the same
    adapter with schemas, tables and detailed object inspection.
    """

    def __init__(self, executor: PostgreSQLExecutor) -> None:
        self._executor = executor

    def list_databases(self) -> tuple[DatabaseInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_DATABASES,
            query_id=LIST_DATABASES_QUERY_ID,
        )
        return tuple(map_database_info(row) for row in rows)

    def get_database(self, name: str) -> DatabaseInfo:
        row = self._executor.fetch_one(
            GET_DATABASE,
            (name,),
            query_id=GET_DATABASE_QUERY_ID,
        )
        if row is None:
            raise ResourceNotFoundError(f"Database '{name}' was not found or is not visible.")
        return map_database_info(row)

    def list_schemas(self) -> tuple[SchemaInfo, ...]:
        raise CapabilityNotAvailableError("Schema inspection is not implemented yet.")

    def list_tables(
        self,
        *,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[TableInfo, ...]:
        del schema, include_system
        raise CapabilityNotAvailableError("Table inspection is not implemented yet.")

    def describe_table(self, name: QualifiedName) -> TableDescription:
        del name
        raise CapabilityNotAvailableError("Table description is not implemented yet.")

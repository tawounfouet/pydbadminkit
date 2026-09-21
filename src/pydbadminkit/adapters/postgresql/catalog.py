"""PostgreSQL CatalogPort implementation."""

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.database import map_database_info
from pydbadminkit.adapters.postgresql.mappers.schema import map_schema_info
from pydbadminkit.adapters.postgresql.mappers.table import (
    build_table_description,
    map_table_info,
)
from pydbadminkit.adapters.postgresql.queries.databases import (
    GET_DATABASE,
    GET_DATABASE_QUERY_ID,
    LIST_DATABASES,
    LIST_DATABASES_QUERY_ID,
)
from pydbadminkit.adapters.postgresql.queries.schemas import (
    GET_SCHEMA,
    GET_SCHEMA_QUERY_ID,
    LIST_SCHEMAS,
    LIST_SCHEMAS_QUERY_ID,
)
from pydbadminkit.adapters.postgresql.queries.tables import (
    GET_TABLE,
    GET_TABLE_COLUMNS,
    GET_TABLE_COLUMNS_QUERY_ID,
    GET_TABLE_CONSTRAINTS,
    GET_TABLE_CONSTRAINTS_QUERY_ID,
    GET_TABLE_QUERY_ID,
    LIST_TABLES,
    LIST_TABLES_QUERY_ID,
)
from pydbadminkit.domain.catalog import DatabaseInfo, SchemaInfo, TableDescription, TableInfo
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.errors import CapabilityNotAvailableError, ResourceNotFoundError


class PostgreSQLCatalogAdapter:
    """PostgreSQL catalog adapter for databases, schemas and tables."""

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

    def list_schemas(
        self,
        *,
        include_system: bool = False,
    ) -> tuple[SchemaInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_SCHEMAS,
            (include_system,),
            query_id=LIST_SCHEMAS_QUERY_ID,
        )
        return tuple(map_schema_info(row) for row in rows)

    def get_schema(self, name: str) -> SchemaInfo:
        row = self._executor.fetch_one(
            GET_SCHEMA,
            (name,),
            query_id=GET_SCHEMA_QUERY_ID,
        )
        if row is None:
            raise ResourceNotFoundError(f"Schema '{name}' was not found or is not visible.")
        return map_schema_info(row)

    def list_tables(
        self,
        *,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[TableInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_TABLES,
            (include_system, schema, schema),
            query_id=LIST_TABLES_QUERY_ID,
        )
        return tuple(map_table_info(row) for row in rows)

    def describe_table(self, name: QualifiedName) -> TableDescription:
        if name.database is not None:
            raise CapabilityNotAvailableError(
                "Cross-database table inspection is not supported by a PostgreSQL session."
            )

        schema = name.schema or "public"
        table_row = self._executor.fetch_one(
            GET_TABLE,
            (schema, name.name),
            query_id=GET_TABLE_QUERY_ID,
        )
        if table_row is None:
            raise ResourceNotFoundError(
                f"Table '{schema}.{name.name}' was not found or is not visible."
            )

        columns = self._executor.fetch_all(
            GET_TABLE_COLUMNS,
            (schema, name.name),
            query_id=GET_TABLE_COLUMNS_QUERY_ID,
        )
        constraints = self._executor.fetch_all(
            GET_TABLE_CONSTRAINTS,
            (schema, name.name),
            query_id=GET_TABLE_CONSTRAINTS_QUERY_ID,
        )
        return build_table_description(table_row, columns, constraints)

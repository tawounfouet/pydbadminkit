"""PostgreSQL CatalogPort implementation."""

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.database import map_database_info
from pydbadminkit.adapters.postgresql.mappers.index import (
    build_index_description,
    map_index_info,
)
from pydbadminkit.adapters.postgresql.mappers.schema import map_schema_info
from pydbadminkit.adapters.postgresql.mappers.table import (
    build_table_description,
    map_table_info,
)
from pydbadminkit.adapters.postgresql.mappers.view import (
    build_view_description,
    map_view_info,
)
from pydbadminkit.adapters.postgresql.queries.databases import (
    GET_DATABASE,
    GET_DATABASE_QUERY_ID,
    LIST_DATABASES,
    LIST_DATABASES_QUERY_ID,
)
from pydbadminkit.adapters.postgresql.queries.indexes import (
    GET_INDEX,
    GET_INDEX_DETAIL,
    GET_INDEX_DETAIL_QUERY_ID,
    GET_INDEX_QUERY_ID,
    LIST_INDEXES,
    LIST_INDEXES_QUERY_ID,
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
from pydbadminkit.adapters.postgresql.queries.views import (
    GET_VIEW,
    GET_VIEW_COLUMNS,
    GET_VIEW_COLUMNS_QUERY_ID,
    GET_VIEW_DEFINITION,
    GET_VIEW_DEFINITION_QUERY_ID,
    GET_VIEW_QUERY_ID,
    LIST_VIEWS,
    LIST_VIEWS_QUERY_ID,
)
from pydbadminkit.domain.catalog import (
    DatabaseInfo,
    IndexDescription,
    IndexInfo,
    SchemaInfo,
    TableDescription,
    TableInfo,
    ViewDescription,
    ViewInfo,
)
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.errors import CapabilityNotAvailableError, ResourceNotFoundError


class PostgreSQLCatalogAdapter:
    """PostgreSQL catalog adapter for common relational objects."""

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
        self._ensure_local_name(name, "table")
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

    def list_views(
        self,
        *,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[ViewInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_VIEWS,
            (include_system, schema, schema),
            query_id=LIST_VIEWS_QUERY_ID,
        )
        return tuple(map_view_info(row) for row in rows)

    def describe_view(self, name: QualifiedName) -> ViewDescription:
        self._ensure_local_name(name, "view")
        schema = name.schema or "public"
        view_row = self._executor.fetch_one(
            GET_VIEW,
            (schema, name.name),
            query_id=GET_VIEW_QUERY_ID,
        )
        if view_row is None:
            raise ResourceNotFoundError(
                f"View '{schema}.{name.name}' was not found or is not visible."
            )

        columns = self._executor.fetch_all(
            GET_VIEW_COLUMNS,
            (schema, name.name),
            query_id=GET_VIEW_COLUMNS_QUERY_ID,
        )
        definition = self._executor.fetch_one(
            GET_VIEW_DEFINITION,
            (schema, name.name),
            query_id=GET_VIEW_DEFINITION_QUERY_ID,
        )
        return build_view_description(view_row, columns, definition)

    def list_indexes(
        self,
        *,
        schema: str | None = None,
        table: str | None = None,
        include_system: bool = False,
    ) -> tuple[IndexInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_INDEXES,
            (include_system, schema, schema, table, table),
            query_id=LIST_INDEXES_QUERY_ID,
        )
        return tuple(map_index_info(row) for row in rows)

    def describe_index(self, name: QualifiedName) -> IndexDescription:
        self._ensure_local_name(name, "index")
        schema = name.schema or "public"
        index_row = self._executor.fetch_one(
            GET_INDEX,
            (schema, name.name),
            query_id=GET_INDEX_QUERY_ID,
        )
        if index_row is None:
            raise ResourceNotFoundError(
                f"Index '{schema}.{name.name}' was not found or is not visible."
            )

        detail = self._executor.fetch_one(
            GET_INDEX_DETAIL,
            (schema, name.name),
            query_id=GET_INDEX_DETAIL_QUERY_ID,
        )
        return build_index_description(index_row, detail)

    @staticmethod
    def _ensure_local_name(name: QualifiedName, resource: str) -> None:
        if name.database is not None:
            raise CapabilityNotAvailableError(
                f"Cross-database {resource} inspection is not supported by a PostgreSQL session."
            )

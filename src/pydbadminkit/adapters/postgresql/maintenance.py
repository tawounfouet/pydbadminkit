"""PostgreSQL maintenance adapter."""

from datetime import UTC, datetime
from time import perf_counter

import psycopg
from psycopg import sql

from pydbadminkit.adapters.postgresql.connection import PostgreSQLConnectionFactory
from pydbadminkit.adapters.postgresql.errors import translate_database_error
from pydbadminkit.domain.common import (
    DatabaseEngine,
    DatabaseVersion,
    OperationStatus,
    QualifiedName,
)
from pydbadminkit.domain.connection import ResolvedConnectionConfig
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    MaintenanceOperation,
    MaintenanceOperationType,
    MaintenanceProgress,
    ReindexCommand,
    ReindexTargetType,
    VacuumCommand,
)
from pydbadminkit.errors import (
    CapabilityNotAvailableError,
    OperationTimeoutError,
    PyDBAdminError,
    ResourceNotFoundError,
)
from pydbadminkit.errors.context import ErrorContext

_TABLE_RELKINDS = frozenset({"r", "p", "m"})
_INDEX_RELKINDS = frozenset({"i", "I"})


class PostgreSQLMaintenanceAdapter:
    """Execute PostgreSQL maintenance with explicit autocommit semantics."""

    def __init__(
        self,
        *,
        connection_factory: PostgreSQLConnectionFactory,
        config: ResolvedConnectionConfig,
        server_version: DatabaseVersion,
    ) -> None:
        self._connection_factory = connection_factory
        self._config = config
        self._server_version = server_version

    def validate_vacuum(self, command: VacuumCommand) -> None:
        self._ensure_local_name(command.table)
        if command.table is not None:
            self._require_relation(command.table, _TABLE_RELKINDS, "table")

    def validate_analyze(self, command: AnalyzeCommand) -> None:
        self._ensure_local_name(command.table)
        if command.table is not None:
            self._require_relation(command.table, _TABLE_RELKINDS, "table")

    def validate_reindex(self, command: ReindexCommand) -> None:
        self._ensure_local_name(command.target)
        expected = (
            _INDEX_RELKINDS if command.target_type is ReindexTargetType.INDEX else _TABLE_RELKINDS
        )
        self._require_relation(
            command.target,
            expected,
            command.target_type.value,
        )
        if command.concurrently and self._server_version.major < 12:
            raise CapabilityNotAvailableError(
                "REINDEX CONCURRENTLY requires PostgreSQL 12 or newer."
            )

    def vacuum(self, command: VacuumCommand) -> MaintenanceOperation:
        self.validate_vacuum(command)
        query = _vacuum_query(command)
        return self._execute(
            operation_type=MaintenanceOperationType.VACUUM,
            target=command.table,
            query=query,
            statement_timeout_seconds=command.statement_timeout_seconds,
            lock_timeout_seconds=command.lock_timeout_seconds,
        )

    def analyze(self, command: AnalyzeCommand) -> MaintenanceOperation:
        self.validate_analyze(command)
        query = _analyze_query(command)
        return self._execute(
            operation_type=MaintenanceOperationType.ANALYZE,
            target=command.table,
            query=query,
            statement_timeout_seconds=command.statement_timeout_seconds,
            lock_timeout_seconds=command.lock_timeout_seconds,
        )

    def reindex(self, command: ReindexCommand) -> MaintenanceOperation:
        self.validate_reindex(command)
        query = _reindex_query(command)
        return self._execute(
            operation_type=MaintenanceOperationType.REINDEX,
            target=command.target,
            query=query,
            statement_timeout_seconds=command.statement_timeout_seconds,
            lock_timeout_seconds=command.lock_timeout_seconds,
        )

    def list_vacuum_progress(self) -> tuple[MaintenanceProgress, ...]:
        rows = self._fetch_progress(
            """
            SELECT
                p.pid,
                n.nspname AS schema_name,
                c.relname AS relation_name,
                p.phase,
                p.heap_blks_scanned::bigint AS completed,
                p.heap_blks_total::bigint AS total
            FROM pg_catalog.pg_stat_progress_vacuum AS p
            LEFT JOIN pg_catalog.pg_class AS c
              ON c.oid = p.relid
            LEFT JOIN pg_catalog.pg_namespace AS n
              ON n.oid = c.relnamespace
            WHERE p.datname = current_database()

            UNION ALL

            SELECT
                p.pid,
                n.nspname AS schema_name,
                c.relname AS relation_name,
                p.phase,
                p.heap_blks_scanned::bigint AS completed,
                p.heap_blks_total::bigint AS total
            FROM pg_catalog.pg_stat_progress_cluster AS p
            LEFT JOIN pg_catalog.pg_class AS c
              ON c.oid = p.relid
            LEFT JOIN pg_catalog.pg_namespace AS n
              ON n.oid = c.relnamespace
            WHERE p.datname = current_database()
              AND p.command = 'VACUUM FULL'
            ORDER BY pid
            """,
            operation="maintenance.vacuum.progress",
        )
        return tuple(_map_progress(row, MaintenanceOperationType.VACUUM) for row in rows)

    def list_reindex_progress(self) -> tuple[MaintenanceProgress, ...]:
        rows = self._fetch_progress(
            """
            SELECT
                p.pid,
                n.nspname AS schema_name,
                c.relname AS relation_name,
                p.phase,
                p.blocks_done::bigint AS completed,
                p.blocks_total::bigint AS total
            FROM pg_catalog.pg_stat_progress_create_index AS p
            LEFT JOIN pg_catalog.pg_class AS c
              ON c.oid = CASE
                    WHEN p.index_relid <> 0 THEN p.index_relid
                    ELSE p.relid
                 END
            LEFT JOIN pg_catalog.pg_namespace AS n
              ON n.oid = c.relnamespace
            WHERE p.datname = current_database()
              AND p.command IN ('REINDEX', 'REINDEX CONCURRENTLY')
            ORDER BY p.pid
            """,
            operation="maintenance.reindex.progress",
        )
        return tuple(_map_progress(row, MaintenanceOperationType.REINDEX) for row in rows)

    def _execute(
        self,
        *,
        operation_type: MaintenanceOperationType,
        target: QualifiedName | None,
        query: sql.SQL | sql.Composed,
        statement_timeout_seconds: float | None,
        lock_timeout_seconds: float | None,
    ) -> MaintenanceOperation:
        context = ErrorContext(
            operation=f"maintenance.{operation_type.value}",
            engine=DatabaseEngine.POSTGRESQL,
            profile=str(self._config.name),
            environment=self._config.environment,
            resource_name=str(target) if target is not None else self._config.database,
        )
        started_at = datetime.now(UTC)
        started = perf_counter()

        try:
            with (
                self._connection_factory.connect(self._config) as connection,
                connection.cursor() as cursor,
            ):
                _apply_timeout(
                    cursor,
                    "statement_timeout",
                    statement_timeout_seconds,
                )
                _apply_timeout(
                    cursor,
                    "lock_timeout",
                    lock_timeout_seconds,
                )
                cursor.execute(query)
        except PyDBAdminError:
            raise
        except psycopg.Error as error:
            if _is_timeout_error(error):
                raise OperationTimeoutError(
                    f"PostgreSQL {operation_type.value} timed out.",
                    context=context,
                ) from error
            raise translate_database_error(error, context=context) from error

        duration_ms = int((perf_counter() - started) * 1000)
        return MaintenanceOperation(
            operation_type=operation_type,
            target=target,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=OperationStatus.SUCCEEDED,
            duration_ms=duration_ms,
            message=f"{operation_type.value} completed.",
        )

    def _require_relation(
        self,
        name: QualifiedName,
        expected_relkinds: frozenset[str],
        resource: str,
    ) -> None:
        schema_name = name.schema or "public"
        context = ErrorContext(
            operation="maintenance.target.inspect",
            engine=DatabaseEngine.POSTGRESQL,
            profile=str(self._config.name),
            environment=self._config.environment,
            resource_type=resource,
            resource_name=str(name),
        )

        try:
            with (
                self._connection_factory.connect(self._config) as connection,
                connection.cursor() as cursor,
            ):
                cursor.execute(
                    """
                    SELECT c.relkind
                    FROM pg_catalog.pg_class AS c
                    JOIN pg_catalog.pg_namespace AS n
                      ON n.oid = c.relnamespace
                    WHERE n.nspname = %s
                      AND c.relname = %s
                    """,
                    (schema_name, name.name),
                )
                row = cursor.fetchone()
        except PyDBAdminError:
            raise
        except psycopg.Error as error:
            raise translate_database_error(error, context=context) from error

        if row is None or str(row[0]) not in expected_relkinds:
            raise ResourceNotFoundError(
                f"{resource.capitalize()} '{schema_name}.{name.name}' was not found."
            )

    def _fetch_progress(
        self,
        query: str,
        *,
        operation: str,
    ) -> tuple[tuple[object, ...], ...]:
        context = ErrorContext(
            operation=operation,
            engine=DatabaseEngine.POSTGRESQL,
            profile=str(self._config.name),
            environment=self._config.environment,
        )
        try:
            with (
                self._connection_factory.connect(self._config) as connection,
                connection.cursor() as cursor,
            ):
                cursor.execute(query)
                return tuple(cursor.fetchall())
        except PyDBAdminError:
            raise
        except psycopg.Error as error:
            raise translate_database_error(error, context=context) from error

    @staticmethod
    def _ensure_local_name(name: QualifiedName | None) -> None:
        if name is not None and name.database is not None:
            raise CapabilityNotAvailableError(
                "Cross-database maintenance targets are not supported by one PostgreSQL session."
            )


def _vacuum_query(command: VacuumCommand) -> sql.SQL | sql.Composed:
    options: list[sql.SQL] = []
    if command.full:
        options.append(sql.SQL("FULL"))
    if command.freeze:
        options.append(sql.SQL("FREEZE"))
    if command.analyze:
        options.append(sql.SQL("ANALYZE"))

    query: sql.SQL | sql.Composed = sql.SQL("VACUUM")
    if options:
        query += sql.SQL(" ({})").format(sql.SQL(", ").join(options))
    if command.table is not None:
        query += sql.SQL(" {}").format(_identifier(command.table))
    return query


def _analyze_query(command: AnalyzeCommand) -> sql.SQL | sql.Composed:
    query: sql.SQL | sql.Composed = sql.SQL("ANALYZE")
    if command.table is None:
        return query

    query += sql.SQL(" {}").format(_identifier(command.table))
    if command.columns:
        query += sql.SQL(" ({})").format(
            sql.SQL(", ").join(sql.Identifier(column) for column in command.columns)
        )
    return query


def _reindex_query(command: ReindexCommand) -> sql.Composed:
    target_type = sql.SQL(command.target_type.value.upper())
    concurrent = sql.SQL(" CONCURRENTLY") if command.concurrently else sql.SQL("")
    return sql.SQL("REINDEX {}{} {}").format(
        target_type,
        concurrent,
        _identifier(command.target),
    )


def _identifier(name: QualifiedName) -> sql.Identifier:
    if name.schema is None:
        return sql.Identifier(name.name)
    return sql.Identifier(name.schema, name.name)


def _apply_timeout(
    cursor: psycopg.Cursor[tuple[object, ...]],
    setting: str,
    seconds: float | None,
) -> None:
    if seconds is None:
        return
    cursor.execute(
        "SELECT pg_catalog.set_config(%s, %s, false)",
        (setting, f"{seconds:g}s"),
    )


def _is_timeout_error(error: psycopg.Error) -> bool:
    message = str(error).casefold()
    return error.sqlstate in {"57014", "55P03"} and "timeout" in message


def _map_progress(
    row: tuple[object, ...],
    operation_type: MaintenanceOperationType,
) -> MaintenanceProgress:
    pid = int(row[0])
    schema_name = str(row[1]) if row[1] is not None else None
    relation_name = str(row[2]) if row[2] is not None else None
    phase = str(row[3]) if row[3] is not None else None
    completed = int(row[4]) if row[4] is not None else None
    total = int(row[5]) if row[5] is not None else None
    percent = None
    if completed is not None and total is not None and total > 0:
        percent = min(100.0, max(0.0, (completed / total) * 100.0))

    target = None
    if relation_name is not None:
        target = QualifiedName(
            schema=schema_name,
            name=relation_name,
        )

    return MaintenanceProgress(
        operation_type=operation_type,
        pid=pid,
        target=target,
        phase=phase,
        completed=completed,
        total=total,
        percent=percent,
    )

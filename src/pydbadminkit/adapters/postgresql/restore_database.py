"""PostgreSQL restore target database adapter."""

from dataclasses import replace

from psycopg import sql

from pydbadminkit.adapters.postgresql.connection import PostgreSQLConnectionFactory
from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.domain.connection import ResolvedConnectionConfig
from pydbadminkit.errors import InternalError


class PostgreSQLRestoreDatabaseAdapter:
    """Inspect, create and verify PostgreSQL restore targets."""

    def __init__(
        self,
        *,
        executor: PostgreSQLExecutor,
        connection_factory: PostgreSQLConnectionFactory,
        config: ResolvedConnectionConfig,
    ) -> None:
        self._executor = executor
        self._connection_factory = connection_factory
        self._config = config

    def target_exists(self, name: str) -> bool:
        row = self._executor.fetch_one(
            """
            SELECT EXISTS (
                SELECT 1
                FROM pg_catalog.pg_database
                WHERE datname = %s
            ) AS exists
            """,
            (name,),
            query_id="restore.target.exists",
        )
        if row is None or "exists" not in row:
            raise InternalError("Restore target inspection returned an unexpected result.")
        return bool(row["exists"])

    def create_target(self, name: str) -> None:
        query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name))
        self._executor.execute(
            query,
            query_id="restore.target.create",
        )

    def verify_target(self, name: str) -> bool:
        target_config = replace(self._config, database=name)
        with (
            self._connection_factory.connect(target_config) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                """
                SELECT
                    current_database(),
                    EXISTS (
                        SELECT 1
                        FROM pg_catalog.pg_namespace
                        WHERE nspname = 'public'
                    )
                """
            )
            row = cursor.fetchone()

        if row is None or len(row) != 2:
            return False
        return str(row[0]) == name and bool(row[1])

"""Shared PostgreSQL query executor."""

from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from pydbadminkit.adapters.postgresql.connection import PostgreSQLConnectionFactory
from pydbadminkit.adapters.postgresql.errors import translate_database_error
from pydbadminkit.domain.common.engine import DatabaseEngine
from pydbadminkit.domain.connection.resolved import ResolvedConnectionConfig
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.errors.context import ErrorContext


class PostgreSQLExecutor:
    """Execute bounded PostgreSQL adapter queries with shared error translation."""

    def __init__(
        self,
        factory: PostgreSQLConnectionFactory,
        config: ResolvedConnectionConfig,
    ) -> None:
        self._factory = factory
        self._config = config

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> tuple[dict[str, Any], ...]:
        """Execute a read query and return internal dictionary rows."""

        context = ErrorContext(
            operation=query_id,
            engine=DatabaseEngine.POSTGRESQL,
            profile=str(self._config.name),
            environment=self._config.environment,
        )

        try:
            with (
                self._factory.connect(self._config) as connection,
                connection.cursor(row_factory=dict_row) as cursor,
            ):
                cursor.execute(query, params)
                return tuple(dict(row) for row in cursor.fetchall())
        except PyDBAdminError:
            raise
        except psycopg.Error as error:
            raise translate_database_error(error, context=context) from error

    def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> dict[str, Any] | None:
        """Execute a read query expected to return at most one row."""

        rows = self.fetch_all(query, params, query_id=query_id)
        if not rows:
            return None
        return rows[0]

    def execute(
        self,
        query: str | sql.Composable,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> int:
        """Execute one bounded mutation statement and return the driver rowcount."""

        context = ErrorContext(
            operation=query_id,
            engine=DatabaseEngine.POSTGRESQL,
            profile=str(self._config.name),
            environment=self._config.environment,
        )

        try:
            with self._factory.connect(self._config) as connection, connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
        except PyDBAdminError:
            raise
        except psycopg.Error as error:
            raise translate_database_error(error, context=context) from error

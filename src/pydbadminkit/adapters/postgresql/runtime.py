"""PostgreSQL RuntimePort implementation."""

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.runtime import (
    map_query_info,
    map_session_info,
    map_transaction_info,
    postgresql_state_filter,
)
from pydbadminkit.adapters.postgresql.queries.runtime import (
    LIST_QUERIES,
    LIST_QUERIES_QUERY_ID,
    LIST_SESSIONS,
    LIST_SESSIONS_QUERY_ID,
    LIST_TRANSACTIONS,
    LIST_TRANSACTIONS_QUERY_ID,
)
from pydbadminkit.domain.runtime import QueryInfo, SessionInfo, SessionState, TransactionInfo


class PostgreSQLRuntimeAdapter:
    """Inspect live PostgreSQL runtime state through pg_stat_activity."""

    def __init__(self, executor: PostgreSQLExecutor) -> None:
        self._executor = executor

    def list_sessions(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        state: SessionState | None = None,
        include_self: bool = False,
    ) -> tuple[SessionInfo, ...]:
        raw_state = postgresql_state_filter(state)
        rows = self._executor.fetch_all(
            LIST_SESSIONS,
            (
                database,
                database,
                username,
                username,
                raw_state,
                raw_state,
                include_self,
            ),
            query_id=LIST_SESSIONS_QUERY_ID,
        )
        return tuple(map_session_info(row) for row in rows)

    def list_queries(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[QueryInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_QUERIES,
            (
                database,
                database,
                username,
                username,
                include_self,
            ),
            query_id=LIST_QUERIES_QUERY_ID,
        )
        return tuple(map_query_info(row) for row in rows)

    def list_transactions(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[TransactionInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_TRANSACTIONS,
            (
                database,
                database,
                username,
                username,
                include_self,
            ),
            query_id=LIST_TRANSACTIONS_QUERY_ID,
        )
        return tuple(map_transaction_info(row) for row in rows)

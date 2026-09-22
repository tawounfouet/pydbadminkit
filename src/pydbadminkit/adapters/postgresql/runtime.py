"""PostgreSQL RuntimePort implementation."""

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.runtime import (
    map_blocking_relation,
    map_lock_info,
    map_query_info,
    map_session_info,
    map_transaction_info,
    map_wait_info,
    postgresql_state_filter,
)
from pydbadminkit.adapters.postgresql.queries.runtime import (
    LIST_BLOCKING,
    LIST_BLOCKING_QUERY_ID,
    LIST_LOCKS,
    LIST_LOCKS_QUERY_ID,
    LIST_QUERIES,
    LIST_QUERIES_QUERY_ID,
    LIST_SESSIONS,
    LIST_SESSIONS_QUERY_ID,
    LIST_TRANSACTIONS,
    LIST_TRANSACTIONS_QUERY_ID,
    LIST_WAITS,
    LIST_WAITS_QUERY_ID,
)
from pydbadminkit.domain.runtime import (
    BlockingRelation,
    LockInfo,
    QueryInfo,
    SessionInfo,
    SessionState,
    TransactionInfo,
    WaitInfo,
)


class PostgreSQLRuntimeAdapter:
    """Inspect live PostgreSQL runtime state."""

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

    def list_waits(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        wait_event_type: str | None = None,
        include_self: bool = False,
    ) -> tuple[WaitInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_WAITS,
            (
                database,
                database,
                username,
                username,
                wait_event_type,
                wait_event_type,
                include_self,
            ),
            query_id=LIST_WAITS_QUERY_ID,
        )
        return tuple(map_wait_info(row) for row in rows)

    def list_locks(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        granted: bool | None = None,
        include_self: bool = False,
    ) -> tuple[LockInfo, ...]:
        rows = self._executor.fetch_all(
            LIST_LOCKS,
            (
                database,
                database,
                username,
                username,
                granted,
                granted,
                include_self,
            ),
            query_id=LIST_LOCKS_QUERY_ID,
        )
        return tuple(map_lock_info(row) for row in rows)

    def list_blocking(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[BlockingRelation, ...]:
        rows = self._executor.fetch_all(
            LIST_BLOCKING,
            (
                database,
                database,
                username,
                username,
                include_self,
            ),
            query_id=LIST_BLOCKING_QUERY_ID,
        )
        return tuple(map_blocking_relation(row) for row in rows)

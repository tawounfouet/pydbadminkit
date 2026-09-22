"""Runtime administration application service."""

from pydbadminkit.domain.runtime import (
    BlockingRelation,
    LockInfo,
    QueryInfo,
    SessionInfo,
    SessionState,
    TransactionInfo,
    WaitInfo,
)
from pydbadminkit.ports.runtime import RuntimePort


class RuntimeService:
    """Application boundary for read-only runtime inspection."""

    def __init__(self, runtime_port: RuntimePort) -> None:
        self._runtime_port = runtime_port

    def list_sessions(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        state: SessionState | None = None,
        include_self: bool = False,
    ) -> tuple[SessionInfo, ...]:
        return self._runtime_port.list_sessions(
            database=database,
            username=username,
            state=state,
            include_self=include_self,
        )

    def list_queries(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[QueryInfo, ...]:
        return self._runtime_port.list_queries(
            database=database,
            username=username,
            include_self=include_self,
        )

    def list_transactions(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[TransactionInfo, ...]:
        return self._runtime_port.list_transactions(
            database=database,
            username=username,
            include_self=include_self,
        )

    def list_waits(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        wait_event_type: str | None = None,
        include_self: bool = False,
    ) -> tuple[WaitInfo, ...]:
        return self._runtime_port.list_waits(
            database=database,
            username=username,
            wait_event_type=wait_event_type,
            include_self=include_self,
        )

    def list_locks(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        granted: bool | None = None,
        include_self: bool = False,
    ) -> tuple[LockInfo, ...]:
        return self._runtime_port.list_locks(
            database=database,
            username=username,
            granted=granted,
            include_self=include_self,
        )

    def list_blocking(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[BlockingRelation, ...]:
        return self._runtime_port.list_blocking(
            database=database,
            username=username,
            include_self=include_self,
        )

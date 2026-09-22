"""Runtime administration port."""

from typing import Protocol

from pydbadminkit.domain.runtime import (
    BlockingRelation,
    LockInfo,
    QueryInfo,
    SessionInfo,
    SessionState,
    TransactionInfo,
    WaitInfo,
)


class RuntimePort(Protocol):
    """Engine-neutral read boundary for live database runtime state."""

    def list_sessions(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        state: SessionState | None = None,
        include_self: bool = False,
    ) -> tuple[SessionInfo, ...]:
        """List visible sessions."""
        ...

    def list_queries(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[QueryInfo, ...]:
        """List currently active queries."""
        ...

    def list_transactions(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[TransactionInfo, ...]:
        """List open transactions."""
        ...

    def list_waits(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        wait_event_type: str | None = None,
        include_self: bool = False,
    ) -> tuple[WaitInfo, ...]:
        """List backends currently reporting a wait event."""
        ...

    def list_locks(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        granted: bool | None = None,
        include_self: bool = False,
    ) -> tuple[LockInfo, ...]:
        """List backend locks."""
        ...

    def list_blocking(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[BlockingRelation, ...]:
        """List recursive blocking-chain edges."""
        ...

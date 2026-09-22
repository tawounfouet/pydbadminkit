"""Runtime administration port."""

from typing import Protocol

from pydbadminkit.domain.runtime import QueryInfo, SessionInfo, SessionState, TransactionInfo


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

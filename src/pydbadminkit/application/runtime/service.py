"""Runtime administration application service."""

from pydbadminkit.domain.runtime import QueryInfo, SessionInfo, SessionState, TransactionInfo
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

"""Runtime administration read models."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SessionState(StrEnum):
    """Normalized cross-engine session states."""

    ACTIVE = "active"
    IDLE = "idle"
    IDLE_IN_TRANSACTION = "idle_in_transaction"
    IDLE_IN_TRANSACTION_ABORTED = "idle_in_transaction_aborted"
    FASTPATH_FUNCTION_CALL = "fastpath_function_call"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SessionInfo:
    """Read-only summary of one database session."""

    pid: int
    database: str | None = None
    username: str | None = None
    application_name: str | None = None
    client_address: str | None = None
    backend_type: str | None = None
    state: SessionState | None = None
    backend_started_at: datetime | None = None
    state_changed_at: datetime | None = None
    wait_event_type: str | None = None
    wait_event: str | None = None

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("session pid must be > 0")


@dataclass(frozen=True, slots=True)
class QueryInfo:
    """Read-only summary of one currently active query."""

    pid: int
    database: str | None = None
    username: str | None = None
    query_id: int | None = None
    state: SessionState | None = None
    query_text: str | None = None
    query_started_at: datetime | None = None
    elapsed_ms: float | None = None
    wait_event_type: str | None = None
    wait_event: str | None = None

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("query pid must be > 0")
        if self.elapsed_ms is not None and self.elapsed_ms < 0:
            raise ValueError("query elapsed_ms must be >= 0")


@dataclass(frozen=True, slots=True)
class TransactionInfo:
    """Read-only summary of one open transaction."""

    pid: int
    transaction_started_at: datetime
    elapsed_ms: float
    database: str | None = None
    username: str | None = None
    state: SessionState | None = None
    backend_xid: str | None = None
    backend_xmin: str | None = None
    query_text: str | None = None

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("transaction pid must be > 0")
        if self.elapsed_ms < 0:
            raise ValueError("transaction elapsed_ms must be >= 0")

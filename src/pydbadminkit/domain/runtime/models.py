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


@dataclass(frozen=True, slots=True)
class WaitInfo:
    """Read-only description of one backend currently waiting."""

    pid: int
    wait_event_type: str
    wait_event: str
    database: str | None = None
    username: str | None = None
    state: SessionState | None = None
    state_changed_at: datetime | None = None
    query_text: str | None = None

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("wait pid must be > 0")
        if not self.wait_event_type or self.wait_event_type.isspace():
            raise ValueError("wait_event_type must not be blank")
        if not self.wait_event or self.wait_event.isspace():
            raise ValueError("wait_event must not be blank")


@dataclass(frozen=True, slots=True)
class LockInfo:
    """Read-only description of one backend lock."""

    pid: int
    lock_type: str
    mode: str
    granted: bool
    database: str | None = None
    username: str | None = None
    relation_schema: str | None = None
    relation_name: str | None = None
    transaction_id: str | None = None
    virtual_transaction_id: str | None = None
    virtual_transaction: str | None = None
    page: int | None = None
    tuple_id: int | None = None
    fastpath: bool | None = None

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("lock pid must be > 0")
        if not self.lock_type or self.lock_type.isspace():
            raise ValueError("lock_type must not be blank")
        if not self.mode or self.mode.isspace():
            raise ValueError("lock mode must not be blank")
        if self.page is not None and self.page < 0:
            raise ValueError("lock page must be >= 0")
        if self.tuple_id is not None and self.tuple_id < 0:
            raise ValueError("lock tuple_id must be >= 0")


@dataclass(frozen=True, slots=True)
class BlockingRelation:
    """One edge in a blocking chain rooted at a waiting backend."""

    root_pid: int
    blocked_pid: int
    blocking_pid: int
    depth: int
    database: str | None = None
    blocked_username: str | None = None
    blocking_username: str | None = None
    wait_event_type: str | None = None
    wait_event: str | None = None
    blocked_query_text: str | None = None
    blocking_query_text: str | None = None

    def __post_init__(self) -> None:
        if self.root_pid <= 0:
            raise ValueError("blocking root_pid must be > 0")
        if self.blocked_pid <= 0:
            raise ValueError("blocked_pid must be > 0")
        if self.blocking_pid < 0:
            raise ValueError("blocking_pid must be >= 0")
        if self.depth <= 0:
            raise ValueError("blocking depth must be > 0")

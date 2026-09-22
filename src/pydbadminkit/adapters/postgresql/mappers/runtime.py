"""Map PostgreSQL runtime rows to public domain models."""

from collections.abc import Mapping
from datetime import datetime

from pydbadminkit.domain.runtime import (
    BlockingRelation,
    LockInfo,
    QueryInfo,
    SessionInfo,
    SessionState,
    TransactionInfo,
    WaitInfo,
)
from pydbadminkit.errors import InternalError

_STATE_BY_POSTGRESQL = {
    "active": SessionState.ACTIVE,
    "idle": SessionState.IDLE,
    "idle in transaction": SessionState.IDLE_IN_TRANSACTION,
    "idle in transaction (aborted)": SessionState.IDLE_IN_TRANSACTION_ABORTED,
    "fastpath function call": SessionState.FASTPATH_FUNCTION_CALL,
    "disabled": SessionState.DISABLED,
}


def map_session_info(row: Mapping[str, object]) -> SessionInfo:
    """Map one PostgreSQL pg_stat_activity session row."""

    try:
        return SessionInfo(
            pid=_required_int(row["pid"]),
            database=_optional_str(row.get("database_name")),
            username=_optional_str(row.get("username")),
            application_name=_optional_str(row.get("application_name")),
            client_address=_optional_str(row.get("client_address")),
            backend_type=_optional_str(row.get("backend_type")),
            state=_optional_state(row.get("state")),
            backend_started_at=_optional_datetime(row.get("backend_start")),
            state_changed_at=_optional_datetime(row.get("state_change")),
            wait_event_type=_optional_str(row.get("wait_event_type")),
            wait_event=_optional_str(row.get("wait_event")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL session row mapping failed.") from error


def map_query_info(row: Mapping[str, object]) -> QueryInfo:
    """Map one PostgreSQL active-query row."""

    try:
        return QueryInfo(
            pid=_required_int(row["pid"]),
            database=_optional_str(row.get("database_name")),
            username=_optional_str(row.get("username")),
            query_id=_optional_int(row.get("query_id")),
            state=_optional_state(row.get("state")),
            query_text=_optional_str(row.get("query")),
            query_started_at=_optional_datetime(row.get("query_start")),
            elapsed_ms=_optional_float(row.get("elapsed_ms")),
            wait_event_type=_optional_str(row.get("wait_event_type")),
            wait_event=_optional_str(row.get("wait_event")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL query row mapping failed.") from error


def map_transaction_info(row: Mapping[str, object]) -> TransactionInfo:
    """Map one PostgreSQL open-transaction row."""

    try:
        started_at = _required_datetime(row["xact_start"])
        elapsed_ms = _required_float(row["elapsed_ms"])
        return TransactionInfo(
            pid=_required_int(row["pid"]),
            database=_optional_str(row.get("database_name")),
            username=_optional_str(row.get("username")),
            state=_optional_state(row.get("state")),
            transaction_started_at=started_at,
            elapsed_ms=elapsed_ms,
            backend_xid=_optional_str(row.get("backend_xid")),
            backend_xmin=_optional_str(row.get("backend_xmin")),
            query_text=_optional_str(row.get("query")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL transaction row mapping failed.") from error


def map_wait_info(row: Mapping[str, object]) -> WaitInfo:
    """Map one PostgreSQL wait-event row."""

    try:
        return WaitInfo(
            pid=_required_int(row["pid"]),
            database=_optional_str(row.get("database_name")),
            username=_optional_str(row.get("username")),
            state=_optional_state(row.get("state")),
            state_changed_at=_optional_datetime(row.get("state_change")),
            wait_event_type=_required_str(row["wait_event_type"]),
            wait_event=_required_str(row["wait_event"]),
            query_text=_optional_str(row.get("query")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL wait row mapping failed.") from error


def map_lock_info(row: Mapping[str, object]) -> LockInfo:
    """Map one PostgreSQL pg_locks row."""

    try:
        return LockInfo(
            pid=_required_int(row["pid"]),
            database=_optional_str(row.get("database_name")),
            username=_optional_str(row.get("username")),
            lock_type=_required_str(row["locktype"]),
            mode=_required_str(row["mode"]),
            granted=_required_bool(row["granted"]),
            relation_schema=_optional_str(row.get("relation_schema")),
            relation_name=_optional_str(row.get("relation_name")),
            transaction_id=_optional_str(row.get("transaction_id")),
            virtual_transaction_id=_optional_str(
                row.get("virtual_transaction_id")
            ),
            virtual_transaction=_optional_str(row.get("virtualtransaction")),
            page=_optional_int(row.get("page")),
            tuple_id=_optional_int(row.get("tuple_id")),
            fastpath=_optional_bool(row.get("fastpath")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL lock row mapping failed.") from error


def map_blocking_relation(row: Mapping[str, object]) -> BlockingRelation:
    """Map one edge from a recursive PostgreSQL blocking chain."""

    try:
        return BlockingRelation(
            root_pid=_required_int(row["root_pid"]),
            blocked_pid=_required_int(row["blocked_pid"]),
            blocking_pid=_required_int(row["blocking_pid"]),
            depth=_required_int(row["depth"]),
            database=_optional_str(row.get("database_name")),
            blocked_username=_optional_str(row.get("blocked_username")),
            blocking_username=_optional_str(row.get("blocking_username")),
            wait_event_type=_optional_str(row.get("wait_event_type")),
            wait_event=_optional_str(row.get("wait_event")),
            blocked_query_text=_optional_str(row.get("blocked_query")),
            blocking_query_text=_optional_str(row.get("blocking_query")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL blocking row mapping failed.") from error


def postgresql_state_filter(state: SessionState | None) -> str | None:
    """Translate one normalized state back to PostgreSQL's pg_stat_activity value."""

    if state is None:
        return None
    for raw, normalized in _STATE_BY_POSTGRESQL.items():
        if normalized is state:
            return raw
    return "__pydbadminkit_unknown_state__"


def _optional_state(value: object) -> SessionState | None:
    if value is None:
        return None
    return _STATE_BY_POSTGRESQL.get(str(value), SessionState.UNKNOWN)


def _required_int(value: object) -> int:
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid integer value")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError("expected integer-compatible value")


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _required_int(value)


def _required_float(value: object) -> float:
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid float value")
    if isinstance(value, (int, float, str)):
        return float(value)
    raise TypeError("expected float-compatible value")


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return _required_float(value)


def _required_bool(value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError("boolean value is required")
    return value


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    return _required_bool(value)


def _required_datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("datetime value is required")
    return value


def _optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return _required_datetime(value)


def _required_str(value: object) -> str:
    if not isinstance(value, str) or not value or value.isspace():
        raise TypeError("non-blank string value is required")
    return value


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)

"""Unit tests for PostgreSQL runtime inspection."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.mappers.runtime import (
    map_blocking_relation,
    map_lock_info,
    map_query_info,
    map_session_info,
    map_transaction_info,
    map_wait_info,
)
from pydbadminkit.adapters.postgresql.runtime import PostgreSQLRuntimeAdapter
from pydbadminkit.domain.runtime import SessionState
from pydbadminkit.errors import InternalError

pytestmark = [pytest.mark.unit, pytest.mark.postgresql, pytest.mark.runtime]


class FakeExecutor:
    def __init__(
        self,
        *,
        many_by_id: dict[str, tuple[dict[str, Any], ...]] | None = None,
    ) -> None:
        self.many_by_id = many_by_id or {}
        self.calls: list[tuple[str, tuple[object, ...] | None, str]] = []

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> tuple[dict[str, Any], ...]:
        self.calls.append((query, params, query_id))
        return self.many_by_id.get(query_id, ())


def _session_row() -> dict[str, Any]:
    return {
        "pid": 101,
        "database_name": "analytics",
        "username": "app",
        "application_name": "psql",
        "client_address": "127.0.0.1",
        "backend_type": "client backend",
        "state": "idle in transaction",
        "backend_start": datetime(2026, 9, 22, 15, 0, tzinfo=UTC),
        "state_change": datetime(2026, 9, 22, 15, 30, tzinfo=UTC),
        "wait_event_type": "Client",
        "wait_event": "ClientRead",
    }


def _query_row() -> dict[str, Any]:
    return {
        "pid": 102,
        "database_name": "analytics",
        "username": "app",
        "query_id": 1234,
        "state": "active",
        "query": "SELECT * FROM orders",
        "query_start": datetime(2026, 9, 22, 15, 59, tzinfo=UTC),
        "elapsed_ms": 250.5,
        "wait_event_type": None,
        "wait_event": None,
    }


def _transaction_row() -> dict[str, Any]:
    return {
        "pid": 103,
        "database_name": "analytics",
        "username": "app",
        "state": "idle in transaction",
        "xact_start": datetime(2026, 9, 22, 15, 58, tzinfo=UTC),
        "elapsed_ms": 120000.0,
        "backend_xid": "735",
        "backend_xmin": "734",
        "query": "UPDATE orders SET status = 'paid'",
    }


def _wait_row() -> dict[str, Any]:
    return {
        "pid": 104,
        "database_name": "analytics",
        "username": "app",
        "state": "active",
        "state_change": datetime(2026, 9, 22, 15, 59, tzinfo=UTC),
        "wait_event_type": "Lock",
        "wait_event": "transactionid",
        "query": "UPDATE orders SET status = 'paid'",
    }


def _lock_row() -> dict[str, Any]:
    return {
        "pid": 105,
        "database_name": "analytics",
        "username": "app",
        "locktype": "relation",
        "mode": "RowExclusiveLock",
        "granted": False,
        "fastpath": False,
        "relation_schema": "public",
        "relation_name": "orders",
        "transaction_id": "735",
        "virtual_transaction_id": "4/21",
        "virtualtransaction": "4/21",
        "page": 3,
        "tuple_id": 7,
    }


def _blocking_row() -> dict[str, Any]:
    return {
        "root_pid": 106,
        "blocked_pid": 106,
        "blocking_pid": 107,
        "depth": 1,
        "database_name": "analytics",
        "blocked_username": "app",
        "blocking_username": "worker",
        "wait_event_type": "Lock",
        "wait_event": "transactionid",
        "blocked_query": "UPDATE orders SET status = 'paid'",
        "blocking_query": "UPDATE orders SET status = 'processing'",
    }


def test_runtime_mappers_build_domain_models() -> None:
    session = map_session_info(_session_row())
    query = map_query_info(_query_row())
    transaction = map_transaction_info(_transaction_row())
    wait = map_wait_info(_wait_row())
    lock = map_lock_info(_lock_row())
    blocking = map_blocking_relation(_blocking_row())

    assert session.state is SessionState.IDLE_IN_TRANSACTION
    assert session.wait_event == "ClientRead"
    assert query.query_id == 1234
    assert query.elapsed_ms == 250.5
    assert transaction.backend_xid == "735"
    assert transaction.elapsed_ms == 120000.0
    assert wait.wait_event_type == "Lock"
    assert lock.relation_name == "orders"
    assert lock.granted is False
    assert blocking.blocking_pid == 107
    assert blocking.depth == 1


def test_runtime_mapper_preserves_unknown_postgresql_state() -> None:
    row = _session_row()
    row["state"] = "future state"

    assert map_session_info(row).state is SessionState.UNKNOWN


@pytest.mark.parametrize(
    ("mapper", "row"),
    [
        (map_session_info, {"pid": "not-an-int"}),
        (map_query_info, {"pid": True}),
        (
            map_transaction_info,
            {
                "pid": 1,
                "xact_start": "not-a-datetime",
                "elapsed_ms": 1.0,
            },
        ),
        (
            map_wait_info,
            {
                "pid": 1,
                "wait_event_type": None,
                "wait_event": "ClientRead",
            },
        ),
        (
            map_lock_info,
            {
                "pid": 1,
                "locktype": "relation",
                "mode": "AccessShareLock",
                "granted": "yes",
            },
        ),
        (
            map_blocking_relation,
            {
                "root_pid": 1,
                "blocked_pid": 1,
                "blocking_pid": 2,
                "depth": 0,
            },
        ),
    ],
)
def test_runtime_mappers_reject_invalid_rows(
    mapper: Callable[[dict[str, Any]], object],
    row: dict[str, Any],
) -> None:
    with pytest.raises(InternalError):
        mapper(row)


def test_runtime_adapter_lists_sessions_with_filters() -> None:
    executor = FakeExecutor(many_by_id={"PG_RUNTIME_LIST_SESSIONS": (_session_row(),)})
    adapter = PostgreSQLRuntimeAdapter(executor)  # type: ignore[arg-type]

    sessions = adapter.list_sessions(
        database="analytics",
        username="app",
        state=SessionState.IDLE_IN_TRANSACTION,
    )

    assert sessions[0].pid == 101
    assert executor.calls[0][1] == (
        "analytics",
        "analytics",
        "app",
        "app",
        "idle in transaction",
        "idle in transaction",
        False,
    )


def test_runtime_adapter_lists_queries_and_transactions() -> None:
    executor = FakeExecutor(
        many_by_id={
            "PG_RUNTIME_LIST_QUERIES": (_query_row(),),
            "PG_RUNTIME_LIST_TRANSACTIONS": (_transaction_row(),),
        }
    )
    adapter = PostgreSQLRuntimeAdapter(executor)  # type: ignore[arg-type]

    queries = adapter.list_queries(database="analytics", include_self=True)
    transactions = adapter.list_transactions(database="analytics", include_self=True)

    assert queries[0].query_text == "SELECT * FROM orders"
    assert transactions[0].backend_xmin == "734"
    assert executor.calls[0][2] == "PG_RUNTIME_LIST_QUERIES"
    assert executor.calls[1][2] == "PG_RUNTIME_LIST_TRANSACTIONS"


def test_runtime_adapter_lists_waits_locks_and_blocking() -> None:
    executor = FakeExecutor(
        many_by_id={
            "PG_RUNTIME_LIST_WAITS": (_wait_row(),),
            "PG_RUNTIME_LIST_LOCKS": (_lock_row(),),
            "PG_RUNTIME_LIST_BLOCKING": (_blocking_row(),),
        }
    )
    adapter = PostgreSQLRuntimeAdapter(executor)  # type: ignore[arg-type]

    waits = adapter.list_waits(
        database="analytics",
        username="app",
        wait_event_type="Lock",
    )
    locks = adapter.list_locks(
        database="analytics",
        username="app",
        granted=False,
    )
    blocking = adapter.list_blocking(
        database="analytics",
        username="app",
    )

    assert waits[0].wait_event == "transactionid"
    assert locks[0].mode == "RowExclusiveLock"
    assert blocking[0].root_pid == 106
    assert executor.calls[0][1] == (
        "analytics",
        "analytics",
        "app",
        "app",
        "Lock",
        "Lock",
        False,
    )
    assert executor.calls[1][1] == (
        "analytics",
        "analytics",
        "app",
        "app",
        False,
        False,
        False,
    )
    assert executor.calls[2][1] == (
        "analytics",
        "analytics",
        "app",
        "app",
        False,
    )

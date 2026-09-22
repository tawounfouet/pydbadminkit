"""Unit tests for PostgreSQL runtime inspection."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.mappers.runtime import (
    map_query_info,
    map_session_info,
    map_transaction_info,
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


def test_runtime_mappers_build_domain_models() -> None:
    session = map_session_info(_session_row())
    query = map_query_info(_query_row())
    transaction = map_transaction_info(_transaction_row())

    assert session.state is SessionState.IDLE_IN_TRANSACTION
    assert session.wait_event == "ClientRead"
    assert query.query_id == 1234
    assert query.elapsed_ms == 250.5
    assert transaction.backend_xid == "735"
    assert transaction.elapsed_ms == 120000.0


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

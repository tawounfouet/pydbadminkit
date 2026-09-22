"""Unit tests for PostgreSQL guarded runtime mutations."""

from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.mappers.runtime import map_backend_signal_result
from pydbadminkit.adapters.postgresql.runtime import PostgreSQLRuntimeAdapter
from pydbadminkit.domain.runtime import CancelQueryCommand, TerminateSessionCommand
from pydbadminkit.errors import InternalError

pytestmark = [pytest.mark.unit, pytest.mark.postgresql, pytest.mark.runtime]


class FakeExecutor:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row
        self.calls: list[tuple[tuple[object, ...] | None, str]] = []

    def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> dict[str, Any] | None:
        del query
        self.calls.append((params, query_id))
        return self.row


def _signal_row(*, changed: bool = True) -> dict[str, Any]:
    return {
        "pid": 101,
        "target_exists": True,
        "self_target": False,
        "client_backend": True,
        "changed": changed,
        "backend_type": "client backend",
        "active_query": True,
    }


def test_map_backend_signal_result() -> None:
    result = map_backend_signal_result(_signal_row())

    assert result.pid == 101
    assert result.target_exists is True
    assert result.self_target is False
    assert result.client_backend is True
    assert result.changed is True
    assert result.active_query is True


def test_map_backend_signal_result_rejects_invalid_bool() -> None:
    row = _signal_row()
    row["changed"] = "yes"

    with pytest.raises(InternalError):
        map_backend_signal_result(row)


def test_postgresql_runtime_adapter_cancels_and_terminates() -> None:
    executor = FakeExecutor(_signal_row())
    adapter = PostgreSQLRuntimeAdapter(executor)  # type: ignore[arg-type]

    cancelled = adapter.cancel_query(CancelQueryCommand(pid=101))
    terminated = adapter.terminate_session(TerminateSessionCommand(pid=101))

    assert cancelled.changed is True
    assert terminated.changed is True
    assert executor.calls == [
        ((101,), "PG_RUNTIME_CANCEL_QUERY"),
        ((101,), "PG_RUNTIME_TERMINATE_SESSION"),
    ]


def test_postgresql_runtime_mutation_requires_guard_result() -> None:
    adapter = PostgreSQLRuntimeAdapter(FakeExecutor(None))  # type: ignore[arg-type]

    with pytest.raises(InternalError):
        adapter.cancel_query(CancelQueryCommand(pid=101))

    with pytest.raises(InternalError):
        adapter.terminate_session(TerminateSessionCommand(pid=101))

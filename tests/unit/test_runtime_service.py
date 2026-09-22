"""Unit tests for the runtime application service."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.application.runtime import RuntimeService
from pydbadminkit.domain.runtime import QueryInfo, SessionInfo, SessionState, TransactionInfo

pytestmark = [pytest.mark.unit, pytest.mark.runtime]


class FakeRuntimePort:
    def list_sessions(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        state: SessionState | None = None,
        include_self: bool = False,
    ) -> tuple[SessionInfo, ...]:
        del username, include_self
        return (SessionInfo(pid=101, database=database, state=state),)

    def list_queries(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[QueryInfo, ...]:
        del username, include_self
        return (QueryInfo(pid=102, database=database, state=SessionState.ACTIVE),)

    def list_transactions(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[TransactionInfo, ...]:
        del username, include_self
        return (
            TransactionInfo(
                pid=103,
                database=database,
                transaction_started_at=datetime(2026, 9, 22, tzinfo=UTC),
                elapsed_ms=1.0,
            ),
        )


def test_runtime_service_delegates_read_operations() -> None:
    service = RuntimeService(FakeRuntimePort())

    sessions = service.list_sessions(
        database="analytics",
        state=SessionState.IDLE,
    )
    queries = service.list_queries(database="analytics")
    transactions = service.list_transactions(database="analytics")

    assert sessions[0].database == "analytics"
    assert sessions[0].state is SessionState.IDLE
    assert queries[0].state is SessionState.ACTIVE
    assert transactions[0].pid == 103

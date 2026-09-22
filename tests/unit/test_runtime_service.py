"""Unit tests for the runtime application service."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.application.runtime import RuntimeService
from pydbadminkit.domain.runtime import (
    BlockingRelation,
    LockInfo,
    QueryInfo,
    SessionInfo,
    SessionState,
    TransactionInfo,
    WaitInfo,
)

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

    def list_waits(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        wait_event_type: str | None = None,
        include_self: bool = False,
    ) -> tuple[WaitInfo, ...]:
        del username, include_self
        return (
            WaitInfo(
                pid=104,
                database=database,
                wait_event_type=wait_event_type or "Lock",
                wait_event="transactionid",
            ),
        )

    def list_locks(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        granted: bool | None = None,
        include_self: bool = False,
    ) -> tuple[LockInfo, ...]:
        del username, include_self
        return (
            LockInfo(
                pid=105,
                database=database,
                lock_type="relation",
                mode="AccessShareLock",
                granted=True if granted is None else granted,
            ),
        )

    def list_blocking(
        self,
        *,
        database: str | None = None,
        username: str | None = None,
        include_self: bool = False,
    ) -> tuple[BlockingRelation, ...]:
        del username, include_self
        return (
            BlockingRelation(
                root_pid=106,
                blocked_pid=106,
                blocking_pid=107,
                depth=1,
                database=database,
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
    waits = service.list_waits(database="analytics", wait_event_type="Lock")
    locks = service.list_locks(database="analytics", granted=False)
    blocking = service.list_blocking(database="analytics")

    assert sessions[0].database == "analytics"
    assert sessions[0].state is SessionState.IDLE
    assert queries[0].state is SessionState.ACTIVE
    assert transactions[0].pid == 103
    assert waits[0].wait_event_type == "Lock"
    assert locks[0].granted is False
    assert blocking[0].blocking_pid == 107

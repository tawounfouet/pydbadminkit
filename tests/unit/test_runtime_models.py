"""Unit tests for runtime domain models."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest

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


def test_runtime_models_accept_valid_values() -> None:
    started_at = datetime(2026, 9, 22, 16, 0, tzinfo=UTC)

    session = SessionInfo(pid=101, state=SessionState.ACTIVE)
    query = QueryInfo(pid=102, elapsed_ms=12.5, state=SessionState.ACTIVE)
    transaction = TransactionInfo(
        pid=103,
        transaction_started_at=started_at,
        elapsed_ms=50.0,
        state=SessionState.IDLE_IN_TRANSACTION,
    )
    wait = WaitInfo(
        pid=104,
        wait_event_type="Lock",
        wait_event="transactionid",
    )
    lock = LockInfo(
        pid=105,
        lock_type="relation",
        mode="AccessShareLock",
        granted=True,
    )
    blocking = BlockingRelation(
        root_pid=106,
        blocked_pid=106,
        blocking_pid=107,
        depth=1,
    )

    assert session.pid == 101
    assert query.elapsed_ms == 12.5
    assert transaction.transaction_started_at == started_at
    assert wait.wait_event_type == "Lock"
    assert lock.granted is True
    assert blocking.blocking_pid == 107

    prepared_blocker = BlockingRelation(
        root_pid=108,
        blocked_pid=108,
        blocking_pid=0,
        depth=1,
    )
    assert prepared_blocker.blocking_pid == 0


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: SessionInfo(pid=0), "session pid"),
        (lambda: QueryInfo(pid=-1), "query pid"),
        (lambda: QueryInfo(pid=1, elapsed_ms=-0.1), "query elapsed_ms"),
        (
            lambda: TransactionInfo(
                pid=1,
                transaction_started_at=datetime(2026, 9, 22, tzinfo=UTC),
                elapsed_ms=-1.0,
            ),
            "transaction elapsed_ms",
        ),
        (
            lambda: WaitInfo(pid=1, wait_event_type="", wait_event="ClientRead"),
            "wait_event_type",
        ),
        (
            lambda: LockInfo(
                pid=1,
                lock_type="relation",
                mode="AccessShareLock",
                granted=True,
                page=-1,
            ),
            "lock page",
        ),
        (
            lambda: BlockingRelation(
                root_pid=1,
                blocked_pid=1,
                blocking_pid=2,
                depth=0,
            ),
            "blocking depth",
        ),
    ],
)
def test_runtime_models_reject_invalid_values(
    factory: Callable[[], object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()

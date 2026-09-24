"""Unit tests for the default health checks."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.application.monitoring.checks import (
    ConnectionUsageCheck,
    ConnectivityCheck,
    IdleTransactionCheck,
    LongQueryCheck,
    LongTransactionCheck,
    WaitingLockCheck,
)
from pydbadminkit.domain.common import DatabaseEngine, DatabaseVersion
from pydbadminkit.domain.connection import ConnectionTestResult
from pydbadminkit.domain.monitoring import (
    ConnectionStatistics,
    HealthStatus,
    Threshold,
)
from pydbadminkit.domain.runtime import (
    BlockingRelation,
    LockInfo,
    QueryInfo,
    SessionState,
    TransactionInfo,
)

pytestmark = pytest.mark.unit


class FakeMonitoringService:
    def __init__(self, statistics: ConnectionStatistics) -> None:
        self.statistics = statistics

    def get_connection_statistics(self) -> ConnectionStatistics:
        return self.statistics


class FakeRuntimeService:
    def __init__(
        self,
        *,
        queries: tuple[QueryInfo, ...] = (),
        transactions: tuple[TransactionInfo, ...] = (),
        locks: tuple[LockInfo, ...] = (),
        blocking: tuple[BlockingRelation, ...] = (),
    ) -> None:
        self.queries = queries
        self.transactions = transactions
        self.locks = locks
        self.blocking = blocking

    def list_queries(self) -> tuple[QueryInfo, ...]:
        return self.queries

    def list_transactions(self) -> tuple[TransactionInfo, ...]:
        return self.transactions

    def list_locks(self, *, granted: bool | None = None) -> tuple[LockInfo, ...]:
        if granted is None:
            return self.locks
        return tuple(lock for lock in self.locks if lock.granted is granted)

    def list_blocking(self) -> tuple[BlockingRelation, ...]:
        return self.blocking


def _transaction(
    pid: int,
    elapsed_seconds: float,
    state: SessionState = SessionState.ACTIVE,
) -> TransactionInfo:
    return TransactionInfo(
        pid=pid,
        transaction_started_at=datetime(2026, 9, 24, tzinfo=UTC),
        elapsed_ms=elapsed_seconds * 1000,
        state=state,
    )


def test_connectivity_check_reports_latency_without_secrets() -> None:
    result = ConnectivityCheck(
        lambda: ConnectionTestResult(
            engine=DatabaseEngine.POSTGRESQL,
            version=DatabaseVersion(18),
            current_database="analytics",
            current_user="app",
            latency_ms=12.5,
        )
    ).run()

    assert result.status is HealthStatus.OK
    assert result.details is not None
    assert result.details["latency_ms"] == 12.5
    assert result.evidence[0].observed == 12.5


@pytest.mark.parametrize(
    ("ratio", "expected"),
    [
        (0.79, HealthStatus.OK),
        (0.80, HealthStatus.WARNING),
        (0.94, HealthStatus.WARNING),
        (0.95, HealthStatus.CRITICAL),
    ],
)
def test_connection_usage_threshold_boundaries(
    ratio: float,
    expected: HealthStatus,
) -> None:
    total = int(ratio * 100)
    check = ConnectionUsageCheck(
        FakeMonitoringService(ConnectionStatistics(total, total, 0, 0, 100, ratio)),  # type: ignore[arg-type]
        Threshold(0.80, 0.95),
    )

    result = check.run()

    assert result.status is expected
    assert result.evidence[0].warning_threshold == 0.80


def test_connection_usage_is_unknown_without_capacity() -> None:
    result = ConnectionUsageCheck(
        FakeMonitoringService(ConnectionStatistics(4, 1, 3, 0, None, None)),  # type: ignore[arg-type]
        Threshold(0.80, 0.95),
    ).run()

    assert result.status is HealthStatus.UNKNOWN


@pytest.mark.parametrize(
    ("elapsed", "expected"),
    [
        (29.0, HealthStatus.OK),
        (30.0, HealthStatus.WARNING),
        (299.0, HealthStatus.WARNING),
        (300.0, HealthStatus.CRITICAL),
    ],
)
def test_long_query_threshold_boundaries(elapsed: float, expected: HealthStatus) -> None:
    runtime = FakeRuntimeService(
        queries=(QueryInfo(pid=101, elapsed_ms=elapsed * 1000),)
    )
    result = LongQueryCheck(runtime, Threshold(30, 300)).run()  # type: ignore[arg-type]

    assert result.status is expected
    assert result.details is not None
    assert "query_text" not in result.details


def test_transaction_checks_separate_general_and_idle_findings() -> None:
    runtime = FakeRuntimeService(
        transactions=(
            _transaction(201, 61),
            _transaction(202, 301, SessionState.IDLE_IN_TRANSACTION),
        )
    )

    long_result = LongTransactionCheck(runtime, Threshold(60, 600)).run()  # type: ignore[arg-type]
    idle_result = IdleTransactionCheck(runtime, Threshold(60, 300)).run()  # type: ignore[arg-type]

    assert long_result.status is HealthStatus.WARNING
    assert idle_result.status is HealthStatus.CRITICAL
    assert idle_result.details is not None
    assert idle_result.details["top_pids"] == [202]


def test_waiting_lock_check_counts_distinct_waiting_sessions() -> None:
    runtime = FakeRuntimeService(
        locks=(
            LockInfo(pid=301, lock_type="advisory", mode="ExclusiveLock", granted=False),
        ),
        blocking=(
            BlockingRelation(
                root_pid=301,
                blocked_pid=301,
                blocking_pid=302,
                depth=1,
            ),
        ),
    )

    result = WaitingLockCheck(runtime, Threshold(1, 10)).run()  # type: ignore[arg-type]

    assert result.status is HealthStatus.WARNING
    assert result.details is not None
    assert result.details["waiting_sessions"] == 1
    assert result.details["root_blockers"] == 1

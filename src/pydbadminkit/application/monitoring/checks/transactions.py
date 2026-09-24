"""Transaction duration health checks."""

from datetime import UTC, datetime

from pydbadminkit.application.runtime import RuntimeService
from pydbadminkit.domain.monitoring import (
    HealthCheckCategory,
    HealthCheckEvidence,
    HealthCheckResult,
    Threshold,
)
from pydbadminkit.domain.runtime import SessionState

from .base import status_for_threshold


class LongTransactionCheck:
    """Evaluate durations of all visible open transactions."""

    name = "long_transactions"
    category = HealthCheckCategory.TRANSACTIONS

    def __init__(self, service: RuntimeService, threshold: Threshold) -> None:
        self._service = service
        self._threshold = threshold

    def run(self) -> HealthCheckResult:
        transactions = self._service.list_transactions()
        durations = [(item.pid, item.elapsed_ms / 1000.0) for item in transactions]
        oldest = max((duration for _, duration in durations), default=0.0)
        warning = self._threshold.warning
        affected = [
            (pid, duration)
            for pid, duration in durations
            if warning is not None and duration >= warning
        ]
        status = status_for_threshold(oldest, self._threshold)
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=(
                "no long-running transactions"
                if not affected
                else f"{len(affected)} long-running transaction"
                f"{'' if len(affected) == 1 else 's'}"
            ),
            details={
                "count": len(affected),
                "oldest_duration_seconds": oldest,
                "top_pids": [pid for pid, _ in sorted(affected, key=lambda item: item[1], reverse=True)[:5]],
            },
            captured_at=datetime.now(UTC),
            evidence=(
                HealthCheckEvidence(
                    metric="transactions.oldest_duration_seconds",
                    observed=oldest,
                    warning_threshold=self._threshold.warning,
                    critical_threshold=self._threshold.critical,
                ),
            ),
        )


class IdleTransactionCheck:
    """Evaluate transactions whose sessions are idle in transaction."""

    name = "idle_transactions"
    category = HealthCheckCategory.TRANSACTIONS

    def __init__(self, service: RuntimeService, threshold: Threshold) -> None:
        self._service = service
        self._threshold = threshold

    def run(self) -> HealthCheckResult:
        idle_states = {
            SessionState.IDLE_IN_TRANSACTION,
            SessionState.IDLE_IN_TRANSACTION_ABORTED,
        }
        transactions = [
            item for item in self._service.list_transactions() if item.state in idle_states
        ]
        durations = [(item.pid, item.elapsed_ms / 1000.0) for item in transactions]
        oldest = max((duration for _, duration in durations), default=0.0)
        warning = self._threshold.warning
        affected = [
            (pid, duration)
            for pid, duration in durations
            if warning is not None and duration >= warning
        ]
        status = status_for_threshold(oldest, self._threshold)
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=(
                "no long idle transactions"
                if not affected
                else f"{len(affected)} long idle transaction"
                f"{'' if len(affected) == 1 else 's'}"
            ),
            details={
                "count": len(affected),
                "oldest_duration_seconds": oldest,
                "top_pids": [pid for pid, _ in sorted(affected, key=lambda item: item[1], reverse=True)[:5]],
            },
            captured_at=datetime.now(UTC),
            evidence=(
                HealthCheckEvidence(
                    metric="transactions.idle_oldest_duration_seconds",
                    observed=oldest,
                    warning_threshold=self._threshold.warning,
                    critical_threshold=self._threshold.critical,
                ),
            ),
        )

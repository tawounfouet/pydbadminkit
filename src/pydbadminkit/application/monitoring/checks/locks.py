"""Waiting-lock health check."""

from datetime import UTC, datetime

from pydbadminkit.application.runtime import RuntimeService
from pydbadminkit.domain.monitoring import (
    HealthCheckCategory,
    HealthCheckEvidence,
    HealthCheckResult,
    Threshold,
)

from .base import status_for_threshold


class WaitingLockCheck:
    """Evaluate visible waiting locks and blocking relationships."""

    name = "waiting_locks"
    category = HealthCheckCategory.LOCKS

    def __init__(self, service: RuntimeService, threshold: Threshold) -> None:
        self._service = service
        self._threshold = threshold

    def run(self) -> HealthCheckResult:
        locks = self._service.list_locks(granted=False)
        blocking = self._service.list_blocking()
        waiting_pids = {lock.pid for lock in locks}
        blocked_pids = {relation.blocked_pid for relation in blocking}
        root_blockers = {
            relation.blocking_pid for relation in blocking if relation.blocking_pid > 0
        }
        waiting_sessions = len(waiting_pids | blocked_pids)
        status = status_for_threshold(waiting_sessions, self._threshold)
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=(
                "no waiting lock sessions"
                if waiting_sessions == 0
                else f"{waiting_sessions} session"
                f"{'' if waiting_sessions == 1 else 's'} waiting on locks"
            ),
            details={
                "waiting_locks": len(locks),
                "waiting_sessions": waiting_sessions,
                "blocked_sessions": len(blocked_pids),
                "root_blockers": len(root_blockers),
            },
            captured_at=datetime.now(UTC),
            evidence=(
                HealthCheckEvidence(
                    metric="locks.waiting_sessions",
                    observed=waiting_sessions,
                    warning_threshold=self._threshold.warning,
                    critical_threshold=self._threshold.critical,
                ),
            ),
        )

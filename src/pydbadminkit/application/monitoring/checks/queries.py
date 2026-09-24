"""Long-running query health check."""

from datetime import UTC, datetime

from pydbadminkit.application.runtime import RuntimeService
from pydbadminkit.domain.monitoring import (
    HealthCheckCategory,
    HealthCheckEvidence,
    HealthCheckResult,
    Threshold,
)

from .base import status_for_threshold


class LongQueryCheck:
    """Evaluate active-query durations without exposing SQL text."""

    name = "long_queries"
    category = HealthCheckCategory.QUERIES

    def __init__(self, service: RuntimeService, threshold: Threshold) -> None:
        self._service = service
        self._threshold = threshold

    def run(self) -> HealthCheckResult:
        queries = self._service.list_queries()
        durations = [
            (query.pid, query.elapsed_ms / 1000.0)
            for query in queries
            if query.elapsed_ms is not None
        ]
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
                "no long-running queries"
                if not affected
                else f"{len(affected)} long-running quer{'y' if len(affected) == 1 else 'ies'}"
            ),
            details={
                "count": len(affected),
                "oldest_duration_seconds": oldest,
                "top_pids": [pid for pid, _ in sorted(affected, key=lambda item: item[1], reverse=True)[:5]],
            },
            captured_at=datetime.now(UTC),
            evidence=(
                HealthCheckEvidence(
                    metric="queries.oldest_duration_seconds",
                    observed=oldest,
                    warning_threshold=self._threshold.warning,
                    critical_threshold=self._threshold.critical,
                ),
            ),
        )

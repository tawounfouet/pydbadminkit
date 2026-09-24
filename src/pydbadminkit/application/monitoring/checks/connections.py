"""Connection utilization health check."""

from datetime import UTC, datetime

from pydbadminkit.application.monitoring.service import MonitoringService
from pydbadminkit.domain.monitoring import (
    HealthCheckCategory,
    HealthCheckEvidence,
    HealthCheckResult,
    HealthStatus,
    Threshold,
)

from .base import status_for_threshold


class ConnectionUsageCheck:
    """Evaluate current connection utilization."""

    name = "connection_usage"
    category = HealthCheckCategory.CONNECTIONS

    def __init__(self, service: MonitoringService, threshold: Threshold) -> None:
        self._service = service
        self._threshold = threshold

    def run(self) -> HealthCheckResult:
        statistics = self._service.get_connection_statistics()
        ratio = statistics.utilization_ratio
        captured_at = datetime.now(UTC)

        if ratio is None:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNKNOWN,
                message="connection utilization is unavailable",
                details={
                    "total": statistics.total,
                    "max_connections": statistics.max_connections,
                    "utilization_ratio": None,
                },
                captured_at=captured_at,
                evidence=(
                    HealthCheckEvidence(
                        metric="connections.utilization_ratio",
                        observed=None,
                        warning_threshold=self._threshold.warning,
                        critical_threshold=self._threshold.critical,
                    ),
                ),
            )

        status = status_for_threshold(ratio, self._threshold)
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=(
                f"{statistics.total} of {statistics.max_connections} connections are in use "
                f"({ratio:.1%})"
            ),
            details={
                "total": statistics.total,
                "active": statistics.active,
                "idle": statistics.idle,
                "idle_in_transaction": statistics.idle_in_transaction,
                "max_connections": statistics.max_connections,
                "utilization_ratio": ratio,
            },
            captured_at=captured_at,
            evidence=(
                HealthCheckEvidence(
                    metric="connections.utilization_ratio",
                    observed=ratio,
                    warning_threshold=self._threshold.warning,
                    critical_threshold=self._threshold.critical,
                ),
            ),
        )

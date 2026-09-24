"""Connectivity health check."""

from collections.abc import Callable
from datetime import UTC, datetime

from pydbadminkit.domain.connection import ConnectionTestResult
from pydbadminkit.domain.monitoring import (
    HealthCheckCategory,
    HealthCheckEvidence,
    HealthCheckResult,
    HealthStatus,
)


class ConnectivityCheck:
    """Verify that the configured database server responds."""

    name = "connectivity"
    category = HealthCheckCategory.CONNECTIVITY

    def __init__(self, probe: Callable[[], ConnectionTestResult]) -> None:
        self._probe = probe

    def run(self) -> HealthCheckResult:
        result = self._probe()
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.OK,
            message=f"server responded in {result.latency_ms:.2f} ms",
            details={
                "engine": result.engine.value,
                "version": str(result.version),
                "database": result.current_database,
                "latency_ms": result.latency_ms,
            },
            captured_at=datetime.now(UTC),
            evidence=(
                HealthCheckEvidence(
                    metric="connectivity.latency_ms",
                    observed=result.latency_ms,
                ),
            ),
        )

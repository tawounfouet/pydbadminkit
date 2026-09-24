"""Shared health-check helpers."""

from typing import Protocol

from pydbadminkit.domain.monitoring import (
    HealthCheckCategory,
    HealthCheckResult,
    HealthStatus,
    Threshold,
)


class HealthCheck(Protocol):
    """One isolated point-in-time health check."""

    name: str
    category: HealthCheckCategory

    def run(self) -> HealthCheckResult:
        """Execute the check."""
        ...


def status_for_threshold(value: int | float, threshold: Threshold) -> HealthStatus:
    """Classify a value where higher values are less healthy."""

    if threshold.critical is not None and value >= threshold.critical:
        return HealthStatus.CRITICAL
    if threshold.warning is not None and value >= threshold.warning:
        return HealthStatus.WARNING
    return HealthStatus.OK

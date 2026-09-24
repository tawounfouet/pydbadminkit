"""Monitoring health models."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from pydbadminkit.domain.monitoring.enums import HealthStatus


@dataclass(frozen=True, slots=True)
class HealthCheckEvidence:
    """Observed value and thresholds supporting one health result."""

    metric: str
    observed: object
    warning_threshold: object | None = None
    critical_threshold: object | None = None

    def __post_init__(self) -> None:
        if not self.metric or self.metric.isspace():
            raise ValueError("health evidence metric must not be blank")


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    """Result of one independent point-in-time health check."""

    name: str
    status: HealthStatus
    message: str
    details: Mapping[str, object] | None = None
    captured_at: datetime | None = None
    evidence: tuple[HealthCheckEvidence, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("health check name must not be blank")
        if not self.message or self.message.isspace():
            raise ValueError("health check message must not be blank")
        if self.captured_at is not None and (
            self.captured_at.tzinfo is None or self.captured_at.utcoffset() is None
        ):
            raise ValueError("health check captured_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class HealthReport:
    """Aggregated health-check report."""

    overall_status: HealthStatus
    checks: tuple[HealthCheckResult, ...]
    captured_at: datetime

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None or self.captured_at.utcoffset() is None:
            raise ValueError("health report captured_at must be timezone-aware")

    @classmethod
    def from_checks(
        cls,
        checks: tuple[HealthCheckResult, ...],
        *,
        captured_at: datetime,
    ) -> "HealthReport":
        """Aggregate check statuses using the stable monitoring precedence."""

        if any(check.status is HealthStatus.CRITICAL for check in checks):
            overall = HealthStatus.CRITICAL
        elif any(check.status is HealthStatus.WARNING for check in checks):
            overall = HealthStatus.WARNING
        elif not checks or all(check.status is HealthStatus.UNKNOWN for check in checks):
            overall = HealthStatus.UNKNOWN
        else:
            overall = HealthStatus.OK
        return cls(overall_status=overall, checks=checks, captured_at=captured_at)

"""Health-check runner."""

from datetime import UTC, datetime

from pydbadminkit.application.monitoring.checks import HealthCheck
from pydbadminkit.domain.monitoring import (
    HealthCheckResult,
    HealthReport,
    HealthStatus,
)
from pydbadminkit.errors import PyDBAdminError


class HealthCheckRunner:
    """Run independent health checks and isolate check-specific failures."""

    def __init__(self, checks: tuple[HealthCheck, ...]) -> None:
        self._checks = checks

    def run(self) -> HealthReport:
        results = tuple(self._run_check(check) for check in self._checks)
        return HealthReport.from_checks(results, captured_at=datetime.now(UTC))

    @staticmethod
    def _run_check(check: HealthCheck) -> HealthCheckResult:
        try:
            return check.run()
        except PyDBAdminError as error:
            status = (
                HealthStatus.CRITICAL
                if check.name == "connectivity"
                else HealthStatus.UNKNOWN
            )
            return HealthCheckResult(
                name=check.name,
                status=status,
                message=str(error),
                details={"error_type": type(error).__name__},
                captured_at=datetime.now(UTC),
            )

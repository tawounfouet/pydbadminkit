"""Default health-suite composition."""

from collections.abc import Callable

from pydbadminkit.application.monitoring.checks import (
    ConnectionUsageCheck,
    ConnectivityCheck,
    IdleTransactionCheck,
    LongQueryCheck,
    LongTransactionCheck,
    WaitingLockCheck,
)
from pydbadminkit.application.monitoring.config import HealthCheckConfig
from pydbadminkit.application.monitoring.runner import HealthCheckRunner
from pydbadminkit.application.monitoring.service import MonitoringService
from pydbadminkit.application.runtime import RuntimeService
from pydbadminkit.domain.connection import ConnectionTestResult
from pydbadminkit.domain.monitoring import HealthReport


class HealthService:
    """Application facade for the default on-demand health suite."""

    def __init__(
        self,
        connectivity_probe: Callable[[], ConnectionTestResult],
        monitoring_service: MonitoringService,
        runtime_service: RuntimeService,
        config: HealthCheckConfig | None = None,
    ) -> None:
        self._config = config or HealthCheckConfig()
        self._runner = HealthCheckRunner(
            (
                ConnectivityCheck(connectivity_probe),
                ConnectionUsageCheck(
                    monitoring_service,
                    self._config.connection_usage,
                ),
                LongQueryCheck(runtime_service, self._config.long_queries_seconds),
                LongTransactionCheck(
                    runtime_service,
                    self._config.long_transactions_seconds,
                ),
                IdleTransactionCheck(
                    runtime_service,
                    self._config.idle_transactions_seconds,
                ),
                WaitingLockCheck(runtime_service, self._config.waiting_locks),
            )
        )

    def check(self) -> HealthReport:
        """Run the default health suite."""

        return self._runner.run()

"""Monitoring snapshot composition."""

from datetime import UTC, datetime

from pydbadminkit.application.monitoring.health import HealthService
from pydbadminkit.application.monitoring.service import MonitoringService
from pydbadminkit.domain.monitoring import MonitoringSnapshot


class MonitoringSnapshotService:
    """Compose raw metrics and health into one point-in-time DTO."""

    def __init__(
        self,
        monitoring_service: MonitoringService,
        health_service: HealthService,
    ) -> None:
        self._monitoring_service = monitoring_service
        self._health_service = health_service

    def capture(self) -> MonitoringSnapshot:
        """Capture metrics and health without claiming atomic database consistency."""

        metrics = self._monitoring_service.collect_metrics()
        health_report = self._health_service.check()
        return MonitoringSnapshot(
            metrics=metrics,
            health_report=health_report,
            captured_at=datetime.now(UTC),
        )

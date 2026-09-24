"""Exporter-facing monitoring application services."""

from pydbadminkit.domain.monitoring import Metric, MetricCardinalityPolicy, MonitoringSnapshot
from pydbadminkit.ports.metric_exporter import MetricExporterPort


class MetricExportService:
    """Validate low-cardinality metrics before delegating to an exporter."""

    def __init__(
        self,
        exporter: MetricExporterPort,
        policy: MetricCardinalityPolicy | None = None,
    ) -> None:
        self._exporter = exporter
        self._policy = policy or MetricCardinalityPolicy()

    def export(self, metrics: tuple[Metric, ...]) -> None:
        """Validate and export one metric batch."""

        for metric in metrics:
            self._policy.validate(metric)
        self._exporter.export(metrics)

    def export_snapshot(self, snapshot: MonitoringSnapshot) -> None:
        """Export the metric portion of a monitoring snapshot."""

        self.export(snapshot.metrics)

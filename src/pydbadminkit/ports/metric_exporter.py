"""Metric exporter port."""

from typing import Protocol

from pydbadminkit.domain.monitoring import Metric


class MetricExporterPort(Protocol):
    """External boundary for exporting already-collected metrics."""

    def export(self, metrics: tuple[Metric, ...]) -> None:
        """Export one point-in-time metric batch."""
        ...

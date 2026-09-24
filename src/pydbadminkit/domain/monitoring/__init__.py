"""Monitoring and observability domain models."""

from pydbadminkit.domain.monitoring.cardinality import (
    DEFAULT_EXPORT_LABELS,
    FORBIDDEN_EXPORT_LABELS,
    MetricCardinalityPolicy,
)
from pydbadminkit.domain.monitoring.descriptor import MetricDescriptor
from pydbadminkit.domain.monitoring.enums import (
    HealthCheckCategory,
    HealthStatus,
    MetricType,
)
from pydbadminkit.domain.monitoring.health import (
    HealthCheckEvidence,
    HealthCheckResult,
    HealthReport,
)
from pydbadminkit.domain.monitoring.metric import Metric
from pydbadminkit.domain.monitoring.naming import (
    INTERNAL_METRIC_PREFIX,
    PROMETHEUS_METRIC_PREFIX,
    internal_metric_name,
    prometheus_metric_name,
    validate_metric_name,
)
from pydbadminkit.domain.monitoring.registry import (
    CORE_METRIC_DESCRIPTORS,
    CORE_METRIC_REGISTRY,
)
from pydbadminkit.domain.monitoring.snapshot import MonitoringSnapshot
from pydbadminkit.domain.monitoring.statistics import (
    ConnectionStatistics,
    DatabaseSizeMetric,
    IndexStatistics,
    TableSizeMetric,
    TableStatistics,
)
from pydbadminkit.domain.monitoring.thresholds import Threshold

__all__ = [
    "CORE_METRIC_DESCRIPTORS",
    "CORE_METRIC_REGISTRY",
    "DEFAULT_EXPORT_LABELS",
    "FORBIDDEN_EXPORT_LABELS",
    "ConnectionStatistics",
    "DatabaseSizeMetric",
    "HealthCheckCategory",
    "HealthCheckEvidence",
    "HealthCheckResult",
    "HealthReport",
    "HealthStatus",
    "INTERNAL_METRIC_PREFIX",
    "IndexStatistics",
    "Metric",
    "MetricCardinalityPolicy",
    "MetricDescriptor",
    "MetricType",
    "MonitoringSnapshot",
    "PROMETHEUS_METRIC_PREFIX",
    "TableSizeMetric",
    "TableStatistics",
    "Threshold",
    "internal_metric_name",
    "prometheus_metric_name",
    "validate_metric_name",
]

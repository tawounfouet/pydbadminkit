"""Core metric descriptors."""

from pydbadminkit.domain.monitoring.descriptor import MetricDescriptor
from pydbadminkit.domain.monitoring.enums import MetricType

CORE_METRIC_DESCRIPTORS = (
    MetricDescriptor(
        name="connections.total",
        unit="count",
        metric_type=MetricType.GAUGE,
        description="Current visible PostgreSQL connections.",
    ),
    MetricDescriptor(
        name="connections.active",
        unit="count",
        metric_type=MetricType.GAUGE,
        description="Current active PostgreSQL connections.",
    ),
    MetricDescriptor(
        name="connections.idle",
        unit="count",
        metric_type=MetricType.GAUGE,
        description="Current idle PostgreSQL connections.",
    ),
    MetricDescriptor(
        name="connections.idle_in_transaction",
        unit="count",
        metric_type=MetricType.GAUGE,
        description="Current PostgreSQL connections idle in transaction.",
    ),
    MetricDescriptor(
        name="connections.utilization_ratio",
        unit="ratio",
        metric_type=MetricType.GAUGE,
        description="Current connection utilization divided by max_connections.",
    ),
    MetricDescriptor(
        name="database.size_bytes",
        unit="bytes",
        metric_type=MetricType.GAUGE,
        description="Current logical database size in bytes.",
        label_names=("database",),
    ),
)

CORE_METRIC_REGISTRY = {descriptor.name: descriptor for descriptor in CORE_METRIC_DESCRIPTORS}

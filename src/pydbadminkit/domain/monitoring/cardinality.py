"""Exporter label-cardinality policy."""

from dataclasses import dataclass, field

from pydbadminkit.domain.monitoring.metric import Metric

DEFAULT_EXPORT_LABELS = frozenset({"profile", "environment", "database", "status"})
FORBIDDEN_EXPORT_LABELS = frozenset(
    {
        "pid",
        "query",
        "query_text",
        "client_address",
        "client_ip",
    }
)


@dataclass(frozen=True, slots=True)
class MetricCardinalityPolicy:
    """Validate metric labels before they cross an exporter boundary."""

    allowed_labels: frozenset[str] = field(default_factory=lambda: DEFAULT_EXPORT_LABELS)
    forbidden_labels: frozenset[str] = field(default_factory=lambda: FORBIDDEN_EXPORT_LABELS)
    max_labels: int = 4

    def __post_init__(self) -> None:
        if self.max_labels < 0:
            raise ValueError("max_labels must be greater than or equal to zero")
        overlap = self.allowed_labels & self.forbidden_labels
        if overlap:
            raise ValueError(
                f"allowed and forbidden labels overlap: {', '.join(sorted(overlap))}"
            )

    def validate(self, metric: Metric) -> None:
        """Reject labels that would make the default exporter surface unsafe."""

        labels = set(metric.labels)
        forbidden = labels & self.forbidden_labels
        if forbidden:
            raise ValueError(
                f"metric {metric.name!r} contains forbidden exporter labels: "
                f"{', '.join(sorted(forbidden))}"
            )
        unsupported = labels - self.allowed_labels
        if unsupported:
            raise ValueError(
                f"metric {metric.name!r} contains unsupported exporter labels: "
                f"{', '.join(sorted(unsupported))}"
            )
        if len(labels) > self.max_labels:
            raise ValueError(
                f"metric {metric.name!r} exceeds the exporter label limit "
                f"({len(labels)} > {self.max_labels})"
            )

"""Metric descriptor model."""

from dataclasses import dataclass

from pydbadminkit.domain.monitoring.enums import MetricType
from pydbadminkit.domain.monitoring.naming import validate_metric_name


@dataclass(frozen=True, slots=True)
class MetricDescriptor:
    """Stable metadata describing one metric family."""

    name: str
    unit: str | None
    metric_type: MetricType
    description: str
    label_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_metric_name(self.name)
        if self.unit is not None and (not self.unit or self.unit.isspace()):
            raise ValueError("metric descriptor unit must not be blank")
        if not self.description or self.description.isspace():
            raise ValueError("metric descriptor description must not be blank")
        if len(set(self.label_names)) != len(self.label_names):
            raise ValueError("metric descriptor label names must be unique")
        if any(not label or label.isspace() for label in self.label_names):
            raise ValueError("metric descriptor label names must not be blank")

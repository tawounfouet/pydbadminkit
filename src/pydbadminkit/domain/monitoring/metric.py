"""Monitoring metric model."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from pydbadminkit.domain.monitoring.naming import validate_metric_name


@dataclass(frozen=True, slots=True)
class Metric:
    """One point-in-time observable fact."""

    name: str
    value: int | float | str | bool | None
    unit: str | None
    labels: Mapping[str, str]
    captured_at: datetime

    def __post_init__(self) -> None:
        validate_metric_name(self.name)
        if self.unit is not None and (not self.unit or self.unit.isspace()):
            raise ValueError("metric unit must not be blank")
        if self.captured_at.tzinfo is None or self.captured_at.utcoffset() is None:
            raise ValueError("metric captured_at must be timezone-aware")
        if any(not key or key.isspace() for key in self.labels):
            raise ValueError("metric label names must not be blank")

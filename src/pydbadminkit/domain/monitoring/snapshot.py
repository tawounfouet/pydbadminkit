"""Point-in-time monitoring snapshot."""

from dataclasses import dataclass
from datetime import datetime

from pydbadminkit.domain.monitoring.health import HealthReport
from pydbadminkit.domain.monitoring.metric import Metric


@dataclass(frozen=True, slots=True)
class MonitoringSnapshot:
    """One non-atomic execution-window snapshot for external consumption."""

    metrics: tuple[Metric, ...]
    health_report: HealthReport
    captured_at: datetime

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None or self.captured_at.utcoffset() is None:
            raise ValueError("monitoring snapshot captured_at must be timezone-aware")

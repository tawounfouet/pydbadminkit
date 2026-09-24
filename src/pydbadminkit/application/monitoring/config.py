"""Health-check configuration."""

from dataclasses import dataclass, field

from pydbadminkit.domain.monitoring import Threshold


@dataclass(frozen=True, slots=True)
class HealthCheckConfig:
    """Thresholds for the default on-demand health suite."""

    connection_usage: Threshold = field(default_factory=lambda: Threshold(0.80, 0.95))
    long_queries_seconds: Threshold = field(default_factory=lambda: Threshold(30.0, 300.0))
    long_transactions_seconds: Threshold = field(
        default_factory=lambda: Threshold(60.0, 600.0)
    )
    idle_transactions_seconds: Threshold = field(
        default_factory=lambda: Threshold(60.0, 300.0)
    )
    waiting_locks: Threshold = field(default_factory=lambda: Threshold(1, 10))

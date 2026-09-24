"""Monitoring threshold models."""

from dataclasses import dataclass


def _validate_value(value: int | float | None, field: str) -> None:
    if isinstance(value, bool):
        raise TypeError(f"{field} must be numeric")
    if value is not None and value < 0:
        raise ValueError(f"{field} must be >= 0")


@dataclass(frozen=True, slots=True)
class Threshold:
    """Warning and critical thresholds for metrics where higher is worse."""

    warning: int | float | None = None
    critical: int | float | None = None

    def __post_init__(self) -> None:
        _validate_value(self.warning, "warning")
        _validate_value(self.critical, "critical")
        if (
            self.warning is not None
            and self.critical is not None
            and self.warning >= self.critical
        ):
            raise ValueError("warning threshold must be lower than critical threshold")

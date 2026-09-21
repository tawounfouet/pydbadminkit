"""Connection timeout primitives."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimeoutConfig:
    """Timeouts used while opening and operating a connection."""

    connect_seconds: int = 10
    statement_ms: int | None = None
    lock_ms: int | None = None

    def __post_init__(self) -> None:
        if self.connect_seconds <= 0:
            raise ValueError("connect_seconds must be > 0")
        if self.statement_ms is not None and self.statement_ms <= 0:
            raise ValueError("statement_ms must be > 0")
        if self.lock_ms is not None and self.lock_ms <= 0:
            raise ValueError("lock_ms must be > 0")

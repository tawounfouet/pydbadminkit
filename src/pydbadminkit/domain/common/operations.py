"""Operation status and risk primitives."""

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Mapping


class RiskLevel(IntEnum):
    """Comparable operational risk levels."""

    LOW = 10
    MEDIUM = 20
    HIGH = 30
    CRITICAL = 40

    @property
    def label(self) -> str:
        """Return the stable lowercase machine label."""

        return self.name.lower()


class OperationStatus(StrEnum):
    """Lifecycle/result states shared by administrative operations."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class OperationResult:
    """Generic immutable operation result."""

    operation: str
    status: OperationStatus
    changed: bool | None = None
    message: str | None = None
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not self.operation or self.operation.isspace():
            raise ValueError("operation must not be blank")

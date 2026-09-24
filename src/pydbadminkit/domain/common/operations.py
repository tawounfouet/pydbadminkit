"""Operation status and risk primitives."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum, StrEnum


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


class OperationName(StrEnum):
    """Stable machine names for guarded administrative mutations."""

    BACKUP_CREATE = "backup.create"
    BACKUP_RESTORE = "backup.restore"
    MAINTENANCE_ANALYZE = "maintenance.analyze"
    MAINTENANCE_REINDEX = "maintenance.reindex"
    MAINTENANCE_VACUUM = "maintenance.vacuum"
    RUNTIME_QUERY_CANCEL = "runtime.query.cancel"
    RUNTIME_SESSION_TERMINATE = "runtime.session.terminate"
    SECURITY_ACCESS_GRANT = "security.access.grant"
    SECURITY_ACCESS_REVOKE = "security.access.revoke"
    SECURITY_MEMBERSHIP_ADD = "security.membership.add"
    SECURITY_MEMBERSHIP_REMOVE = "security.membership.remove"
    SECURITY_ROLE_ALTER = "security.role.alter"
    SECURITY_ROLE_CREATE = "security.role.create"
    SECURITY_ROLE_DROP = "security.role.drop"


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

"""Audit event model."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from pydbadminkit.domain.common import EnvironmentName, OperationStatus, RiskLevel


class AuditEventType(StrEnum):
    """Security audit lifecycle event types."""

    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Secret-safe administrative audit event."""

    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    actor: str
    profile: str
    environment: EnvironmentName
    database: str
    operation: str
    target: str
    risk: RiskLevel
    status: OperationStatus
    correlation_id: str
    message: str | None = None

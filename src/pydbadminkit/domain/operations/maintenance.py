"""Maintenance domain models."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from pydbadminkit.domain.common import OperationStatus, QualifiedName


class MaintenanceOperationType(StrEnum):
    """Supported PostgreSQL maintenance operations."""

    VACUUM = "vacuum"
    ANALYZE = "analyze"
    REINDEX = "reindex"


class ReindexTargetType(StrEnum):
    """Supported REINDEX target scopes for the MVP."""

    INDEX = "index"
    TABLE = "table"


@dataclass(frozen=True, slots=True)
class VacuumCommand:
    """Request PostgreSQL VACUUM maintenance."""

    table: QualifiedName | None = None
    full: bool = False
    freeze: bool = False
    analyze: bool = False
    statement_timeout_seconds: float | None = None
    lock_timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        _validate_timeouts(
            self.statement_timeout_seconds,
            self.lock_timeout_seconds,
        )


@dataclass(frozen=True, slots=True)
class AnalyzeCommand:
    """Request PostgreSQL ANALYZE maintenance."""

    table: QualifiedName | None = None
    columns: tuple[str, ...] = ()
    statement_timeout_seconds: float | None = None
    lock_timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.columns and self.table is None:
            raise ValueError("ANALYZE columns require a table target")
        if any(not column or column.isspace() for column in self.columns):
            raise ValueError("ANALYZE column names must not be blank")
        _validate_timeouts(
            self.statement_timeout_seconds,
            self.lock_timeout_seconds,
        )


@dataclass(frozen=True, slots=True)
class ReindexCommand:
    """Request PostgreSQL REINDEX maintenance."""

    target_type: ReindexTargetType
    target: QualifiedName
    concurrently: bool = False
    statement_timeout_seconds: float | None = None
    lock_timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        _validate_timeouts(
            self.statement_timeout_seconds,
            self.lock_timeout_seconds,
        )


@dataclass(frozen=True, slots=True)
class MaintenanceOperation:
    """Completed PostgreSQL maintenance execution."""

    operation_type: MaintenanceOperationType
    target: QualifiedName | None
    started_at: datetime
    finished_at: datetime | None
    status: OperationStatus
    duration_ms: int
    message: str | None = None

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("maintenance duration_ms must be >= 0")


@dataclass(frozen=True, slots=True)
class MaintenanceProgress:
    """Best-effort progress view for one PostgreSQL maintenance backend."""

    operation_type: MaintenanceOperationType
    pid: int
    target: QualifiedName | None
    phase: str | None
    completed: int | None
    total: int | None
    percent: float | None

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("maintenance progress pid must be > 0")
        if self.completed is not None and self.completed < 0:
            raise ValueError("maintenance progress completed must be >= 0")
        if self.total is not None and self.total < 0:
            raise ValueError("maintenance progress total must be >= 0")
        if self.percent is not None and not 0 <= self.percent <= 100:
            raise ValueError("maintenance progress percent must be between 0 and 100")


def _validate_timeouts(
    statement_timeout_seconds: float | None,
    lock_timeout_seconds: float | None,
) -> None:
    if statement_timeout_seconds is not None and statement_timeout_seconds <= 0:
        raise ValueError("statement_timeout_seconds must be > 0")
    if lock_timeout_seconds is not None and lock_timeout_seconds <= 0:
        raise ValueError("lock_timeout_seconds must be > 0")

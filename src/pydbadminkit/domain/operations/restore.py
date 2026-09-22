"""Restore domain models."""

from dataclasses import dataclass
from datetime import datetime

from pydbadminkit.domain.common import OperationStatus
from pydbadminkit.domain.operations.backup import Backup, BackupFormat


@dataclass(frozen=True, slots=True)
class RestoreBackupCommand:
    """Request restoration of one logical backup."""

    backup_path: str
    target_database: str
    clean: bool = False
    create: bool = False
    jobs: int | None = None
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        if not self.backup_path or self.backup_path.isspace():
            raise ValueError("restore backup_path must not be blank")
        if not self.target_database or self.target_database.isspace():
            raise ValueError("restore target_database must not be blank")
        if self.clean and self.create:
            raise ValueError("restore clean and create modes are mutually exclusive")
        if self.jobs is not None and self.jobs <= 0:
            raise ValueError("restore jobs must be > 0")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("restore timeout_seconds must be > 0")


@dataclass(frozen=True, slots=True)
class RestoreValidation:
    """Preflight result for one restore request."""

    valid: bool
    backup_format: BackupFormat | None
    target_exists: bool | None
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RestoreOperation:
    """Completed restore execution."""

    backup: Backup
    target_database: str
    started_at: datetime
    finished_at: datetime | None
    status: OperationStatus
    duration_ms: int
    verification_passed: bool
    tool: str
    tool_version: str | None

    def __post_init__(self) -> None:
        if not self.target_database or self.target_database.isspace():
            raise ValueError("restore target_database must not be blank")
        if self.duration_ms < 0:
            raise ValueError("restore duration_ms must be >= 0")
        if not self.tool or self.tool.isspace():
            raise ValueError("restore tool must not be blank")

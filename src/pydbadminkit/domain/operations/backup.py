"""Backup domain models."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from pydbadminkit.domain.common import (
    DatabaseEngine,
    DatabaseVersion,
    OperationStatus,
)


class BackupFormat(StrEnum):
    """Logical backup formats exposed by PyDBAdminKit."""

    CUSTOM = "custom"
    PLAIN_SQL = "plain_sql"
    DIRECTORY = "directory"
    TAR = "tar"


@dataclass(frozen=True, slots=True)
class Backup:
    """Logical backup artifact."""

    id: str
    database: str
    format: BackupFormat
    path: str
    created_at: datetime
    size_bytes: int | None
    checksum: str | None
    engine: DatabaseEngine
    engine_version: DatabaseVersion | None
    tool_version: str | None
    status: OperationStatus

    def __post_init__(self) -> None:
        if not self.id or self.id.isspace():
            raise ValueError("backup id must not be blank")
        if not self.database or self.database.isspace():
            raise ValueError("backup database must not be blank")
        if not self.path or self.path.isspace():
            raise ValueError("backup path must not be blank")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("backup size_bytes must be >= 0")


@dataclass(frozen=True, slots=True)
class BackupMetadata:
    """Secret-safe sidecar metadata for one backup artifact."""

    backup_id: str
    database: str
    format: BackupFormat
    created_at: datetime
    engine: DatabaseEngine
    engine_version: DatabaseVersion | None
    tool_version: str | None
    size_bytes: int | None
    checksum_algorithm: str | None
    checksum: str | None

    def __post_init__(self) -> None:
        if not self.backup_id or self.backup_id.isspace():
            raise ValueError("backup metadata id must not be blank")
        if not self.database or self.database.isspace():
            raise ValueError("backup metadata database must not be blank")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("backup metadata size_bytes must be >= 0")


@dataclass(frozen=True, slots=True)
class CreateBackupCommand:
    """Request one logical database backup."""

    database: str
    format: BackupFormat
    output_path: str
    compress: bool | None = None
    checksum: bool = True
    jobs: int | None = None
    timeout_seconds: float | None = None
    force: bool = False

    def __post_init__(self) -> None:
        if not self.database or self.database.isspace():
            raise ValueError("backup database must not be blank")
        if not self.output_path or self.output_path.isspace():
            raise ValueError("backup output_path must not be blank")
        if self.jobs is not None and self.jobs <= 0:
            raise ValueError("backup jobs must be > 0")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("backup timeout_seconds must be > 0")


@dataclass(frozen=True, slots=True)
class BackupValidation:
    """Validation result for one backup artifact."""

    valid: bool
    level: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.level or self.level.isspace():
            raise ValueError("backup validation level must not be blank")


@dataclass(frozen=True, slots=True)
class BackupPaths:
    """Filesystem paths used while atomically producing one backup."""

    final_path: str
    temporary_path: str
    metadata_path: str
    metadata_temporary_path: str


@dataclass(frozen=True, slots=True)
class BackupArtifactInfo:
    """Filesystem inspection result for a backup artifact."""

    exists: bool
    readable: bool
    size_bytes: int | None


@dataclass(frozen=True, slots=True)
class ExternalTool:
    """Resolved external PostgreSQL utility."""

    name: str
    path: str | None
    version: str | None
    available: bool

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("external tool name must not be blank")
        if self.available and (self.path is None or not self.path):
            raise ValueError("available external tool requires a path")


@dataclass(frozen=True, slots=True)
class ProcessResult:
    """Secret-safe process execution result."""

    return_code: int
    stdout: str
    stderr: str
    duration_ms: int

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("process duration_ms must be >= 0")


@dataclass(frozen=True, slots=True)
class BackupToolResult:
    """Native-tool result associated with its resolved executable."""

    tool: ExternalTool
    process: ProcessResult

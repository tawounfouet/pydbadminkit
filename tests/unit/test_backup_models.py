"""Unit tests for backup domain models."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.domain.common import DatabaseEngine, DatabaseVersion, OperationStatus
from pydbadminkit.domain.operations import (
    Backup,
    BackupFormat,
    BackupMetadata,
    BackupValidation,
    CreateBackupCommand,
    ExternalTool,
    ProcessResult,
)

pytestmark = [pytest.mark.unit, pytest.mark.backup]


def test_backup_models_accept_valid_values() -> None:
    created_at = datetime(2026, 9, 22, tzinfo=UTC)
    backup = Backup(
        id="backup_1",
        database="accounting",
        format=BackupFormat.CUSTOM,
        path="/tmp/accounting.dump",
        created_at=created_at,
        size_bytes=42,
        checksum="abc",
        engine=DatabaseEngine.POSTGRESQL,
        engine_version=DatabaseVersion(18),
        tool_version="18",
        status=OperationStatus.SUCCEEDED,
    )
    metadata = BackupMetadata(
        backup_id=backup.id,
        database=backup.database,
        format=backup.format,
        created_at=created_at,
        engine=backup.engine,
        engine_version=backup.engine_version,
        tool_version=backup.tool_version,
        size_bytes=backup.size_bytes,
        checksum_algorithm="sha256",
        checksum=backup.checksum,
    )
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path="/tmp/accounting.dump",
        timeout_seconds=30,
    )
    validation = BackupValidation(
        valid=True,
        level="logical",
        warnings=(),
        errors=(),
    )
    tool = ExternalTool(
        name="pg_dump",
        path="/usr/bin/pg_dump",
        version="pg_dump (PostgreSQL) 18.1",
        available=True,
    )
    process = ProcessResult(
        return_code=0,
        stdout="",
        stderr="",
        duration_ms=10,
    )

    assert metadata.backup_id == backup.id
    assert command.checksum is True
    assert validation.valid is True
    assert tool.available is True
    assert process.duration_ms == 10


@pytest.mark.parametrize(
    "factory",
    [
        lambda: CreateBackupCommand(
            database="",
            format=BackupFormat.CUSTOM,
            output_path="/tmp/x.dump",
        ),
        lambda: CreateBackupCommand(
            database="db",
            format=BackupFormat.CUSTOM,
            output_path="",
        ),
        lambda: CreateBackupCommand(
            database="db",
            format=BackupFormat.CUSTOM,
            output_path="/tmp/x.dump",
            jobs=0,
        ),
        lambda: CreateBackupCommand(
            database="db",
            format=BackupFormat.CUSTOM,
            output_path="/tmp/x.dump",
            timeout_seconds=0,
        ),
        lambda: ExternalTool(
            name="pg_dump",
            path=None,
            version="18",
            available=True,
        ),
        lambda: ProcessResult(
            return_code=0,
            stdout="",
            stderr="",
            duration_ms=-1,
        ),
    ],
)
def test_backup_models_reject_invalid_values(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]

"""Unit tests for restore domain models."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.domain.common import DatabaseEngine, OperationStatus
from pydbadminkit.domain.operations import (
    Backup,
    BackupFormat,
    RestoreBackupCommand,
    RestoreOperation,
    RestoreValidation,
)

pytestmark = [pytest.mark.unit, pytest.mark.restore]


def _backup() -> Backup:
    return Backup(
        id="backup_test",
        database="source",
        format=BackupFormat.CUSTOM,
        path="/tmp/source.dump",
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
        size_bytes=42,
        checksum="abc",
        engine=DatabaseEngine.POSTGRESQL,
        engine_version=None,
        tool_version="18",
        status=OperationStatus.SUCCEEDED,
    )


def test_restore_models_accept_valid_values() -> None:
    command = RestoreBackupCommand(
        backup_path="/tmp/source.dump",
        target_database="target",
        create=True,
        jobs=2,
        timeout_seconds=30,
    )
    validation = RestoreValidation(
        valid=True,
        backup_format=BackupFormat.CUSTOM,
        target_exists=False,
        warnings=(),
        errors=(),
    )
    operation = RestoreOperation(
        backup=_backup(),
        target_database="target",
        started_at=datetime(2026, 9, 22, tzinfo=UTC),
        finished_at=datetime(2026, 9, 22, tzinfo=UTC),
        status=OperationStatus.SUCCEEDED,
        duration_ms=10,
        verification_passed=True,
        tool="pg_restore",
        tool_version="18",
    )

    assert command.create is True
    assert validation.valid is True
    assert operation.verification_passed is True


@pytest.mark.parametrize(
    "factory",
    [
        lambda: RestoreBackupCommand("", "target"),
        lambda: RestoreBackupCommand("/tmp/x.dump", ""),
        lambda: RestoreBackupCommand("/tmp/x.dump", "target", clean=True, create=True),
        lambda: RestoreBackupCommand("/tmp/x.dump", "target", jobs=0),
        lambda: RestoreBackupCommand("/tmp/x.dump", "target", timeout_seconds=0),
        lambda: RestoreOperation(
            backup=_backup(),
            target_database="",
            started_at=datetime(2026, 9, 22, tzinfo=UTC),
            finished_at=None,
            status=OperationStatus.FAILED,
            duration_ms=0,
            verification_passed=False,
            tool="pg_restore",
            tool_version="18",
        ),
        lambda: RestoreOperation(
            backup=_backup(),
            target_database="target",
            started_at=datetime(2026, 9, 22, tzinfo=UTC),
            finished_at=None,
            status=OperationStatus.FAILED,
            duration_ms=-1,
            verification_passed=False,
            tool="pg_restore",
            tool_version="18",
        ),
        lambda: RestoreOperation(
            backup=_backup(),
            target_database="target",
            started_at=datetime(2026, 9, 22, tzinfo=UTC),
            finished_at=None,
            status=OperationStatus.FAILED,
            duration_ms=0,
            verification_passed=False,
            tool="",
            tool_version="18",
        ),
    ],
)
def test_restore_models_reject_invalid_values(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]

"""Unit tests for backup restore CLI."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app
from pydbadminkit.domain.common import (
    DatabaseEngine,
    EnvironmentName,
    OperationStatus,
    RiskLevel,
)
from pydbadminkit.domain.operations import (
    Backup,
    BackupFormat,
    RestoreBackupCommand,
    RestoreOperation,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan

pytestmark = [pytest.mark.unit, pytest.mark.restore]

runner = CliRunner()


def _backup(path: str) -> Backup:
    return Backup(
        id="backup_test",
        database="source",
        format=BackupFormat.CUSTOM,
        path=path,
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
        size_bytes=42,
        checksum="abc",
        engine=DatabaseEngine.POSTGRESQL,
        engine_version=None,
        tool_version="18",
        status=OperationStatus.SUCCEEDED,
    )


class FakeRestoreService:
    def plan_restore(self, command: RestoreBackupCommand) -> OperationPlan:
        return OperationPlan(
            operation="backup.restore",
            target=command.target_database,
            environment=EnvironmentName.TESTING,
            risk=RiskLevel.HIGH,
            confirmation=ConfirmationLevel.EXPLICIT,
            effects=("Restore backup.",),
            correlation_id="restore-correlation",
        )

    def restore(
        self,
        command: RestoreBackupCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | RestoreOperation:
        assert plan is not None
        if options.dry_run:
            return plan
        return RestoreOperation(
            backup=_backup(command.backup_path),
            target_database=command.target_database,
            started_at=datetime(2026, 9, 22, tzinfo=UTC),
            finished_at=datetime(2026, 9, 22, tzinfo=UTC),
            status=OperationStatus.SUCCEEDED,
            duration_ms=12,
            verification_passed=True,
            tool="pg_restore",
            tool_version="18",
        )


@pytest.fixture
def fake_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pydbadminkit.cli.commands.backup.build_restore_service",
        lambda *args, **kwargs: FakeRestoreService(),
    )


def test_restore_dry_run_json(fake_restore: None, tmp_path: Path) -> None:
    del fake_restore
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--dry-run",
            "--output",
            "json",
            "backup",
            "restore",
            str(tmp_path / "source.dump"),
            "--database",
            "target",
            "--create",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["operation"] == "backup.restore"
    assert parsed["target"] == "target"


def test_restore_success_human_output(fake_restore: None, tmp_path: Path) -> None:
    del fake_restore
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--yes",
            "backup",
            "restore",
            str(tmp_path / "source.dump"),
            "--database",
            "target",
            "--create",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Target: target" in result.stdout
    assert "Verification: passed" in result.stdout

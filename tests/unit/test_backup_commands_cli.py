"""Unit tests for backup CLI commands."""

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
    BackupValidation,
    CreateBackupCommand,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan

pytestmark = [pytest.mark.unit, pytest.mark.backup]

runner = CliRunner()


def _plan(target: str) -> OperationPlan:
    return OperationPlan(
        operation="backup.create",
        target=target,
        environment=EnvironmentName.TESTING,
        risk=RiskLevel.LOW,
        confirmation=ConfirmationLevel.NONE,
        effects=("Create backup.",),
        correlation_id="backup-correlation",
    )


def _backup(path: str) -> Backup:
    return Backup(
        id="backup_test",
        database="accounting",
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


class FakeBackupService:
    def __init__(self) -> None:
        self.commands: list[CreateBackupCommand] = []

    def plan_create_backup(self, command: CreateBackupCommand) -> OperationPlan:
        return _plan(command.output_path)

    def create_backup(
        self,
        command: CreateBackupCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | Backup:
        assert plan is not None
        self.commands.append(command)
        if options.dry_run:
            return plan
        return _backup(command.output_path)


class FakeValidationService:
    def validate_backup(
        self,
        path: str,
        *,
        timeout_seconds: float | None = None,
    ) -> BackupValidation:
        del path, timeout_seconds
        return BackupValidation(
            valid=True,
            level="logical",
            warnings=(),
            errors=(),
        )


@pytest.fixture
def fake_services(monkeypatch: pytest.MonkeyPatch) -> FakeBackupService:
    service = FakeBackupService()
    monkeypatch.setattr(
        "pydbadminkit.cli.commands.backup.build_backup_service",
        lambda *args, **kwargs: service,
    )
    monkeypatch.setattr(
        "pydbadminkit.cli.commands.backup.build_backup_validation_service",
        lambda: FakeValidationService(),
    )
    return service


def test_backup_create_human_output(
    tmp_path: Path,
    fake_services: FakeBackupService,
) -> None:
    target = tmp_path / "accounting.dump"

    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "backup",
            "create",
            "accounting",
            "--output-path",
            str(target),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Backup ID: backup_test" in result.stdout
    assert "Status: succeeded" in result.stdout
    assert fake_services.commands[0].output_path == str(target)


def test_backup_create_dry_run_json(
    tmp_path: Path,
    fake_services: FakeBackupService,
) -> None:
    target = tmp_path / "accounting.dump"

    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--dry-run",
            "--output",
            "json",
            "backup",
            "create",
            "accounting",
            "--output-path",
            str(target),
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["operation"] == "backup.create"
    assert parsed["target"] == str(target)


def test_backup_validate_does_not_require_connection_profile(
    fake_services: FakeBackupService,
) -> None:
    del fake_services

    result = runner.invoke(
        app,
        ["--output", "json", "backup", "validate", "accounting.dump"],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["valid"] is True
    assert parsed["level"] == "logical"


def test_backup_create_default_path_uses_format_suffix(
    fake_services: FakeBackupService,
) -> None:
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "backup",
            "create",
            "accounting",
            "--format",
            "plain_sql",
        ],
    )

    assert result.exit_code == 0, result.output
    assert fake_services.commands[-1].output_path == "accounting.sql"

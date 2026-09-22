"""Unit tests for backup application services."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from pydbadminkit.application.operations import BackupService, BackupValidationService
from pydbadminkit.domain.audit import AuditEvent, AuditEventType
from pydbadminkit.domain.common import (
    DatabaseEngine,
    EnvironmentName,
    OperationStatus,
    RiskLevel,
)
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SSLConfig,
    TimeoutConfig,
)
from pydbadminkit.domain.operations import (
    Backup,
    BackupFormat,
    BackupValidation,
    CreateBackupCommand,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.errors import ConfirmationRequiredError, PolicyDeniedError

pytestmark = [pytest.mark.unit, pytest.mark.backup]


class FakeBackupPort:
    def __init__(self, backup: Backup) -> None:
        self.backup = backup
        self.created: list[CreateBackupCommand] = []
        self.validated: list[str] = []

    def create_backup(self, command: CreateBackupCommand) -> Backup:
        self.created.append(command)
        return self.backup

    def validate_backup(
        self,
        backup: Backup,
        *,
        timeout_seconds: float | None = None,
    ) -> BackupValidation:
        del timeout_seconds
        self.validated.append(backup.path)
        return BackupValidation(True, "logical", (), ())


class FakeAuditPort:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)


class FakeFileStore:
    def __init__(self, backup: Backup) -> None:
        self.backup = backup

    def load_backup(self, path: str) -> Backup:
        assert path == self.backup.path
        return self.backup


def _backup(path: str = "/tmp/accounting.dump") -> Backup:
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


def _config(
    environment: EnvironmentName = EnvironmentName.TESTING,
) -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("local"),
        engine=DatabaseEngine.POSTGRESQL,
        host="127.0.0.1",
        port=5432,
        database="postgres",
        username="postgres",
        password=None,
        environment=environment,
        read_only=False,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(),
    )


def test_backup_dry_run_does_not_execute_or_audit() -> None:
    backup = _backup()
    port = FakeBackupPort(backup)
    audit = FakeAuditPort()
    service = BackupService(
        backup_port=port,
        audit_port=audit,
        config=_config(),
    )
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path=backup.path,
    )
    plan = service.plan_create_backup(command)

    outcome = service.create_backup(
        command,
        MutationOptions(dry_run=True),
        plan=plan,
    )

    assert isinstance(outcome, OperationPlan)
    assert outcome.risk is RiskLevel.LOW
    assert outcome.confirmation is ConfirmationLevel.NONE
    assert port.created == []
    assert audit.events == []


def test_force_backup_requires_approval_and_audits_success() -> None:
    backup = _backup()
    port = FakeBackupPort(backup)
    audit = FakeAuditPort()
    service = BackupService(
        backup_port=port,
        audit_port=audit,
        config=_config(),
    )
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path=backup.path,
        force=True,
    )
    plan = service.plan_create_backup(command)

    assert plan.risk is RiskLevel.MEDIUM

    with pytest.raises(ConfirmationRequiredError):
        service.create_backup(command, MutationOptions(), plan=plan)

    audit.events.clear()
    outcome = service.create_backup(
        command,
        MutationOptions(approved=True),
        plan=plan,
    )

    assert outcome == backup
    assert [event.event_type for event in audit.events] == [
        AuditEventType.STARTED,
        AuditEventType.SUCCEEDED,
    ]


def test_production_force_backup_is_high_risk() -> None:
    service = BackupService(
        backup_port=FakeBackupPort(_backup()),
        audit_port=FakeAuditPort(),
        config=_config(EnvironmentName.PRODUCTION),
    )
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path="/tmp/accounting.dump",
        force=True,
    )

    plan = service.plan_create_backup(command)

    assert plan.risk is RiskLevel.HIGH
    assert plan.confirmation is ConfirmationLevel.EXPLICIT
    assert any("production-sensitive" in warning for warning in plan.warnings)


def test_force_backup_unknown_environment_fails_closed() -> None:
    audit = FakeAuditPort()
    service = BackupService(
        backup_port=FakeBackupPort(_backup()),
        audit_port=audit,
        config=_config(EnvironmentName.UNKNOWN),
    )
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path="/tmp/accounting.dump",
        force=True,
    )
    plan = service.plan_create_backup(command)

    with pytest.raises(PolicyDeniedError):
        service.create_backup(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )

    assert audit.events[-1].event_type is AuditEventType.BLOCKED


def test_backup_validation_service_loads_sidecar_backed_backup() -> None:
    backup = _backup()
    port = FakeBackupPort(backup)
    service = BackupValidationService(
        backup_port=port,
        file_store=FakeFileStore(backup),  # type: ignore[arg-type]
    )

    validation = service.validate_backup(backup.path)

    assert validation.valid is True
    assert port.validated == [backup.path]

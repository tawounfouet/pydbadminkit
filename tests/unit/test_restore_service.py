"""Unit tests for guarded restore orchestration."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.application.operations import RestoreService
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
    RestoreBackupCommand,
    RestoreOperation,
    RestoreValidation,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.errors import ConfirmationRequiredError, PolicyDeniedError

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


class FakeBackupPort:
    def validate_backup(
        self,
        backup: Backup,
        *,
        timeout_seconds: float | None = None,
    ) -> BackupValidation:
        del backup, timeout_seconds
        return BackupValidation(True, "logical", (), ())


class FakeFileStore:
    def load_backup(self, path: str) -> Backup:
        assert path == "/tmp/source.dump"
        return _backup()


class FakeRestorePort:
    def __init__(self, *, target_exists: bool = False) -> None:
        self.target_exists = target_exists
        self.calls = 0

    def validate_restore(
        self,
        command: RestoreBackupCommand,
        backup: Backup,
    ) -> RestoreValidation:
        del command, backup
        return RestoreValidation(
            True,
            BackupFormat.CUSTOM,
            self.target_exists,
            (),
            (),
        )

    def restore_backup(
        self,
        command: RestoreBackupCommand,
        backup: Backup,
    ) -> RestoreOperation:
        self.calls += 1
        return RestoreOperation(
            backup=backup,
            target_database=command.target_database,
            started_at=datetime(2026, 9, 22, tzinfo=UTC),
            finished_at=datetime(2026, 9, 22, tzinfo=UTC),
            status=OperationStatus.SUCCEEDED,
            duration_ms=5,
            verification_passed=True,
            tool="pg_restore",
            tool_version="18",
        )


class FakeAuditPort:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)


def _config(
    environment: EnvironmentName = EnvironmentName.TESTING,
    *,
    read_only: bool = False,
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
        read_only=read_only,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(),
    )


def _service(
    config: ResolvedConnectionConfig,
    restore: FakeRestorePort | None = None,
) -> tuple[RestoreService, FakeRestorePort, FakeAuditPort]:
    restore_port = restore or FakeRestorePort()
    audit = FakeAuditPort()
    return (
        RestoreService(
            restore_port=restore_port,
            backup_port=FakeBackupPort(),  # type: ignore[arg-type]
            file_store=FakeFileStore(),  # type: ignore[arg-type]
            audit_port=audit,
            config=config,
        ),
        restore_port,
        audit,
    )


def test_restore_dry_run_is_high_risk_and_does_not_execute() -> None:
    service, restore_port, audit = _service(_config())
    command = RestoreBackupCommand("/tmp/source.dump", "target", create=True)
    plan = service.plan_restore(command)

    outcome = service.restore(
        command,
        MutationOptions(dry_run=True),
        plan=plan,
    )

    assert isinstance(outcome, OperationPlan)
    assert plan.risk is RiskLevel.HIGH
    assert plan.confirmation is ConfirmationLevel.EXPLICIT
    assert restore_port.calls == 0
    assert audit.events == []


def test_restore_requires_approval_and_audits_success() -> None:
    service, restore_port, audit = _service(_config())
    command = RestoreBackupCommand("/tmp/source.dump", "target", create=True)
    plan = service.plan_restore(command)

    with pytest.raises(ConfirmationRequiredError):
        service.restore(command, MutationOptions(), plan=plan)

    audit.events.clear()
    outcome = service.restore(
        command,
        MutationOptions(approved=True),
        plan=plan,
    )

    assert isinstance(outcome, RestoreOperation)
    assert restore_port.calls == 1
    assert [event.event_type for event in audit.events] == [
        AuditEventType.STARTED,
        AuditEventType.SUCCEEDED,
    ]


def test_production_restore_is_critical_and_requires_typed_target() -> None:
    service, _restore_port, _audit = _service(_config(EnvironmentName.PRODUCTION))
    command = RestoreBackupCommand("/tmp/source.dump", "prod_target", create=True)
    plan = service.plan_restore(command)

    assert plan.risk is RiskLevel.CRITICAL
    assert plan.confirmation is ConfirmationLevel.TYPE_TARGET

    with pytest.raises(ConfirmationRequiredError):
        service.restore(
            command,
            MutationOptions(confirmed_target="wrong"),
            plan=plan,
        )


@pytest.mark.parametrize(
    "config",
    [
        _config(read_only=True),
        _config(EnvironmentName.UNKNOWN),
    ],
)
def test_restore_policy_fails_closed(config: ResolvedConnectionConfig) -> None:
    service, _restore_port, audit = _service(config)
    command = RestoreBackupCommand("/tmp/source.dump", "target", create=True)
    plan = service.plan_restore(command)

    with pytest.raises(PolicyDeniedError):
        service.restore(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )

    assert audit.events[-1].event_type is AuditEventType.BLOCKED

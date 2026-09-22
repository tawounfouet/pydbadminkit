"""Unit tests for guarded maintenance orchestration."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.application.operations import MaintenanceService
from pydbadminkit.domain.audit import AuditEvent, AuditEventType
from pydbadminkit.domain.common import (
    DatabaseEngine,
    EnvironmentName,
    OperationStatus,
    QualifiedName,
    RiskLevel,
)
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SSLConfig,
    TimeoutConfig,
)
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    MaintenanceOperation,
    MaintenanceOperationType,
    MaintenanceProgress,
    ReindexCommand,
    ReindexTargetType,
    VacuumCommand,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.errors import ConfirmationRequiredError, PolicyDeniedError

pytestmark = [pytest.mark.unit, pytest.mark.maintenance]


class FakeMaintenancePort:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def validate_vacuum(self, command: VacuumCommand) -> None:
        del command
        self.calls.append("validate_vacuum")

    def validate_analyze(self, command: AnalyzeCommand) -> None:
        del command
        self.calls.append("validate_analyze")

    def validate_reindex(self, command: ReindexCommand) -> None:
        del command
        self.calls.append("validate_reindex")

    def vacuum(self, command: VacuumCommand) -> MaintenanceOperation:
        self.calls.append("vacuum")
        return _operation(MaintenanceOperationType.VACUUM, command.table)

    def analyze(self, command: AnalyzeCommand) -> MaintenanceOperation:
        self.calls.append("analyze")
        return _operation(MaintenanceOperationType.ANALYZE, command.table)

    def reindex(self, command: ReindexCommand) -> MaintenanceOperation:
        self.calls.append("reindex")
        return _operation(MaintenanceOperationType.REINDEX, command.target)

    def list_vacuum_progress(self) -> tuple[MaintenanceProgress, ...]:
        self.calls.append("vacuum_progress")
        return (_progress(MaintenanceOperationType.VACUUM),)

    def list_reindex_progress(self) -> tuple[MaintenanceProgress, ...]:
        self.calls.append("reindex_progress")
        return (_progress(MaintenanceOperationType.REINDEX),)


class FakeAuditPort:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)


def _operation(
    operation_type: MaintenanceOperationType,
    target: QualifiedName | None,
) -> MaintenanceOperation:
    return MaintenanceOperation(
        operation_type=operation_type,
        target=target,
        started_at=datetime(2026, 9, 22, tzinfo=UTC),
        finished_at=datetime(2026, 9, 22, tzinfo=UTC),
        status=OperationStatus.SUCCEEDED,
        duration_ms=15,
        message=f"{operation_type.value} completed.",
    )


def _progress(operation_type: MaintenanceOperationType) -> MaintenanceProgress:
    return MaintenanceProgress(
        operation_type=operation_type,
        pid=123,
        target=QualifiedName(schema="public", name="events"),
        phase="working",
        completed=1,
        total=2,
        percent=50.0,
    )


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
        database="pydbadmin_test",
        username="postgres",
        password=None,
        environment=environment,
        read_only=read_only,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(),
    )


def _service(
    config: ResolvedConnectionConfig | None = None,
) -> tuple[MaintenanceService, FakeMaintenancePort, FakeAuditPort]:
    port = FakeMaintenancePort()
    audit = FakeAuditPort()
    return (
        MaintenanceService(
            maintenance_port=port,
            audit_port=audit,
            config=config or _config(),
        ),
        port,
        audit,
    )


def test_vacuum_dry_run_preflights_without_execution() -> None:
    service, port, audit = _service()
    command = VacuumCommand(
        table=QualifiedName(schema="public", name="events")
    )
    plan = service.plan_vacuum(command)

    outcome = service.vacuum(
        command,
        MutationOptions(dry_run=True),
        plan=plan,
    )

    assert isinstance(outcome, OperationPlan)
    assert plan.risk is RiskLevel.MEDIUM
    assert plan.confirmation is ConfirmationLevel.SIMPLE
    assert port.calls == ["validate_vacuum"]
    assert audit.events == []


def test_vacuum_full_and_reindex_risk_escalation() -> None:
    service, _port, _audit = _service()
    full = service.plan_vacuum(
        VacuumCommand(
            table=QualifiedName(schema="public", name="events"),
            full=True,
        )
    )
    reindex = service.plan_reindex(
        ReindexCommand(
            target_type=ReindexTargetType.INDEX,
            target=QualifiedName(schema="public", name="events_idx"),
        )
    )

    assert full.risk is RiskLevel.HIGH
    assert full.confirmation is ConfirmationLevel.EXPLICIT
    assert reindex.risk is RiskLevel.HIGH

    prod, _port2, _audit2 = _service(_config(EnvironmentName.PRODUCTION))
    critical = prod.plan_reindex(
        ReindexCommand(
            target_type=ReindexTargetType.TABLE,
            target=QualifiedName(schema="public", name="events"),
        )
    )
    assert critical.risk is RiskLevel.CRITICAL
    assert critical.confirmation is ConfirmationLevel.TYPE_TARGET


def test_analyze_requires_approval_and_success_is_audited() -> None:
    service, port, audit = _service()
    command = AnalyzeCommand(
        table=QualifiedName(schema="public", name="events"),
        columns=("payload",),
    )
    plan = service.plan_analyze(command)

    with pytest.raises(ConfirmationRequiredError):
        service.analyze(command, MutationOptions(), plan=plan)

    audit.events.clear()
    outcome = service.analyze(
        command,
        MutationOptions(approved=True),
        plan=plan,
    )

    assert outcome.status is OperationStatus.SUCCEEDED
    assert outcome.metadata is not None
    assert outcome.metadata["duration_ms"] == 15
    assert "analyze" in port.calls
    assert [event.event_type for event in audit.events] == [
        AuditEventType.STARTED,
        AuditEventType.SUCCEEDED,
    ]


@pytest.mark.parametrize(
    "config",
    [
        _config(read_only=True),
        _config(EnvironmentName.UNKNOWN),
    ],
)
def test_maintenance_policy_fails_closed(config: ResolvedConnectionConfig) -> None:
    service, _port, audit = _service(config)
    command = VacuumCommand()
    plan = service.plan_vacuum(command)

    with pytest.raises(PolicyDeniedError):
        service.vacuum(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )

    assert audit.events[-1].event_type is AuditEventType.BLOCKED


def test_production_critical_operation_requires_exact_target() -> None:
    service, _port, _audit = _service(_config(EnvironmentName.PRODUCTION))
    command = ReindexCommand(
        target_type=ReindexTargetType.INDEX,
        target=QualifiedName(schema="public", name="events_idx"),
    )
    plan = service.plan_reindex(command)

    with pytest.raises(ConfirmationRequiredError):
        service.reindex(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )

    outcome = service.reindex(
        command,
        MutationOptions(confirmed_target=plan.target),
        plan=plan,
    )

    assert outcome.status is OperationStatus.SUCCEEDED


def test_progress_surfaces_are_read_only() -> None:
    service, port, audit = _service(_config(read_only=True))

    vacuum = service.list_vacuum_progress()
    reindex = service.list_reindex_progress()

    assert vacuum[0].operation_type is MaintenanceOperationType.VACUUM
    assert reindex[0].operation_type is MaintenanceOperationType.REINDEX
    assert port.calls == ["vacuum_progress", "reindex_progress"]
    assert audit.events == []

"""Unit tests for guarded security mutation orchestration."""

import pytest

from pydbadminkit.application.security import SecurityMutationService
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
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.domain.security import (
    AccessType,
    AlterRoleCommand,
    CreateRoleCommand,
    MembershipCommand,
    RelationAccessCommand,
)
from pydbadminkit.errors import ConfirmationRequiredError, PolicyDeniedError

pytestmark = [pytest.mark.unit, pytest.mark.security]


class FakeMutationPort:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def create_role(self, command: CreateRoleCommand) -> None:
        self.calls.append(("create_role", command))

    def alter_role(self, command: AlterRoleCommand) -> None:
        self.calls.append(("alter_role", command))

    def drop_role(self, name: str) -> None:
        self.calls.append(("drop_role", name))

    def add_membership(self, command: MembershipCommand) -> None:
        self.calls.append(("add_membership", command))

    def remove_membership(self, command: MembershipCommand) -> None:
        self.calls.append(("remove_membership", command))

    def grant_access(self, command: RelationAccessCommand) -> None:
        self.calls.append(("grant_access", command))

    def revoke_access(self, command: RelationAccessCommand) -> None:
        self.calls.append(("revoke_access", command))


class FakeAuditPort:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)


def _config(
    *,
    environment: EnvironmentName = EnvironmentName.TESTING,
    read_only: bool = False,
    username: str = "postgres",
) -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("local"),
        engine=DatabaseEngine.POSTGRESQL,
        host="127.0.0.1",
        port=5432,
        database="pydbadmin_test",
        username=username,
        password=None,
        environment=environment,
        read_only=read_only,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(),
    )


def _service(
    *,
    environment: EnvironmentName = EnvironmentName.TESTING,
    read_only: bool = False,
    username: str = "postgres",
) -> tuple[SecurityMutationService, FakeMutationPort, FakeAuditPort]:
    mutation = FakeMutationPort()
    audit = FakeAuditPort()
    return (
        SecurityMutationService(
            mutation,
            audit,
            _config(
                environment=environment,
                read_only=read_only,
                username=username,
            ),
        ),
        mutation,
        audit,
    )


def test_dry_run_returns_plan_without_mutation_or_audit() -> None:
    service, mutation, audit = _service()
    command = CreateRoleCommand(name="app", can_login=True)
    plan = service.plan_create_role(command)

    outcome = service.create_role(
        command,
        MutationOptions(dry_run=True),
        plan=plan,
    )

    assert isinstance(outcome, OperationPlan)
    assert outcome.target == "app"
    assert mutation.calls == []
    assert audit.events == []


def test_medium_risk_requires_approval_and_audits_block() -> None:
    service, mutation, audit = _service()
    command = CreateRoleCommand(name="app")
    plan = service.plan_create_role(command)

    assert plan.risk is RiskLevel.MEDIUM
    assert plan.confirmation is ConfirmationLevel.SIMPLE

    with pytest.raises(ConfirmationRequiredError):
        service.create_role(command, MutationOptions(), plan=plan)

    assert mutation.calls == []
    assert audit.events[-1].event_type is AuditEventType.BLOCKED
    assert audit.events[-1].status is OperationStatus.BLOCKED


def test_superuser_creation_requires_typed_target() -> None:
    service, mutation, _audit = _service()
    command = CreateRoleCommand(name="admin", is_superuser=True)
    plan = service.plan_create_role(command)

    assert plan.risk is RiskLevel.CRITICAL
    assert plan.confirmation is ConfirmationLevel.TYPE_TARGET

    with pytest.raises(ConfirmationRequiredError):
        service.create_role(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )

    outcome = service.create_role(
        command,
        MutationOptions(confirmed_target="admin"),
        plan=plan,
    )

    assert outcome.status is OperationStatus.SUCCEEDED
    assert mutation.calls[0][0] == "create_role"


def test_read_only_and_unknown_environment_fail_closed() -> None:
    command = CreateRoleCommand(name="app")

    read_only, _mutation, _audit = _service(read_only=True)
    plan = read_only.plan_create_role(command)
    with pytest.raises(PolicyDeniedError):
        read_only.create_role(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )

    unknown, _mutation2, _audit2 = _service(environment=EnvironmentName.UNKNOWN)
    plan2 = unknown.plan_create_role(command)
    with pytest.raises(PolicyDeniedError):
        unknown.create_role(
            command,
            MutationOptions(approved=True),
            plan=plan2,
        )


def test_drop_current_role_and_builtin_role_are_protected() -> None:
    service, _mutation, _audit = _service(username="postgres")

    current_plan = service.plan_drop_role("postgres")
    with pytest.raises(PolicyDeniedError):
        service.drop_role(
            "postgres",
            MutationOptions(approved=True),
            plan=current_plan,
        )

    builtin_plan = service.plan_drop_role("pg_monitor")
    with pytest.raises(PolicyDeniedError):
        service.drop_role(
            "pg_monitor",
            MutationOptions(approved=True),
            plan=builtin_plan,
        )


def test_successful_mutation_writes_started_and_succeeded_audit_events() -> None:
    service, mutation, audit = _service()
    command = MembershipCommand(role="reader", member="app")
    plan = service.plan_add_membership(command)

    outcome = service.add_membership(
        command,
        MutationOptions(approved=True),
        plan=plan,
    )

    assert outcome.status is OperationStatus.SUCCEEDED
    assert mutation.calls[0][0] == "add_membership"
    assert [event.event_type for event in audit.events] == [
        AuditEventType.STARTED,
        AuditEventType.SUCCEEDED,
    ]
    assert audit.events[0].correlation_id == plan.correlation_id


def test_production_access_grant_escalates_to_typed_confirmation() -> None:
    service, _mutation, _audit = _service(environment=EnvironmentName.PRODUCTION)
    command = RelationAccessCommand(
        principal="app",
        access_type=AccessType.SELECT,
        object=QualifiedName(schema="public", name="customers"),
    )

    plan = service.plan_grant_access(command)

    assert plan.risk is RiskLevel.HIGH
    assert plan.confirmation is ConfirmationLevel.EXPLICIT

    grant_option_command = RelationAccessCommand(
        principal="app",
        access_type=AccessType.SELECT,
        object=QualifiedName(schema="public", name="customers"),
        grant_option=True,
    )
    critical = service.plan_grant_access(grant_option_command)

    assert critical.risk is RiskLevel.CRITICAL
    assert critical.confirmation is ConfirmationLevel.TYPE_TARGET

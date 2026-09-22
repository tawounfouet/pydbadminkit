"""Unit tests for guarded runtime mutation orchestration."""

import pytest

from pydbadminkit.application.runtime import RuntimeMutationService
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
from pydbadminkit.domain.runtime import (
    BackendSignalResult,
    CancelQueryCommand,
    TerminateSessionCommand,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.errors import (
    ConfirmationRequiredError,
    DatabaseOperationError,
    PolicyDeniedError,
    ResourceNotFoundError,
)

pytestmark = [pytest.mark.unit, pytest.mark.runtime]


class FakeRuntimeMutationPort:
    def __init__(self, result: BackendSignalResult | None = None) -> None:
        self.result = result or BackendSignalResult(
            pid=101,
            target_exists=True,
            self_target=False,
            client_backend=True,
            changed=True,
            backend_type="client backend",
            active_query=True,
        )
        self.calls: list[tuple[str, int]] = []

    def cancel_query(self, command: CancelQueryCommand) -> BackendSignalResult:
        self.calls.append(("cancel", command.pid))
        return self.result

    def terminate_session(
        self,
        command: TerminateSessionCommand,
    ) -> BackendSignalResult:
        self.calls.append(("terminate", command.pid))
        return self.result


class FakeAuditPort:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)


def _config(
    *,
    environment: EnvironmentName = EnvironmentName.TESTING,
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
    *,
    environment: EnvironmentName = EnvironmentName.TESTING,
    read_only: bool = False,
    result: BackendSignalResult | None = None,
) -> tuple[RuntimeMutationService, FakeRuntimeMutationPort, FakeAuditPort]:
    mutation = FakeRuntimeMutationPort(result)
    audit = FakeAuditPort()
    service = RuntimeMutationService(
        mutation_port=mutation,
        audit_port=audit,
        config=_config(environment=environment, read_only=read_only),
    )
    return service, mutation, audit


def test_cancel_query_dry_run_returns_plan_without_signal_or_audit() -> None:
    service, mutation, audit = _service()
    command = CancelQueryCommand(pid=101)
    plan = service.plan_cancel_query(command)

    outcome = service.cancel_query(
        command,
        MutationOptions(dry_run=True),
        plan=plan,
    )

    assert isinstance(outcome, OperationPlan)
    assert outcome.target == "pid:101"
    assert outcome.risk is RiskLevel.MEDIUM
    assert outcome.confirmation is ConfirmationLevel.SIMPLE
    assert mutation.calls == []
    assert audit.events == []


def test_cancel_query_requires_approval_then_audits_success() -> None:
    service, mutation, audit = _service()
    command = CancelQueryCommand(pid=101)
    plan = service.plan_cancel_query(command)

    with pytest.raises(ConfirmationRequiredError):
        service.cancel_query(command, MutationOptions(), plan=plan)

    assert audit.events[-1].event_type is AuditEventType.BLOCKED
    audit.events.clear()

    outcome = service.cancel_query(
        command,
        MutationOptions(approved=True),
        plan=plan,
    )

    assert outcome.status is OperationStatus.SUCCEEDED
    assert mutation.calls[-1] == ("cancel", 101)
    assert [event.event_type for event in audit.events] == [
        AuditEventType.STARTED,
        AuditEventType.SUCCEEDED,
    ]


def test_terminate_session_is_high_risk_and_critical_in_production() -> None:
    service, _mutation, _audit = _service()
    command = TerminateSessionCommand(pid=101)

    plan = service.plan_terminate_session(command)

    assert plan.risk is RiskLevel.HIGH
    assert plan.confirmation is ConfirmationLevel.EXPLICIT

    production, _mutation2, _audit2 = _service(environment=EnvironmentName.PRODUCTION)
    critical = production.plan_terminate_session(command)

    assert critical.risk is RiskLevel.CRITICAL
    assert critical.confirmation is ConfirmationLevel.TYPE_TARGET

    with pytest.raises(ConfirmationRequiredError):
        production.terminate_session(
            command,
            MutationOptions(approved=True),
            plan=critical,
        )

    outcome = production.terminate_session(
        command,
        MutationOptions(confirmed_target="pid:101"),
        plan=critical,
    )
    assert outcome.status is OperationStatus.SUCCEEDED


def test_runtime_mutations_fail_closed_for_profile_policy() -> None:
    command = CancelQueryCommand(pid=101)

    read_only, _mutation, audit = _service(read_only=True)
    plan = read_only.plan_cancel_query(command)
    with pytest.raises(PolicyDeniedError):
        read_only.cancel_query(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )
    assert audit.events[-1].event_type is AuditEventType.BLOCKED

    unknown, _mutation2, _audit2 = _service(environment=EnvironmentName.UNKNOWN)
    plan2 = unknown.plan_cancel_query(command)
    with pytest.raises(PolicyDeniedError):
        unknown.cancel_query(
            command,
            MutationOptions(approved=True),
            plan=plan2,
        )


@pytest.mark.parametrize(
    ("result", "error_type"),
    [
        (
            BackendSignalResult(
                pid=101,
                target_exists=False,
                self_target=False,
                client_backend=False,
                changed=False,
            ),
            ResourceNotFoundError,
        ),
        (
            BackendSignalResult(
                pid=101,
                target_exists=True,
                self_target=True,
                client_backend=True,
                changed=False,
                backend_type="client backend",
            ),
            PolicyDeniedError,
        ),
        (
            BackendSignalResult(
                pid=101,
                target_exists=True,
                self_target=False,
                client_backend=False,
                changed=False,
                backend_type="autovacuum worker",
            ),
            PolicyDeniedError,
        ),
        (
            BackendSignalResult(
                pid=101,
                target_exists=True,
                self_target=False,
                client_backend=True,
                changed=False,
                backend_type="client backend",
                active_query=False,
            ),
            PolicyDeniedError,
        ),
        (
            BackendSignalResult(
                pid=101,
                target_exists=True,
                self_target=False,
                client_backend=True,
                changed=False,
                backend_type="client backend",
                active_query=True,
            ),
            DatabaseOperationError,
        ),
    ],
)
def test_runtime_signal_result_guards(
    result: BackendSignalResult,
    error_type: type[Exception],
) -> None:
    service, _mutation, audit = _service(result=result)
    command = CancelQueryCommand(pid=101)
    plan = service.plan_cancel_query(command)

    with pytest.raises(error_type):
        service.cancel_query(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )

    assert audit.events[0].event_type is AuditEventType.STARTED
    assert audit.events[-1].event_type in {
        AuditEventType.BLOCKED,
        AuditEventType.FAILED,
    }

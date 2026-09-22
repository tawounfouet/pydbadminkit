"""Unit coverage for guarded Runtime mutation CLI commands."""

import json

import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app
from pydbadminkit.domain.common import (
    EnvironmentName,
    OperationResult,
    OperationStatus,
    RiskLevel,
)
from pydbadminkit.domain.runtime import CancelQueryCommand, TerminateSessionCommand
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan

pytestmark = [pytest.mark.unit, pytest.mark.runtime]

runner = CliRunner()


def _plan(
    operation: str,
    target: str,
    *,
    risk: RiskLevel,
) -> OperationPlan:
    confirmation = {
        RiskLevel.LOW: ConfirmationLevel.NONE,
        RiskLevel.MEDIUM: ConfirmationLevel.SIMPLE,
        RiskLevel.HIGH: ConfirmationLevel.EXPLICIT,
        RiskLevel.CRITICAL: ConfirmationLevel.TYPE_TARGET,
    }[risk]
    return OperationPlan(
        operation=operation,
        target=target,
        environment=EnvironmentName.TESTING,
        risk=risk,
        confirmation=confirmation,
        effects=(f"Apply {operation}.",),
        correlation_id=f"corr-{operation}",
    )


def _result(operation: str, target: str) -> OperationResult:
    return OperationResult(
        operation=operation,
        status=OperationStatus.SUCCEEDED,
        changed=True,
        message="Completed.",
        metadata={"target": target},
    )


class FakeRuntimeMutationService:
    def __init__(self) -> None:
        self.executed: list[tuple[str, int]] = []

    def plan_cancel_query(self, command: CancelQueryCommand) -> OperationPlan:
        return _plan(
            "runtime.query.cancel",
            f"pid:{command.pid}",
            risk=RiskLevel.MEDIUM,
        )

    def cancel_query(
        self,
        command: CancelQueryCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        assert plan is not None
        if options.dry_run:
            return plan
        assert options.approved is True
        self.executed.append(("cancel", command.pid))
        return _result(plan.operation, plan.target)

    def plan_terminate_session(
        self,
        command: TerminateSessionCommand,
    ) -> OperationPlan:
        return _plan(
            "runtime.session.terminate",
            f"pid:{command.pid}",
            risk=RiskLevel.HIGH,
        )

    def terminate_session(
        self,
        command: TerminateSessionCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        assert plan is not None
        if options.dry_run:
            return plan
        assert options.approved is True
        self.executed.append(("terminate", command.pid))
        return _result(plan.operation, plan.target)


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeRuntimeMutationService:
    service = FakeRuntimeMutationService()
    monkeypatch.setattr(
        "pydbadminkit.cli.commands.query.build_runtime_mutation_service",
        lambda *args, **kwargs: service,
    )
    monkeypatch.setattr(
        "pydbadminkit.cli.commands.session.build_runtime_mutation_service",
        lambda *args, **kwargs: service,
    )
    return service


def test_runtime_mutation_commands_execute_through_shared_pipeline(
    fake_service: FakeRuntimeMutationService,
) -> None:
    cancel = runner.invoke(
        app,
        ["--connection", "local", "--yes", "query", "cancel", "101"],
    )
    terminate = runner.invoke(
        app,
        ["--connection", "local", "--yes", "session", "terminate", "102"],
    )

    assert cancel.exit_code == 0, cancel.output
    assert terminate.exit_code == 0, terminate.output
    assert "Status: succeeded" in cancel.stdout
    assert "Status: succeeded" in terminate.stdout
    assert fake_service.executed == [("cancel", 101), ("terminate", 102)]


def test_query_cancel_dry_run_outputs_machine_plan_without_execute(
    fake_service: FakeRuntimeMutationService,
) -> None:
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--dry-run",
            "--output",
            "json",
            "query",
            "cancel",
            "101",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["operation"] == "runtime.query.cancel"
    assert parsed["target"] == "pid:101"
    assert fake_service.executed == []


@pytest.mark.parametrize(
    "command",
    [
        ["--yes", "query", "cancel", "0"],
        ["--yes", "session", "terminate", "--", "-1"],
    ],
)
def test_runtime_mutation_pid_validation_is_usage_exit(
    fake_service: FakeRuntimeMutationService,
    command: list[str],
) -> None:
    del fake_service
    result = runner.invoke(app, ["--connection", "local", *command])

    assert result.exit_code == 2
    assert "pid must be > 0" in result.output

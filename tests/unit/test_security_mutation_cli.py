"""Unit coverage for guarded Security mutation CLI commands."""

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
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.domain.security import (
    AlterRoleCommand,
    CreateRoleCommand,
    MembershipCommand,
    RelationAccessCommand,
)

pytestmark = [pytest.mark.unit, pytest.mark.security]

runner = CliRunner()


def _plan(
    operation: str,
    target: str,
    *,
    risk: RiskLevel = RiskLevel.MEDIUM,
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


class FakeMutationService:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def plan_create_role(self, command: CreateRoleCommand) -> OperationPlan:
        return _plan("security.role.create", command.name)

    def create_role(
        self,
        command: CreateRoleCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        assert plan is not None
        if options.dry_run:
            return plan
        self.executed.append("create")
        return _result(plan.operation, command.name)

    def plan_alter_role(self, command: AlterRoleCommand) -> OperationPlan:
        return _plan("security.role.alter", command.name)

    def alter_role(
        self,
        command: AlterRoleCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationResult:
        assert plan is not None
        assert options.approved is True
        self.executed.append("alter")
        return _result(plan.operation, command.name)

    def plan_drop_role(self, name: str) -> OperationPlan:
        return _plan("security.role.drop", name, risk=RiskLevel.HIGH)

    def drop_role(
        self,
        name: str,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationResult:
        assert plan is not None
        assert options.approved is True
        self.executed.append("drop")
        return _result(plan.operation, name)

    def plan_add_membership(self, command: MembershipCommand) -> OperationPlan:
        return _plan(
            "security.membership.add",
            f"{command.member}->{command.role}",
        )

    def add_membership(
        self,
        command: MembershipCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationResult:
        assert plan is not None
        assert options.approved is True
        self.executed.append("membership-add")
        return _result(plan.operation, plan.target)

    def plan_remove_membership(self, command: MembershipCommand) -> OperationPlan:
        return _plan(
            "security.membership.remove",
            f"{command.member}->{command.role}",
        )

    def remove_membership(
        self,
        command: MembershipCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationResult:
        assert plan is not None
        assert options.approved is True
        self.executed.append("membership-remove")
        return _result(plan.operation, plan.target)

    def plan_grant_access(self, command: RelationAccessCommand) -> OperationPlan:
        return _plan(
            "security.access.grant",
            f"{command.principal}:{command.object}:{command.access_type.value}",
        )

    def grant_access(
        self,
        command: RelationAccessCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationResult:
        assert plan is not None
        assert options.approved is True
        self.executed.append("grant")
        return _result(plan.operation, plan.target)

    def plan_revoke_access(self, command: RelationAccessCommand) -> OperationPlan:
        return _plan(
            "security.access.revoke",
            f"{command.principal}:{command.object}:{command.access_type.value}",
            risk=RiskLevel.HIGH,
        )

    def revoke_access(
        self,
        command: RelationAccessCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationResult:
        assert plan is not None
        assert options.approved is True
        self.executed.append("revoke")
        return _result(plan.operation, plan.target)


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeMutationService:
    service = FakeMutationService()
    monkeypatch.setattr(
        "pydbadminkit.cli.commands.role.build_security_mutation_service",
        lambda *args, **kwargs: service,
    )
    monkeypatch.setattr(
        "pydbadminkit.cli.commands.access.build_security_mutation_service",
        lambda *args, **kwargs: service,
    )
    return service


def test_role_mutation_commands_execute_through_shared_pipeline(
    fake_service: FakeMutationService,
) -> None:
    commands = (
        ["--yes", "role", "create", "app", "--login"],
        ["--yes", "role", "alter", "app", "--createdb", "enable"],
        ["--yes", "role", "membership-add", "reader", "app"],
        ["--yes", "role", "membership-remove", "reader", "app"],
        ["--yes", "role", "drop", "app"],
    )

    for command in commands:
        result = runner.invoke(app, ["--connection", "local", *command])
        assert result.exit_code == 0, result.output
        assert "Status: succeeded" in result.stdout

    assert fake_service.executed == [
        "create",
        "alter",
        "membership-add",
        "membership-remove",
        "drop",
    ]


def test_access_grant_and_revoke_commands_execute(
    fake_service: FakeMutationService,
) -> None:
    grant = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--yes",
            "access",
            "grant",
            "--role",
            "app",
            "--object",
            "public.customers",
            "--access",
            "SELECT",
        ],
    )
    revoke = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--yes",
            "access",
            "revoke",
            "--role",
            "app",
            "--object",
            "public.customers",
            "--access",
            "SELECT",
        ],
    )

    assert grant.exit_code == 0, grant.output
    assert revoke.exit_code == 0, revoke.output
    assert fake_service.executed == ["grant", "revoke"]


def test_role_create_dry_run_outputs_machine_plan_without_execute(
    fake_service: FakeMutationService,
) -> None:
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--dry-run",
            "--output",
            "json",
            "role",
            "create",
            "planned",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["operation"] == "security.role.create"
    assert parsed["target"] == "planned"
    assert fake_service.executed == []


def test_role_create_validation_error_is_usage_exit(
    fake_service: FakeMutationService,
) -> None:
    del fake_service

    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--yes",
            "role",
            "create",
            "app",
            "--connection-limit",
            "-2",
        ],
    )

    assert result.exit_code == 2
    assert "connection_limit must be >= -1" in result.output

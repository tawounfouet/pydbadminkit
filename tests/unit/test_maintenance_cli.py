"""Unit tests for PostgreSQL maintenance CLI."""

import json

import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app
from pydbadminkit.domain.common import (
    EnvironmentName,
    OperationResult,
    OperationStatus,
    QualifiedName,
    RiskLevel,
)
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    MaintenanceOperationType,
    MaintenanceProgress,
    ReindexCommand,
    VacuumCommand,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan

pytestmark = [pytest.mark.unit, pytest.mark.maintenance]

runner = CliRunner()


def _plan(operation: str, target: str, risk: RiskLevel) -> OperationPlan:
    confirmation = {
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
        effects=(f"Execute {operation}.",),
        correlation_id=f"corr-{operation}",
    )


def _result(operation: str, target: str) -> OperationResult:
    return OperationResult(
        operation=operation,
        status=OperationStatus.SUCCEEDED,
        changed=True,
        message="Completed.",
        metadata={"target": target, "duration_ms": 5},
    )


class FakeMaintenanceService:
    def __init__(self) -> None:
        self.vacuum_commands: list[VacuumCommand] = []
        self.analyze_commands: list[AnalyzeCommand] = []
        self.reindex_commands: list[ReindexCommand] = []

    def plan_vacuum(self, command: VacuumCommand) -> OperationPlan:
        target = str(command.table) if command.table is not None else "database:test"
        return _plan("maintenance.vacuum", target, RiskLevel.MEDIUM)

    def vacuum(
        self,
        command: VacuumCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        assert plan is not None
        self.vacuum_commands.append(command)
        if options.dry_run:
            return plan
        assert options.approved is True
        return _result(plan.operation, plan.target)

    def plan_analyze(self, command: AnalyzeCommand) -> OperationPlan:
        target = str(command.table) if command.table is not None else "database:test"
        return _plan("maintenance.analyze", target, RiskLevel.MEDIUM)

    def analyze(
        self,
        command: AnalyzeCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        assert plan is not None
        self.analyze_commands.append(command)
        if options.dry_run:
            return plan
        assert options.approved is True
        return _result(plan.operation, plan.target)

    def plan_reindex(self, command: ReindexCommand) -> OperationPlan:
        return _plan(
            "maintenance.reindex",
            f"{command.target_type.value}:{command.target}",
            RiskLevel.HIGH,
        )

    def reindex(
        self,
        command: ReindexCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        assert plan is not None
        self.reindex_commands.append(command)
        if options.dry_run:
            return plan
        assert options.approved is True
        return _result(plan.operation, plan.target)

    def list_vacuum_progress(self) -> tuple[MaintenanceProgress, ...]:
        return (
            MaintenanceProgress(
                operation_type=MaintenanceOperationType.VACUUM,
                pid=123,
                target=QualifiedName(schema="public", name="events"),
                phase="scanning heap",
                completed=5,
                total=10,
                percent=50.0,
            ),
        )

    def list_reindex_progress(self) -> tuple[MaintenanceProgress, ...]:
        return ()


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeMaintenanceService:
    service = FakeMaintenanceService()
    monkeypatch.setattr(
        "pydbadminkit.cli.commands.postgres.build_maintenance_service",
        lambda *args, **kwargs: service,
    )
    return service


def test_vacuum_dry_run_json(fake_service: FakeMaintenanceService) -> None:
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--dry-run",
            "--output",
            "json",
            "postgres",
            "vacuum",
            "--table",
            "public.events",
            "--analyze",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["operation"] == "maintenance.vacuum"
    assert parsed["target"] == "public.events"
    assert fake_service.vacuum_commands[0].analyze is True


def test_analyze_repeated_columns_execute(
    fake_service: FakeMaintenanceService,
) -> None:
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--yes",
            "postgres",
            "analyze",
            "--table",
            "public.events",
            "--column",
            "created_at",
            "--column",
            "payload",
        ],
    )

    assert result.exit_code == 0, result.output
    assert fake_service.analyze_commands[0].columns == (
        "created_at",
        "payload",
    )
    assert "Status: succeeded" in result.stdout


def test_reindex_requires_exactly_one_target(
    fake_service: FakeMaintenanceService,
) -> None:
    del fake_service

    missing = runner.invoke(
        app,
        ["--connection", "local", "--yes", "postgres", "reindex"],
    )
    multiple = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--yes",
            "postgres",
            "reindex",
            "--index",
            "public.events_idx",
            "--table",
            "public.events",
        ],
    )

    assert missing.exit_code == 2
    assert multiple.exit_code == 2
    assert "Choose exactly one" in missing.output
    assert "Choose exactly one" in multiple.output


def test_reindex_index_concurrently_executes(
    fake_service: FakeMaintenanceService,
) -> None:
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--yes",
            "postgres",
            "reindex",
            "--index",
            "public.events_idx",
            "--concurrently",
        ],
    )

    assert result.exit_code == 0, result.output
    assert fake_service.reindex_commands[0].concurrently is True
    assert "Status: succeeded" in result.stdout


def test_vacuum_progress_json(fake_service: FakeMaintenanceService) -> None:
    del fake_service
    result = runner.invoke(
        app,
        [
            "--connection",
            "local",
            "--output",
            "json",
            "postgres",
            "progress",
            "vacuum",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed[0]["pid"] == 123
    assert parsed[0]["operation_type"] == "vacuum"
    assert parsed[0]["percent"] == 50.0

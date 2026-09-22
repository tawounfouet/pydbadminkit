"""Guarded maintenance application service."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from pydbadminkit.domain.audit import AuditEvent, AuditEventType
from pydbadminkit.domain.common import (
    EnvironmentName,
    OperationResult,
    OperationStatus,
    RiskLevel,
)
from pydbadminkit.domain.connection import ResolvedConnectionConfig
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    MaintenanceOperation,
    MaintenanceProgress,
    ReindexCommand,
    VacuumCommand,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.errors import (
    ConfirmationRequiredError,
    PolicyDeniedError,
    PyDBAdminError,
)
from pydbadminkit.ports.audit import AuditPort
from pydbadminkit.ports.maintenance import MaintenancePort


class MaintenanceService:
    """Plan, guard, audit and execute database maintenance."""

    def __init__(
        self,
        *,
        maintenance_port: MaintenancePort,
        audit_port: AuditPort,
        config: ResolvedConnectionConfig,
    ) -> None:
        self._maintenance_port = maintenance_port
        self._audit_port = audit_port
        self._config = config

    def plan_vacuum(self, command: VacuumCommand) -> OperationPlan:
        self._maintenance_port.validate_vacuum(command)
        base_risk = RiskLevel.HIGH if command.full else RiskLevel.MEDIUM
        risk = self._escalate_for_environment(base_risk)
        target = self._target(command.table)

        effects = [f"VACUUM target '{target}'."]
        warnings: list[str] = [
            "VACUUM can generate substantial I/O and affect concurrent workloads.",
        ]
        if command.full:
            effects.append("Rewrite the target relation(s) with VACUUM FULL.")
            warnings.append(
                "VACUUM FULL requires stronger locks and can block application traffic."
            )
        if command.freeze:
            effects.append("Apply PostgreSQL FREEZE processing.")
        if command.analyze:
            effects.append("Refresh planner statistics after VACUUM.")

        return self._plan(
            operation="maintenance.vacuum",
            target=target,
            risk=risk,
            effects=tuple(effects),
            warnings=tuple(warnings),
        )

    def vacuum(
        self,
        command: VacuumCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_vacuum(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._maintenance_port.vacuum(command),
        )

    def plan_analyze(self, command: AnalyzeCommand) -> OperationPlan:
        self._maintenance_port.validate_analyze(command)
        risk = self._escalate_for_environment(RiskLevel.MEDIUM)
        target = self._target(command.table)
        effects = [f"ANALYZE target '{target}'."]
        if command.columns:
            effects.append(
                "Refresh statistics for columns: "
                + ", ".join(command.columns)
                + "."
            )
        return self._plan(
            operation="maintenance.analyze",
            target=target,
            risk=risk,
            effects=tuple(effects),
            warnings=(
                "ANALYZE samples table data and can consume CPU and I/O resources.",
            ),
        )

    def analyze(
        self,
        command: AnalyzeCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_analyze(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._maintenance_port.analyze(command),
        )

    def plan_reindex(self, command: ReindexCommand) -> OperationPlan:
        self._maintenance_port.validate_reindex(command)
        risk = self._escalate_for_environment(RiskLevel.HIGH)
        target = f"{command.target_type.value}:{command.target}"
        effects = (
            f"Rebuild {command.target_type.value} '{command.target}'.",
        )
        warnings = [
            "REINDEX can be I/O intensive and may affect application latency.",
        ]
        if command.concurrently:
            warnings.append(
                "REINDEX CONCURRENTLY reduces write blocking but performs more work "
                "and can take longer."
            )
        else:
            warnings.append(
                "Non-concurrent REINDEX can block writes on the affected relation."
            )
        return self._plan(
            operation="maintenance.reindex",
            target=target,
            risk=risk,
            effects=effects,
            warnings=tuple(warnings),
        )

    def reindex(
        self,
        command: ReindexCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_reindex(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._maintenance_port.reindex(command),
        )

    def list_vacuum_progress(self) -> tuple[MaintenanceProgress, ...]:
        """Return currently visible VACUUM progress."""

        return self._maintenance_port.list_vacuum_progress()

    def list_reindex_progress(self) -> tuple[MaintenanceProgress, ...]:
        """Return currently visible REINDEX progress."""

        return self._maintenance_port.list_reindex_progress()

    def _execute(
        self,
        plan: OperationPlan,
        options: MutationOptions,
        action: Callable[[], MaintenanceOperation],
    ) -> OperationPlan | OperationResult:
        if options.dry_run:
            return plan

        try:
            self._enforce_profile_policy()
            self._enforce_approval(plan, options)
        except PyDBAdminError as error:
            self._audit(
                plan,
                AuditEventType.BLOCKED,
                OperationStatus.BLOCKED,
                str(error),
            )
            raise

        self._audit(
            plan,
            AuditEventType.STARTED,
            OperationStatus.RUNNING,
        )
        try:
            operation = action()
        except PyDBAdminError as error:
            self._audit(
                plan,
                AuditEventType.FAILED,
                OperationStatus.FAILED,
                str(error),
            )
            raise
        except Exception as error:
            self._audit(
                plan,
                AuditEventType.FAILED,
                OperationStatus.FAILED,
                str(error),
            )
            raise

        self._audit(
            plan,
            AuditEventType.SUCCEEDED,
            OperationStatus.SUCCEEDED,
        )
        return OperationResult(
            operation=plan.operation,
            status=OperationStatus.SUCCEEDED,
            changed=True,
            message=operation.message or f"{plan.operation} completed.",
            metadata={
                "target": plan.target,
                "risk": plan.risk.label,
                "duration_ms": operation.duration_ms,
                "correlation_id": plan.correlation_id,
            },
        )

    def _enforce_profile_policy(self) -> None:
        if self._config.read_only:
            raise PolicyDeniedError(
                "Maintenance is blocked by the read-only connection profile."
            )
        if self._config.environment is EnvironmentName.UNKNOWN:
            raise PolicyDeniedError(
                "Maintenance is blocked when the connection environment is unknown."
            )

    @staticmethod
    def _enforce_approval(
        plan: OperationPlan,
        options: MutationOptions,
    ) -> None:
        if plan.confirmation is ConfirmationLevel.NONE:
            return
        if plan.confirmation is ConfirmationLevel.TYPE_TARGET:
            if options.confirmed_target != plan.target:
                raise ConfirmationRequiredError(
                    f"Typed target confirmation required: '{plan.target}'."
                )
            return
        if not options.approved:
            raise ConfirmationRequiredError(
                f"Explicit approval required for {plan.risk.label}-risk operation."
            )

    def _plan(
        self,
        *,
        operation: str,
        target: str,
        risk: RiskLevel,
        effects: tuple[str, ...],
        warnings: tuple[str, ...],
    ) -> OperationPlan:
        production_warning = (
            ("Target connection is classified as production.",)
            if self._config.environment is EnvironmentName.PRODUCTION
            else ()
        )
        return OperationPlan(
            operation=operation,
            target=target,
            environment=self._config.environment,
            risk=risk,
            confirmation=_confirmation_for_risk(risk),
            effects=effects,
            warnings=production_warning + warnings,
            correlation_id=str(uuid4()),
        )

    def _target(self, relation: object | None) -> str:
        if relation is None:
            return f"database:{self._config.database}"
        return str(relation)

    def _audit(
        self,
        plan: OperationPlan,
        event_type: AuditEventType,
        status: OperationStatus,
        message: str | None = None,
    ) -> None:
        self._audit_port.write(
            AuditEvent(
                event_id=str(uuid4()),
                event_type=event_type,
                timestamp=datetime.now(UTC),
                actor=self._config.username,
                profile=str(self._config.name),
                environment=self._config.environment,
                database=self._config.database,
                operation=plan.operation,
                target=plan.target,
                risk=plan.risk,
                status=status,
                correlation_id=plan.correlation_id,
                message=message,
            )
        )

    def _escalate_for_environment(self, risk: RiskLevel) -> RiskLevel:
        if self._config.environment is not EnvironmentName.PRODUCTION:
            return risk
        if risk is RiskLevel.MEDIUM:
            return RiskLevel.HIGH
        if risk is RiskLevel.HIGH:
            return RiskLevel.CRITICAL
        return risk


def _confirmation_for_risk(risk: RiskLevel) -> ConfirmationLevel:
    if risk is RiskLevel.LOW:
        return ConfirmationLevel.NONE
    if risk is RiskLevel.MEDIUM:
        return ConfirmationLevel.SIMPLE
    if risk is RiskLevel.HIGH:
        return ConfirmationLevel.EXPLICIT
    return ConfirmationLevel.TYPE_TARGET

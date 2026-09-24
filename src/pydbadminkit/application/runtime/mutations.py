"""Guarded runtime mutation application service."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from pydbadminkit.domain.audit import AuditEvent, AuditEventType
from pydbadminkit.domain.common import (
    EnvironmentName,
    OperationName,
    OperationResult,
    OperationStatus,
    RiskLevel,
)
from pydbadminkit.domain.connection import ResolvedConnectionConfig
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
    PyDBAdminError,
    ResourceNotFoundError,
)
from pydbadminkit.ports.audit import AuditPort
from pydbadminkit.ports.runtime_mutation import RuntimeMutationPort


class RuntimeMutationService:
    """Plan, guard, audit and execute Runtime mutations."""

    def __init__(
        self,
        mutation_port: RuntimeMutationPort,
        audit_port: AuditPort,
        config: ResolvedConnectionConfig,
    ) -> None:
        self._mutation_port = mutation_port
        self._audit_port = audit_port
        self._config = config

    def plan_cancel_query(self, command: CancelQueryCommand) -> OperationPlan:
        risk = self._escalate_for_environment(RiskLevel.MEDIUM)
        return self._plan(
            operation=OperationName.RUNTIME_QUERY_CANCEL,
            target=f"pid:{command.pid}",
            risk=risk,
            effects=(f"Request cancellation of the query on backend PID {command.pid}.",),
            warnings=(
                "The backend session remains connected after a successful cancellation.",
                "A cancelled statement can leave its transaction requiring rollback.",
            ),
        )

    def cancel_query(
        self,
        command: CancelQueryCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_cancel_query(command)
        return self._execute(
            resolved_plan,
            options,
            command.pid,
            lambda: self._mutation_port.cancel_query(command),
            require_active_query=True,
        )

    def plan_terminate_session(self, command: TerminateSessionCommand) -> OperationPlan:
        risk = self._escalate_for_environment(RiskLevel.HIGH)
        return self._plan(
            operation=OperationName.RUNTIME_SESSION_TERMINATE,
            target=f"pid:{command.pid}",
            risk=risk,
            effects=(f"Terminate client backend session PID {command.pid}.",),
            warnings=(
                "The target client will be disconnected.",
                "Any active transaction on the target session will be rolled back.",
            ),
        )

    def terminate_session(
        self,
        command: TerminateSessionCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_terminate_session(command)
        return self._execute(
            resolved_plan,
            options,
            command.pid,
            lambda: self._mutation_port.terminate_session(command),
            require_active_query=False,
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

    def _execute(
        self,
        plan: OperationPlan,
        options: MutationOptions,
        pid: int,
        action: Callable[[], BackendSignalResult],
        *,
        require_active_query: bool,
    ) -> OperationPlan | OperationResult:
        if options.dry_run:
            return plan

        try:
            self._enforce_profile_policy()
            self._enforce_approval(plan, options)
        except PyDBAdminError as error:
            self._audit(plan, AuditEventType.BLOCKED, OperationStatus.BLOCKED, str(error))
            raise

        self._audit(plan, AuditEventType.STARTED, OperationStatus.RUNNING)
        try:
            signal = action()
            self._enforce_signal_result(
                signal,
                require_active_query=require_active_query,
            )
        except PolicyDeniedError as error:
            self._audit(plan, AuditEventType.BLOCKED, OperationStatus.BLOCKED, str(error))
            raise
        except PyDBAdminError as error:
            self._audit(plan, AuditEventType.FAILED, OperationStatus.FAILED, str(error))
            raise
        except Exception as error:
            self._audit(plan, AuditEventType.FAILED, OperationStatus.FAILED, str(error))
            raise

        self._audit(plan, AuditEventType.SUCCEEDED, OperationStatus.SUCCEEDED)
        return OperationResult(
            operation=plan.operation,
            status=OperationStatus.SUCCEEDED,
            changed=True,
            message=f"{plan.operation} completed for backend PID {pid}.",
            metadata={
                "target": plan.target,
                "pid": pid,
                "risk": plan.risk.label,
                "correlation_id": plan.correlation_id,
                "backend_type": signal.backend_type,
            },
        )

    def _enforce_profile_policy(self) -> None:
        if self._config.read_only:
            raise PolicyDeniedError("Mutation blocked by read-only connection profile.")
        if self._config.environment is EnvironmentName.UNKNOWN:
            raise PolicyDeniedError(
                "Mutation blocked because the connection environment is unknown."
            )

    @staticmethod
    def _enforce_signal_result(
        signal: BackendSignalResult,
        *,
        require_active_query: bool,
    ) -> None:
        if not signal.target_exists:
            raise ResourceNotFoundError(
                f"Backend PID {signal.pid} was not found or is no longer visible."
            )
        if signal.self_target:
            raise PolicyDeniedError(
                "Signaling the PyDBAdminKit execution backend itself is blocked."
            )
        if not signal.client_backend:
            target_type = signal.backend_type or "unknown"
            raise PolicyDeniedError(
                f"Runtime mutation is restricted to client backends; got '{target_type}'."
            )
        if require_active_query and signal.active_query is not True:
            raise PolicyDeniedError(
                "Query cancellation requires a client backend with an active query."
            )
        if not signal.changed:
            raise DatabaseOperationError(
                f"PostgreSQL did not deliver the signal to backend PID {signal.pid}."
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

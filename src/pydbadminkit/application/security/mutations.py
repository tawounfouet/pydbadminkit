"""Guarded security mutation application service."""

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
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.domain.security import (
    AlterRoleCommand,
    CreateRoleCommand,
    MembershipCommand,
    RelationAccessCommand,
)
from pydbadminkit.errors import (
    ConfirmationRequiredError,
    PolicyDeniedError,
    PyDBAdminError,
)
from pydbadminkit.ports.audit import AuditPort
from pydbadminkit.ports.security_mutation import SecurityMutationPort


class SecurityMutationService:
    """Plan, guard, audit and execute Security mutations."""

    def __init__(
        self,
        mutation_port: SecurityMutationPort,
        audit_port: AuditPort,
        config: ResolvedConnectionConfig,
    ) -> None:
        self._mutation_port = mutation_port
        self._audit_port = audit_port
        self._config = config

    def plan_create_role(self, command: CreateRoleCommand) -> OperationPlan:
        risk = _role_create_risk(command)
        risk = self._escalate_for_environment(risk)
        return self._plan(
            operation="security.role.create",
            target=command.name,
            risk=risk,
            effects=(f"Create role '{command.name}'.",),
            warnings=_privileged_role_warnings(command),
        )

    def create_role(
        self,
        command: CreateRoleCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_create_role(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._mutation_port.create_role(command),
        )

    def plan_alter_role(self, command: AlterRoleCommand) -> OperationPlan:
        risk = _role_alter_risk(command)
        risk = self._escalate_for_environment(risk)
        changed = _altered_role_attributes(command)
        return self._plan(
            operation="security.role.alter",
            target=command.name,
            risk=risk,
            effects=(f"Alter role attributes: {', '.join(changed)}.",),
            warnings=(
                ("Role attributes can change effective authorization immediately.",)
                if risk >= RiskLevel.HIGH
                else ()
            ),
        )

    def alter_role(
        self,
        command: AlterRoleCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_alter_role(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._mutation_port.alter_role(command),
        )

    def plan_drop_role(self, name: str) -> OperationPlan:
        risk = (
            RiskLevel.CRITICAL
            if self._config.environment is EnvironmentName.PRODUCTION
            else RiskLevel.HIGH
        )
        return self._plan(
            operation="security.role.drop",
            target=name,
            risk=risk,
            effects=(f"Drop role '{name}'.",),
            warnings=("Dropping a role is destructive and may fail while dependencies remain.",),
        )

    def drop_role(
        self,
        name: str,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_drop_role(name)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._mutation_port.drop_role(name),
            protected_role=name,
            destructive=True,
        )

    def plan_add_membership(self, command: MembershipCommand) -> OperationPlan:
        base = RiskLevel.HIGH if command.admin_option else RiskLevel.MEDIUM
        return self._plan(
            operation="security.membership.add",
            target=f"{command.member}->{command.role}",
            risk=self._escalate_for_environment(base),
            effects=(f"Add role '{command.member}' to '{command.role}'.",),
            warnings=(
                ("ADMIN OPTION allows the member to manage this membership.",)
                if command.admin_option
                else ()
            ),
        )

    def add_membership(
        self,
        command: MembershipCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_add_membership(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._mutation_port.add_membership(command),
        )

    def plan_remove_membership(self, command: MembershipCommand) -> OperationPlan:
        return self._plan(
            operation="security.membership.remove",
            target=f"{command.member}->{command.role}",
            risk=self._escalate_for_environment(RiskLevel.MEDIUM),
            effects=(f"Remove role '{command.member}' from '{command.role}'.",),
        )

    def remove_membership(
        self,
        command: MembershipCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_remove_membership(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._mutation_port.remove_membership(command),
        )

    def plan_grant_access(self, command: RelationAccessCommand) -> OperationPlan:
        base = RiskLevel.HIGH if command.grant_option else RiskLevel.MEDIUM
        return self._plan_relation_access(
            command,
            operation="security.access.grant",
            verb="Grant",
            base_risk=base,
        )

    def grant_access(
        self,
        command: RelationAccessCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_grant_access(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._mutation_port.grant_access(command),
        )

    def plan_revoke_access(self, command: RelationAccessCommand) -> OperationPlan:
        return self._plan_relation_access(
            command,
            operation="security.access.revoke",
            verb="Revoke",
            base_risk=RiskLevel.HIGH,
        )

    def revoke_access(
        self,
        command: RelationAccessCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | OperationResult:
        resolved_plan = plan or self.plan_revoke_access(command)
        return self._execute(
            resolved_plan,
            options,
            lambda: self._mutation_port.revoke_access(command),
        )

    def _plan_relation_access(
        self,
        command: RelationAccessCommand,
        *,
        operation: str,
        verb: str,
        base_risk: RiskLevel,
    ) -> OperationPlan:
        relation = str(command.object)
        target = f"{command.principal}:{relation}:{command.access_type.value}"
        return self._plan(
            operation=operation,
            target=target,
            risk=self._escalate_for_environment(base_risk),
            effects=(
                f"{verb} {command.access_type.value} on '{relation}' for '{command.principal}'.",
            ),
            warnings=(
                ("WITH GRANT OPTION delegates privilege management.",)
                if command.grant_option
                else ()
            ),
        )

    def _plan(
        self,
        *,
        operation: str,
        target: str,
        risk: RiskLevel,
        effects: tuple[str, ...],
        warnings: tuple[str, ...] = (),
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
        action: Callable[[], None],
        *,
        protected_role: str | None = None,
        destructive: bool = False,
    ) -> OperationPlan | OperationResult:
        if options.dry_run:
            return plan

        try:
            self._enforce_policy(plan, protected_role=protected_role, destructive=destructive)
            self._enforce_approval(plan, options)
        except PyDBAdminError as error:
            self._audit(plan, AuditEventType.BLOCKED, OperationStatus.BLOCKED, str(error))
            raise

        self._audit(plan, AuditEventType.STARTED, OperationStatus.RUNNING)
        try:
            action()
        except Exception as error:
            self._audit(plan, AuditEventType.FAILED, OperationStatus.FAILED, str(error))
            raise

        self._audit(plan, AuditEventType.SUCCEEDED, OperationStatus.SUCCEEDED)
        return OperationResult(
            operation=plan.operation,
            status=OperationStatus.SUCCEEDED,
            changed=True,
            message=f"{plan.operation} completed for '{plan.target}'.",
            metadata={
                "target": plan.target,
                "risk": plan.risk.label,
                "correlation_id": plan.correlation_id,
            },
        )

    def _enforce_policy(
        self,
        plan: OperationPlan,
        *,
        protected_role: str | None,
        destructive: bool,
    ) -> None:
        if self._config.read_only:
            raise PolicyDeniedError("Mutation blocked by read-only connection profile.")
        if self._config.environment is EnvironmentName.UNKNOWN:
            raise PolicyDeniedError(
                "Mutation blocked because the connection environment is unknown."
            )
        if protected_role is not None:
            if protected_role.startswith("pg_"):
                raise PolicyDeniedError(
                    "Built-in PostgreSQL roles are protected from this operation."
                )
            if destructive and protected_role == self._config.username:
                raise PolicyDeniedError("Dropping the current connection role is blocked.")
        if plan.target.startswith("pg_") and plan.operation.startswith("security.role."):
            raise PolicyDeniedError("Built-in PostgreSQL role namespace is protected.")

    def _enforce_approval(
        self,
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


def _role_create_risk(command: CreateRoleCommand) -> RiskLevel:
    if command.is_superuser or command.bypass_rls:
        return RiskLevel.CRITICAL
    if command.can_create_role or command.can_replicate or command.can_create_db:
        return RiskLevel.HIGH
    return RiskLevel.MEDIUM


def _role_alter_risk(command: AlterRoleCommand) -> RiskLevel:
    if command.is_superuser is True or command.bypass_rls is True:
        return RiskLevel.CRITICAL
    elevated = (
        command.can_create_role is not None
        or command.can_replicate is not None
        or command.can_create_db is not None
    )
    if elevated:
        return RiskLevel.HIGH
    return RiskLevel.MEDIUM


def _altered_role_attributes(command: AlterRoleCommand) -> tuple[str, ...]:
    names = (
        "can_login",
        "is_superuser",
        "can_create_db",
        "can_create_role",
        "can_replicate",
        "inherit",
        "bypass_rls",
        "connection_limit",
    )
    return tuple(name for name in names if getattr(command, name) is not None)


def _privileged_role_warnings(command: CreateRoleCommand) -> tuple[str, ...]:
    elevated = []
    if command.is_superuser:
        elevated.append("SUPERUSER")
    if command.bypass_rls:
        elevated.append("BYPASSRLS")
    if command.can_create_role:
        elevated.append("CREATEROLE")
    if command.can_replicate:
        elevated.append("REPLICATION")
    if command.can_create_db:
        elevated.append("CREATEDB")
    if not elevated:
        return ()
    return (f"Elevated role attributes requested: {', '.join(elevated)}.",)

"""Backup application services."""

from datetime import UTC, datetime
from uuid import uuid4

from pydbadminkit.domain.audit import AuditEvent, AuditEventType
from pydbadminkit.domain.common import (
    EnvironmentName,
    OperationName,
    OperationStatus,
    RiskLevel,
)
from pydbadminkit.domain.connection import ResolvedConnectionConfig
from pydbadminkit.domain.operations import Backup, BackupValidation, CreateBackupCommand
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.errors import (
    ConfirmationRequiredError,
    PolicyDeniedError,
    PyDBAdminError,
)
from pydbadminkit.ports.audit import AuditPort
from pydbadminkit.ports.backup import BackupPort
from pydbadminkit.ports.backup_files import BackupFileStorePort


class BackupService:
    """Plan, audit and execute logical backup creation."""

    def __init__(
        self,
        *,
        backup_port: BackupPort,
        audit_port: AuditPort,
        config: ResolvedConnectionConfig,
    ) -> None:
        self._backup_port = backup_port
        self._audit_port = audit_port
        self._config = config

    def plan_create_backup(self, command: CreateBackupCommand) -> OperationPlan:
        risk = self._risk_for(command)
        warnings: list[str] = []
        if self._config.environment is EnvironmentName.PRODUCTION:
            warnings.append(
                "Backup output may contain production-sensitive data and must be protected."
            )
        if command.force:
            warnings.append("Existing backup artifact and metadata may be replaced.")

        return OperationPlan(
            operation=OperationName.BACKUP_CREATE,
            target=command.output_path,
            environment=self._config.environment,
            risk=risk,
            confirmation=_confirmation_for_risk(risk),
            effects=(
                f"Create a {command.format.value} logical backup of database '{command.database}'.",
                f"Write backup artifact to '{command.output_path}'.",
            ),
            warnings=tuple(warnings),
            correlation_id=str(uuid4()),
        )

    def create_backup(
        self,
        command: CreateBackupCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | Backup:
        resolved_plan = plan or self.plan_create_backup(command)
        if options.dry_run:
            return resolved_plan

        try:
            self._enforce_policy(command)
            self._enforce_approval(resolved_plan, options)
        except PyDBAdminError as error:
            self._audit(
                resolved_plan,
                AuditEventType.BLOCKED,
                OperationStatus.BLOCKED,
                str(error),
            )
            raise

        self._audit(
            resolved_plan,
            AuditEventType.STARTED,
            OperationStatus.RUNNING,
        )
        try:
            backup = self._backup_port.create_backup(command)
        except PyDBAdminError as error:
            self._audit(
                resolved_plan,
                AuditEventType.FAILED,
                OperationStatus.FAILED,
                str(error),
            )
            raise
        except Exception as error:
            self._audit(
                resolved_plan,
                AuditEventType.FAILED,
                OperationStatus.FAILED,
                str(error),
            )
            raise

        self._audit(
            resolved_plan,
            AuditEventType.SUCCEEDED,
            OperationStatus.SUCCEEDED,
        )
        return backup

    def _enforce_policy(self, command: CreateBackupCommand) -> None:
        if command.force and self._config.environment is EnvironmentName.UNKNOWN:
            raise PolicyDeniedError(
                "Forced backup overwrite is blocked when the environment is unknown."
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

    def _risk_for(self, command: CreateBackupCommand) -> RiskLevel:
        if not command.force:
            return RiskLevel.LOW
        if self._config.environment is EnvironmentName.PRODUCTION:
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

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


class BackupValidationService:
    """Load and validate backup artifacts without requiring a database connection."""

    def __init__(
        self,
        *,
        backup_port: BackupPort,
        file_store: BackupFileStorePort,
    ) -> None:
        self._backup_port = backup_port
        self._file_store = file_store

    def validate_backup(
        self,
        path: str,
        *,
        timeout_seconds: float | None = None,
    ) -> BackupValidation:
        backup = self._file_store.load_backup(path)
        return self._backup_port.validate_backup(
            backup,
            timeout_seconds=timeout_seconds,
        )


def _confirmation_for_risk(risk: RiskLevel) -> ConfirmationLevel:
    if risk is RiskLevel.LOW:
        return ConfirmationLevel.NONE
    if risk is RiskLevel.MEDIUM:
        return ConfirmationLevel.SIMPLE
    if risk is RiskLevel.HIGH:
        return ConfirmationLevel.EXPLICIT
    return ConfirmationLevel.TYPE_TARGET

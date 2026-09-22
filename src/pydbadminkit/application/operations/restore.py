"""Restore application service."""

from datetime import UTC, datetime
from uuid import uuid4

from pydbadminkit.domain.audit import AuditEvent, AuditEventType
from pydbadminkit.domain.common import EnvironmentName, OperationStatus, RiskLevel
from pydbadminkit.domain.connection import ResolvedConnectionConfig
from pydbadminkit.domain.operations import (
    Backup,
    RestoreBackupCommand,
    RestoreOperation,
)
from pydbadminkit.domain.safety import ConfirmationLevel, MutationOptions, OperationPlan
from pydbadminkit.errors import (
    BackupValidationError,
    ConfirmationRequiredError,
    PolicyDeniedError,
    PyDBAdminError,
    RestoreValidationError,
)
from pydbadminkit.ports.audit import AuditPort
from pydbadminkit.ports.backup import BackupPort
from pydbadminkit.ports.backup_files import BackupFileStorePort
from pydbadminkit.ports.restore import RestorePort


class RestoreService:
    """Preflight, plan, audit and execute logical restores."""

    def __init__(
        self,
        *,
        restore_port: RestorePort,
        backup_port: BackupPort,
        file_store: BackupFileStorePort,
        audit_port: AuditPort,
        config: ResolvedConnectionConfig,
    ) -> None:
        self._restore_port = restore_port
        self._backup_port = backup_port
        self._file_store = file_store
        self._audit_port = audit_port
        self._config = config

    def plan_restore(self, command: RestoreBackupCommand) -> OperationPlan:
        backup = self._load_validated_backup(command)
        validation = self._restore_port.validate_restore(command, backup)
        if not validation.valid:
            raise RestoreValidationError("; ".join(validation.errors))

        risk = (
            RiskLevel.CRITICAL
            if self._config.environment is EnvironmentName.PRODUCTION
            else RiskLevel.HIGH
        )
        effects = [
            f"Restore '{backup.path}' into database '{command.target_database}'.",
        ]
        if command.create:
            effects.insert(0, f"Create database '{command.target_database}'.")
        if command.clean:
            effects.insert(
                0,
                f"Drop archive-owned objects in '{command.target_database}' before restore.",
            )

        warnings = list(validation.warnings)
        if validation.target_exists:
            warnings.append(f"Target database '{command.target_database}' already exists.")
        if command.create:
            warnings.append(
                "If restore fails after target creation, the partial target database is retained."
            )
        if self._config.environment is EnvironmentName.PRODUCTION:
            warnings.append("Production restore requires exact typed-target confirmation.")

        return OperationPlan(
            operation="backup.restore",
            target=command.target_database,
            environment=self._config.environment,
            risk=risk,
            confirmation=_confirmation_for_risk(risk),
            effects=tuple(effects),
            warnings=tuple(warnings),
            correlation_id=str(uuid4()),
        )

    def restore(
        self,
        command: RestoreBackupCommand,
        options: MutationOptions,
        *,
        plan: OperationPlan | None = None,
    ) -> OperationPlan | RestoreOperation:
        resolved_plan = plan or self.plan_restore(command)
        if options.dry_run:
            return resolved_plan

        try:
            self._enforce_policy()
            self._enforce_approval(resolved_plan, options)
        except PyDBAdminError as error:
            self._audit(
                resolved_plan,
                AuditEventType.BLOCKED,
                OperationStatus.BLOCKED,
                str(error),
            )
            raise

        backup = self._load_validated_backup(command)
        self._audit(
            resolved_plan,
            AuditEventType.STARTED,
            OperationStatus.RUNNING,
        )
        try:
            outcome = self._restore_port.restore_backup(command, backup)
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
        return outcome

    def _load_validated_backup(self, command: RestoreBackupCommand) -> Backup:
        backup = self._file_store.load_backup(command.backup_path)
        validation = self._backup_port.validate_backup(
            backup,
            timeout_seconds=command.timeout_seconds,
        )
        if not validation.valid:
            raise BackupValidationError("; ".join(validation.errors))
        return backup

    def _enforce_policy(self) -> None:
        if self._config.read_only:
            raise PolicyDeniedError("Restore is blocked by the read-only connection profile.")
        if self._config.environment is EnvironmentName.UNKNOWN:
            raise PolicyDeniedError(
                "Restore is blocked when the connection environment is unknown."
            )

    @staticmethod
    def _enforce_approval(
        plan: OperationPlan,
        options: MutationOptions,
    ) -> None:
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


def _confirmation_for_risk(risk: RiskLevel) -> ConfirmationLevel:
    if risk is RiskLevel.CRITICAL:
        return ConfirmationLevel.TYPE_TARGET
    return ConfirmationLevel.EXPLICIT

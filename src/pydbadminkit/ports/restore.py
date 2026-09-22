"""Restore application port."""

from typing import Protocol

from pydbadminkit.domain.operations import (
    Backup,
    RestoreBackupCommand,
    RestoreOperation,
    RestoreValidation,
)


class RestorePort(Protocol):
    """Engine-specific logical restore contract."""

    def validate_restore(
        self,
        command: RestoreBackupCommand,
        backup: Backup,
    ) -> RestoreValidation:
        """Validate restore compatibility, tooling and target state."""
        ...

    def restore_backup(
        self,
        command: RestoreBackupCommand,
        backup: Backup,
    ) -> RestoreOperation:
        """Execute and verify one logical restore."""
        ...

"""Backup application port."""

from typing import Protocol

from pydbadminkit.domain.operations import (
    Backup,
    BackupValidation,
    CreateBackupCommand,
)


class BackupPort(Protocol):
    """Engine-specific logical backup contract."""

    def create_backup(self, command: CreateBackupCommand) -> Backup:
        """Create one logical backup artifact."""
        ...

    def validate_backup(
        self,
        backup: Backup,
        *,
        timeout_seconds: float | None = None,
    ) -> BackupValidation:
        """Validate one existing backup with engine-native tooling when useful."""
        ...

"""Backup filesystem port."""

from typing import Protocol

from pydbadminkit.domain.operations import (
    Backup,
    BackupArtifactInfo,
    BackupMetadata,
    BackupPaths,
)


class BackupFileStorePort(Protocol):
    """Secret-safe filesystem operations for logical backup artifacts."""

    def prepare(self, output_path: str, *, force: bool) -> BackupPaths:
        """Validate destination paths before a native backup process starts."""
        ...

    def secure_artifact(self, path: str) -> None:
        """Apply restrictive local permissions when supported."""
        ...

    def inspect(self, path: str) -> BackupArtifactInfo:
        """Inspect one backup artifact."""
        ...

    def sha256(self, path: str) -> str:
        """Compute SHA-256 for one backup artifact."""
        ...

    def finalize(
        self,
        paths: BackupPaths,
        metadata: BackupMetadata,
        *,
        force: bool,
    ) -> None:
        """Commit artifact and metadata from temporary paths."""
        ...

    def cleanup_temporary(self, paths: BackupPaths) -> None:
        """Remove temporary artifacts after failure."""
        ...

    def load_backup(self, path: str) -> Backup:
        """Load a backup from its artifact and metadata sidecar."""
        ...

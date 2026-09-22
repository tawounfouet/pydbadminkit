"""Maintenance application port."""

from typing import Protocol

from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    MaintenanceOperation,
    MaintenanceProgress,
    ReindexCommand,
    VacuumCommand,
)


class MaintenancePort(Protocol):
    """Engine-specific database maintenance contract."""

    def validate_vacuum(self, command: VacuumCommand) -> None:
        """Validate VACUUM target and options without mutation."""
        ...

    def validate_analyze(self, command: AnalyzeCommand) -> None:
        """Validate ANALYZE target and options without mutation."""
        ...

    def validate_reindex(self, command: ReindexCommand) -> None:
        """Validate REINDEX target and options without mutation."""
        ...

    def vacuum(self, command: VacuumCommand) -> MaintenanceOperation:
        """Execute VACUUM."""
        ...

    def analyze(self, command: AnalyzeCommand) -> MaintenanceOperation:
        """Execute ANALYZE."""
        ...

    def reindex(self, command: ReindexCommand) -> MaintenanceOperation:
        """Execute REINDEX."""
        ...

    def list_vacuum_progress(self) -> tuple[MaintenanceProgress, ...]:
        """Return currently visible VACUUM progress."""
        ...

    def list_reindex_progress(self) -> tuple[MaintenanceProgress, ...]:
        """Return currently visible REINDEX progress."""
        ...

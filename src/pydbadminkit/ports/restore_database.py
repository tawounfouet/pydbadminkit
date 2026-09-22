"""Restore target database port."""

from typing import Protocol


class RestoreDatabasePort(Protocol):
    """Inspect, create and verify a restore target database."""

    def target_exists(self, name: str) -> bool:
        """Return whether the target database currently exists."""
        ...

    def create_target(self, name: str) -> None:
        """Create one empty target database."""
        ...

    def verify_target(self, name: str) -> bool:
        """Verify connectivity and basic catalog presence after restore."""
        ...

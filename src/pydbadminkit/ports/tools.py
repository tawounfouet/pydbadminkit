"""External tool resolution port."""

from typing import Protocol

from pydbadminkit.domain.operations import ExternalTool


class ToolResolverPort(Protocol):
    """Resolve native PostgreSQL utilities from the local system."""

    def resolve(self, name: str) -> ExternalTool:
        """Resolve one executable and its version."""
        ...

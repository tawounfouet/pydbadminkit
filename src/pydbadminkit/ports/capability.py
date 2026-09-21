"""Capability discovery port."""

from typing import Protocol

from pydbadminkit.domain.common.capabilities import CapabilityStatus


class CapabilityPort(Protocol):
    """Capability discovery contract."""

    def get_capability(self, name: str) -> CapabilityStatus:
        """Return the status of one named capability."""
        ...

    def list_capabilities(self) -> tuple[CapabilityStatus, ...]:
        """Return capability statuses in deterministic name order."""
        ...

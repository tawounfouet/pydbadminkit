"""Capability application service."""

from pydbadminkit.domain.common import CapabilityStatus
from pydbadminkit.ports import CapabilityPort


class CapabilityService:
    """Application boundary for capability discovery."""

    def __init__(self, capability_port: CapabilityPort) -> None:
        self._capability_port = capability_port

    def get(self, name: str) -> CapabilityStatus:
        return self._capability_port.get_capability(name)

    def list(self) -> tuple[CapabilityStatus, ...]:
        return self._capability_port.list_capabilities()

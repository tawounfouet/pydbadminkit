"""Capability discovery models."""

from dataclasses import dataclass
from enum import StrEnum


class CapabilityAvailability(StrEnum):
    """Why a capability is or is not currently usable."""

    AVAILABLE = "available"
    UNAVAILABLE_ENGINE = "unavailable_engine"
    UNAVAILABLE_VERSION = "unavailable_version"
    UNAVAILABLE_PERMISSION = "unavailable_permission"
    UNAVAILABLE_TOOL = "unavailable_tool"
    UNAVAILABLE_EXTENSION = "unavailable_extension"
    DISABLED_BY_POLICY = "disabled_by_policy"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CapabilityStatus:
    """Current availability of a named capability."""

    name: str
    availability: CapabilityAvailability
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("capability name must not be blank")

    @property
    def available(self) -> bool:
        """Return whether the capability can currently be used."""

        return self.availability is CapabilityAvailability.AVAILABLE

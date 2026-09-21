"""Effective relation access models."""

from dataclasses import dataclass
from enum import StrEnum

from pydbadminkit.domain.common import DatabaseObjectRef
from pydbadminkit.domain.security.access import AccessType


class AccessSource(StrEnum):
    """Sources contributing to effective access."""

    DIRECT = "direct"
    INHERITED = "inherited"
    PUBLIC = "public"
    OWNER = "owner"
    SUPERUSER = "superuser"


@dataclass(frozen=True, slots=True)
class EffectiveAccess:
    """One effective relation access entry with explicit source attribution."""

    principal: str
    access_type: AccessType
    object: DatabaseObjectRef
    sources: tuple[AccessSource, ...]

    def __post_init__(self) -> None:
        if not self.principal or self.principal.isspace():
            raise ValueError("access principal must not be blank")
        if not self.sources:
            raise ValueError("effective access requires at least one source")

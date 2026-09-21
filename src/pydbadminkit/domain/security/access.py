"""Direct access security models."""

from dataclasses import dataclass
from enum import StrEnum

from pydbadminkit.domain.common import DatabaseObjectRef


class AccessType(StrEnum):
    """Initial relation access vocabulary."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRUNCATE = "TRUNCATE"
    REFERENCES = "REFERENCES"
    TRIGGER = "TRIGGER"


@dataclass(frozen=True, slots=True)
class DirectAccess:
    """One explicit relation access entry for one principal."""

    principal: str
    access_type: AccessType
    object: DatabaseObjectRef
    issuer: str | None = None
    delegable: bool = False

    def __post_init__(self) -> None:
        if not self.principal or self.principal.isspace():
            raise ValueError("access principal must not be blank")

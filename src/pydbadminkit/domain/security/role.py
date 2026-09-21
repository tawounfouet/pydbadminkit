"""Role and membership security models."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RoleInfo:
    """Immutable cross-engine role summary."""

    name: str
    can_login: bool = False
    is_superuser: bool = False
    can_create_db: bool = False
    can_create_role: bool = False
    can_replicate: bool = False
    inherit: bool = True
    connection_limit: int | None = None
    valid_until: datetime | None = None
    bypass_rls: bool = False
    is_system: bool = False

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("role name must not be blank")
        if self.connection_limit is not None and self.connection_limit < -1:
            raise ValueError("connection_limit must be >= -1")


@dataclass(frozen=True, slots=True)
class RoleMembership:
    """Directed membership edge: member belongs to role."""

    role: str
    member: str
    grantor: str | None = None
    admin_option: bool = False

    def __post_init__(self) -> None:
        if not self.role or self.role.isspace():
            raise ValueError("membership role must not be blank")
        if not self.member or self.member.isspace():
            raise ValueError("membership member must not be blank")


@dataclass(frozen=True, slots=True)
class RoleDescription:
    """Detailed role view including incoming and outgoing memberships."""

    role: RoleInfo
    member_of: tuple[RoleMembership, ...] = ()
    members: tuple[RoleMembership, ...] = ()

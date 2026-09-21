"""Security mutation command models."""

from dataclasses import dataclass

from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.security.access import AccessType


@dataclass(frozen=True, slots=True)
class CreateRoleCommand:
    """Create one PostgreSQL-style role without password material."""

    name: str
    can_login: bool = False
    is_superuser: bool = False
    can_create_db: bool = False
    can_create_role: bool = False
    can_replicate: bool = False
    inherit: bool = True
    bypass_rls: bool = False
    connection_limit: int = -1

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("role name must not be blank")
        if self.connection_limit < -1:
            raise ValueError("connection_limit must be >= -1")


@dataclass(frozen=True, slots=True)
class AlterRoleCommand:
    """Alter selected role attributes."""

    name: str
    can_login: bool | None = None
    is_superuser: bool | None = None
    can_create_db: bool | None = None
    can_create_role: bool | None = None
    can_replicate: bool | None = None
    inherit: bool | None = None
    bypass_rls: bool | None = None
    connection_limit: int | None = None

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("role name must not be blank")
        if self.connection_limit is not None and self.connection_limit < -1:
            raise ValueError("connection_limit must be >= -1")
        values = (
            self.can_login,
            self.is_superuser,
            self.can_create_db,
            self.can_create_role,
            self.can_replicate,
            self.inherit,
            self.bypass_rls,
            self.connection_limit,
        )
        if all(value is None for value in values):
            raise ValueError("at least one role attribute must be changed")


@dataclass(frozen=True, slots=True)
class MembershipCommand:
    """Add or remove one role membership."""

    role: str
    member: str
    admin_option: bool = False

    def __post_init__(self) -> None:
        if not self.role or self.role.isspace():
            raise ValueError("membership role must not be blank")
        if not self.member or self.member.isspace():
            raise ValueError("membership member must not be blank")
        if self.role == self.member:
            raise ValueError("a role cannot be a member of itself")


@dataclass(frozen=True, slots=True)
class RelationAccessCommand:
    """Grant or revoke one relation access type."""

    principal: str
    access_type: AccessType
    object: QualifiedName
    grant_option: bool = False

    def __post_init__(self) -> None:
        if not self.principal or self.principal.isspace():
            raise ValueError("access principal must not be blank")
        if self.object.database is not None:
            raise ValueError("cross-database relation access mutation is not supported")

"""Security application service."""

from pydbadminkit.domain.common import DatabaseObjectType
from pydbadminkit.domain.security import (
    DirectAccess,
    EffectiveAccess,
    OwnershipInfo,
    RoleDescription,
    RoleInfo,
    RoleMembership,
)
from pydbadminkit.ports.security import SecurityPort


class SecurityService:
    """Application boundary for read-only security inspection."""

    def __init__(self, security_port: SecurityPort) -> None:
        self._security_port = security_port

    def list_roles(
        self,
        *,
        include_system: bool = False,
        login_only: bool = False,
    ) -> tuple[RoleInfo, ...]:
        return self._security_port.list_roles(
            include_system=include_system,
            login_only=login_only,
        )

    def describe_role(self, name: str) -> RoleDescription:
        return self._security_port.describe_role(name)

    def list_role_memberships(self) -> tuple[RoleMembership, ...]:
        return self._security_port.list_role_memberships()

    def list_direct_access(
        self,
        role: str,
        *,
        schema: str | None = None,
        object_name: str | None = None,
        include_system: bool = False,
    ) -> tuple[DirectAccess, ...]:
        return self._security_port.list_direct_access(
            role,
            schema=schema,
            object_name=object_name,
            include_system=include_system,
        )

    def list_effective_access(
        self,
        role: str,
        *,
        schema: str | None = None,
        object_name: str | None = None,
        include_system: bool = False,
    ) -> tuple[EffectiveAccess, ...]:
        return self._security_port.list_effective_access(
            role,
            schema=schema,
            object_name=object_name,
            include_system=include_system,
        )

    def list_ownership(
        self,
        owner: str,
        *,
        object_type: DatabaseObjectType | None = None,
        schema: str | None = None,
        include_system: bool = False,
    ) -> tuple[OwnershipInfo, ...]:
        return self._security_port.list_ownership(
            owner,
            object_type=object_type,
            schema=schema,
            include_system=include_system,
        )

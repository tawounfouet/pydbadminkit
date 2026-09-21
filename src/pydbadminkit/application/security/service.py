"""Security application service."""

from pydbadminkit.domain.security import RoleDescription, RoleInfo, RoleMembership
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

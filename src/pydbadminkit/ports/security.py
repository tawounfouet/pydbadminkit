"""Security inspection port."""

from typing import Protocol

from pydbadminkit.domain.security import RoleDescription, RoleInfo, RoleMembership


class SecurityPort(Protocol):
    """Engine-independent security inspection contract."""

    def list_roles(
        self,
        *,
        include_system: bool = False,
        login_only: bool = False,
    ) -> tuple[RoleInfo, ...]:
        """Return visible roles in deterministic name order."""
        ...

    def describe_role(self, name: str) -> RoleDescription:
        """Return one role and its membership relationships."""
        ...

    def list_role_memberships(self) -> tuple[RoleMembership, ...]:
        """Return visible role membership edges."""
        ...

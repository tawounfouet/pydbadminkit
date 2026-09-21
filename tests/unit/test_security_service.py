"""Unit tests for the security application service."""

import pytest

from pydbadminkit.application.security import SecurityService
from pydbadminkit.domain.security import RoleDescription, RoleInfo, RoleMembership

pytestmark = pytest.mark.unit


class FakeSecurityPort:
    def list_roles(
        self,
        *,
        include_system: bool = False,
        login_only: bool = False,
    ) -> tuple[RoleInfo, ...]:
        roles = (
            RoleInfo(name="app", can_login=True),
            RoleInfo(name="reader"),
            RoleInfo(name="pg_monitor", is_system=True),
        )
        return tuple(
            role
            for role in roles
            if (include_system or not role.is_system) and (not login_only or role.can_login)
        )

    def describe_role(self, name: str) -> RoleDescription:
        return RoleDescription(
            role=RoleInfo(name=name, can_login=True),
            member_of=(RoleMembership(role="reader", member=name),),
        )

    def list_role_memberships(self) -> tuple[RoleMembership, ...]:
        return (RoleMembership(role="reader", member="app"),)


def test_security_service_delegates_role_filters() -> None:
    service = SecurityService(FakeSecurityPort())

    assert [role.name for role in service.list_roles()] == ["app", "reader"]
    assert [role.name for role in service.list_roles(login_only=True)] == ["app"]
    assert service.list_roles(include_system=True)[-1].name == "pg_monitor"


def test_security_service_describes_and_lists_memberships() -> None:
    service = SecurityService(FakeSecurityPort())

    assert service.describe_role("app").member_of[0].role == "reader"
    assert service.list_role_memberships()[0].member == "app"

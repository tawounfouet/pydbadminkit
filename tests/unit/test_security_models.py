"""Unit tests for security domain models."""

from dataclasses import FrozenInstanceError

import pytest

from pydbadminkit.domain.security import RoleDescription, RoleInfo, RoleMembership

pytestmark = pytest.mark.unit


def test_role_info_is_immutable() -> None:
    role = RoleInfo(name="reader", can_login=True)

    with pytest.raises(FrozenInstanceError):
        role.can_login = False  # type: ignore[misc]


def test_role_info_validates_name_and_connection_limit() -> None:
    with pytest.raises(ValueError):
        RoleInfo(name=" ")

    with pytest.raises(ValueError):
        RoleInfo(name="reader", connection_limit=-2)


def test_role_membership_validates_names() -> None:
    with pytest.raises(ValueError):
        RoleMembership(role="", member="app")

    with pytest.raises(ValueError):
        RoleMembership(role="reader", member=" ")


def test_role_description_uses_immutable_membership_tuples() -> None:
    membership = RoleMembership(role="reader", member="app")
    description = RoleDescription(
        role=RoleInfo(name="app"),
        member_of=(membership,),
    )

    assert description.member_of == (membership,)
    assert description.members == ()

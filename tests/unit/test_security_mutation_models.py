"""Unit tests for security mutation command models."""

import pytest

from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.security import (
    AccessType,
    AlterRoleCommand,
    CreateRoleCommand,
    MembershipCommand,
    RelationAccessCommand,
)

pytestmark = [pytest.mark.unit, pytest.mark.security]


def test_create_role_validates_name_and_limit() -> None:
    with pytest.raises(ValueError):
        CreateRoleCommand(name=" ")

    with pytest.raises(ValueError):
        CreateRoleCommand(name="app", connection_limit=-2)


def test_alter_role_requires_at_least_one_change() -> None:
    with pytest.raises(ValueError):
        AlterRoleCommand(name="app")


def test_membership_blocks_self_membership() -> None:
    with pytest.raises(ValueError):
        MembershipCommand(role="app", member="app")


def test_relation_access_blocks_cross_database_target() -> None:
    with pytest.raises(ValueError):
        RelationAccessCommand(
            principal="app",
            access_type=AccessType.SELECT,
            object=QualifiedName(database="other", schema="public", name="customers"),
        )

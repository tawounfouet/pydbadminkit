"""Unit tests for PostgreSQL security inspection."""

from datetime import UTC, datetime
from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.mappers.security import (
    map_role_info,
    map_role_membership,
)
from pydbadminkit.adapters.postgresql.security import PostgreSQLSecurityAdapter
from pydbadminkit.errors import InternalError, ResourceNotFoundError

pytestmark = [pytest.mark.unit, pytest.mark.security]


class FakeExecutor:
    def __init__(
        self,
        *,
        one_by_id: dict[str, dict[str, Any] | None] | None = None,
        many_by_id: dict[str, tuple[dict[str, Any], ...]] | None = None,
    ) -> None:
        self.one_by_id = one_by_id or {}
        self.many_by_id = many_by_id or {}
        self.calls: list[tuple[str, tuple[object, ...] | None, str]] = []

    def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> dict[str, Any] | None:
        self.calls.append((query, params, query_id))
        return self.one_by_id.get(query_id)

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> tuple[dict[str, Any], ...]:
        self.calls.append((query, params, query_id))
        return self.many_by_id.get(query_id, ())


def _role_row(name: str = "app", *, can_login: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "can_login": can_login,
        "is_superuser": False,
        "can_create_db": False,
        "can_create_role": False,
        "can_replicate": False,
        "inherit": True,
        "connection_limit": -1,
        "valid_until": datetime(2030, 1, 1, tzinfo=UTC),
        "bypass_rls": False,
    }


def _membership_row() -> dict[str, Any]:
    return {
        "role_name": "reader",
        "member_name": "app",
        "grantor_name": "postgres",
        "admin_option": False,
    }


def test_role_mapper_preserves_security_flags() -> None:
    role = map_role_info(_role_row("pg_monitor", can_login=False))

    assert role.name == "pg_monitor"
    assert role.can_login is False
    assert role.connection_limit == -1
    assert role.valid_until == datetime(2030, 1, 1, tzinfo=UTC)
    assert role.is_system is True


def test_role_mapper_rejects_invalid_boolean() -> None:
    row = _role_row()
    row["can_login"] = "yes"

    with pytest.raises(InternalError):
        map_role_info(row)


def test_membership_mapper() -> None:
    membership = map_role_membership(_membership_row())

    assert membership.role == "reader"
    assert membership.member == "app"
    assert membership.grantor == "postgres"
    assert membership.admin_option is False


def test_security_adapter_lists_roles_with_filters() -> None:
    executor = FakeExecutor(many_by_id={"PG_LIST_ROLES": (_role_row(),)})
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]

    roles = adapter.list_roles(include_system=True, login_only=True)

    assert roles[0].name == "app"
    assert executor.calls[0][1] == (True, True)


def test_security_adapter_describes_memberships_both_directions() -> None:
    memberships = (
        _membership_row(),
        {
            "role_name": "app",
            "member_name": "worker",
            "grantor_name": "postgres",
            "admin_option": True,
        },
    )
    executor = FakeExecutor(
        one_by_id={"PG_GET_ROLE": _role_row()},
        many_by_id={"PG_LIST_ROLE_MEMBERSHIPS": memberships},
    )
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]

    description = adapter.describe_role("app")

    assert description.member_of[0].role == "reader"
    assert description.members[0].member == "worker"
    assert [call[2] for call in executor.calls] == [
        "PG_GET_ROLE",
        "PG_LIST_ROLE_MEMBERSHIPS",
    ]


def test_security_adapter_missing_role() -> None:
    adapter = PostgreSQLSecurityAdapter(FakeExecutor())  # type: ignore[arg-type]

    with pytest.raises(ResourceNotFoundError):
        adapter.describe_role("missing")

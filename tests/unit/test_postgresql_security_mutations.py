"""Unit tests for PostgreSQL security mutation adapter methods."""

from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.security import PostgreSQLSecurityAdapter
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.domain.security import (
    AccessType,
    AlterRoleCommand,
    CreateRoleCommand,
    MembershipCommand,
    RelationAccessCommand,
)

pytestmark = [pytest.mark.unit, pytest.mark.security]


class FakeExecutor:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute(
        self,
        query: Any,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> int:
        del query, params
        self.calls.append(query_id)
        return 0


def test_postgresql_security_mutation_adapter_executes_all_commands() -> None:
    executor = FakeExecutor()
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]

    adapter.create_role(
        CreateRoleCommand(
            name="app",
            can_login=True,
            can_create_db=True,
            can_create_role=True,
            can_replicate=True,
            inherit=False,
            bypass_rls=True,
            connection_limit=5,
        )
    )
    adapter.alter_role(
        AlterRoleCommand(
            name="app",
            can_login=False,
            is_superuser=False,
            can_create_db=False,
            can_create_role=False,
            can_replicate=False,
            inherit=True,
            bypass_rls=False,
            connection_limit=-1,
        )
    )
    adapter.drop_role("app")
    adapter.add_membership(MembershipCommand(role="reader", member="app", admin_option=True))
    adapter.remove_membership(MembershipCommand(role="reader", member="app"))
    command = RelationAccessCommand(
        principal="app",
        access_type=AccessType.SELECT,
        object=QualifiedName(schema="public", name="customers"),
        grant_option=True,
    )
    adapter.grant_access(command)
    adapter.revoke_access(command)

    assert executor.calls == [
        "PG_CREATE_ROLE",
        "PG_ALTER_ROLE",
        "PG_DROP_ROLE",
        "PG_ADD_ROLE_MEMBERSHIP",
        "PG_REMOVE_ROLE_MEMBERSHIP",
        "PG_GRANT_RELATION_ACCESS",
        "PG_REVOKE_RELATION_ACCESS",
    ]


def test_alter_role_adapter_supports_sparse_changes() -> None:
    executor = FakeExecutor()
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]

    adapter.alter_role(AlterRoleCommand(name="app", can_login=True))

    assert executor.calls == ["PG_ALTER_ROLE"]

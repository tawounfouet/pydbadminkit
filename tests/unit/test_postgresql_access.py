"""Unit tests for PostgreSQL direct relation access."""

from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.mappers.access import map_direct_access
from pydbadminkit.adapters.postgresql.security import PostgreSQLSecurityAdapter
from pydbadminkit.domain.common import DatabaseObjectType, QualifiedName
from pydbadminkit.domain.security import AccessType
from pydbadminkit.errors import InternalError

pytestmark = [pytest.mark.unit, pytest.mark.security]


class FakeExecutor:
    def __init__(
        self,
        rows: tuple[dict[str, Any], ...],
    ) -> None:
        self.rows = rows
        self.calls: list[tuple[tuple[object, ...] | None, str]] = []

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> tuple[dict[str, Any], ...]:
        del query
        self.calls.append((params, query_id))
        return self.rows

    def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> dict[str, Any] | None:
        del query, params, query_id
        return None


def _row() -> dict[str, Any]:
    return {
        "principal": "app",
        "issuer": "postgres",
        "schema_name": "public",
        "object_name": "customers",
        "relkind": "r",
        "access_type": "SELECT",
        "delegable": False,
    }


def test_access_mapper_builds_typed_object_reference() -> None:
    entry = map_direct_access(_row())

    assert entry.principal == "app"
    assert entry.access_type is AccessType.SELECT
    assert entry.object.object_type is DatabaseObjectType.TABLE
    assert entry.object.name == QualifiedName(schema="public", name="customers")
    assert entry.issuer == "postgres"


def test_access_mapper_rejects_unknown_relation_kind() -> None:
    row = _row()
    row["relkind"] = "?"

    with pytest.raises(InternalError):
        map_direct_access(row)


def test_access_mapper_rejects_invalid_boolean() -> None:
    row = _row()
    row["delegable"] = "no"

    with pytest.raises(InternalError):
        map_direct_access(row)


def test_security_adapter_forwards_direct_access_filters() -> None:
    executor = FakeExecutor((_row(),))
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]

    entries = adapter.list_direct_access(
        "app",
        schema="public",
        object_name="customers",
    )

    assert entries[0].access_type is AccessType.SELECT
    assert executor.calls[0] == (
        (
            "app",
            False,
            "public",
            "public",
            "customers",
            "customers",
        ),
        "PG_LIST_DIRECT_RELATION_ACCESS",
    )

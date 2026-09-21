"""Unit tests for effective access and ownership inspection."""

from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.mappers.effective_access import map_effective_access
from pydbadminkit.adapters.postgresql.mappers.ownership import map_ownership
from pydbadminkit.adapters.postgresql.security import PostgreSQLSecurityAdapter
from pydbadminkit.domain.common import DatabaseObjectType
from pydbadminkit.domain.security import AccessSource, AccessType
from pydbadminkit.errors import InternalError

pytestmark = [pytest.mark.unit, pytest.mark.security]


class FakeExecutor:
    def __init__(
        self,
        rows_by_id: dict[str, tuple[dict[str, Any], ...]],
    ) -> None:
        self.rows_by_id = rows_by_id
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
        return self.rows_by_id.get(query_id, ())

    def fetch_one(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> dict[str, Any] | None:
        del query, params, query_id
        return None


def _effective_row() -> dict[str, Any]:
    return {
        "principal": "app",
        "schema_name": "public",
        "object_name": "customers",
        "relkind": "r",
        "access_type": "SELECT",
        "source_direct": True,
        "source_inherited": True,
        "source_public": False,
        "source_owner": False,
        "source_superuser": False,
    }


def test_effective_access_mapper_preserves_multiple_sources() -> None:
    entry = map_effective_access(_effective_row())

    assert entry.access_type is AccessType.SELECT
    assert entry.sources == (
        AccessSource.DIRECT,
        AccessSource.INHERITED,
    )


def test_effective_access_mapper_requires_source() -> None:
    row = _effective_row()
    for key in (
        "source_direct",
        "source_inherited",
        "source_public",
        "source_owner",
        "source_superuser",
    ):
        row[key] = False

    with pytest.raises(InternalError):
        map_effective_access(row)


def test_ownership_mapper_supports_schema_and_relation_objects() -> None:
    schema = map_ownership(
        {
            "owner": "app",
            "object_type": "schema",
            "schema_name": None,
            "object_name": "app_schema",
        }
    )
    table = map_ownership(
        {
            "owner": "app",
            "object_type": "table",
            "schema_name": "public",
            "object_name": "customers",
        }
    )

    assert schema.object.object_type is DatabaseObjectType.SCHEMA
    assert schema.object.name.name == "app_schema"
    assert table.object.object_type is DatabaseObjectType.TABLE
    assert table.object.name.schema == "public"


def test_security_adapter_forwards_effective_access_filters() -> None:
    executor = FakeExecutor(
        {"PG_LIST_EFFECTIVE_RELATION_ACCESS": (_effective_row(),)}
    )
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]

    entries = adapter.list_effective_access(
        "app",
        schema="public",
        object_name="customers",
    )

    assert entries[0].sources[0] is AccessSource.DIRECT
    assert executor.calls[0] == (
        (
            "app",
            False,
            "public",
            "public",
            "customers",
            "customers",
        ),
        "PG_LIST_EFFECTIVE_RELATION_ACCESS",
    )


def test_security_adapter_filters_ownership_type() -> None:
    executor = FakeExecutor(
        {
            "PG_LIST_OWNERSHIP": (
                {
                    "owner": "app",
                    "object_type": "table",
                    "schema_name": "public",
                    "object_name": "customers",
                },
                {
                    "owner": "app",
                    "object_type": "view",
                    "schema_name": "public",
                    "object_name": "customer_view",
                },
            )
        }
    )
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]

    entries = adapter.list_ownership(
        "app",
        object_type=DatabaseObjectType.TABLE,
        schema="public",
    )

    assert [entry.object.name.name for entry in entries] == ["customers"]
    assert executor.calls[0][1] == "PG_LIST_OWNERSHIP"

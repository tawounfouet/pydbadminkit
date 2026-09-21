"""Unit tests for PostgreSQL view and index catalog support."""

from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.catalog import PostgreSQLCatalogAdapter
from pydbadminkit.adapters.postgresql.mappers.index import (
    build_index_description,
    map_index_info,
)
from pydbadminkit.adapters.postgresql.mappers.view import (
    build_view_description,
    map_view_info,
)
from pydbadminkit.domain.catalog import ViewKind
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.errors import (
    CapabilityNotAvailableError,
    InternalError,
    ResourceNotFoundError,
)

pytestmark = pytest.mark.unit


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


def _view_row(
    name: str = "customer_view",
    *,
    relkind: str = "v",
) -> dict[str, Any]:
    return {
        "schema_name": "public",
        "name": name,
        "owner": "postgres",
        "relkind": relkind,
    }


def _column_row() -> dict[str, Any]:
    return {
        "name": "id",
        "position": 1,
        "data_type": "bigint",
        "nullable": True,
        "default_expression": None,
        "identity": False,
        "generated": False,
        "comment": None,
    }


def _index_row(name: str = "customers_email_idx") -> dict[str, Any]:
    return {
        "schema_name": "public",
        "name": name,
        "table_schema": "public",
        "table_name": "customers",
        "method": "btree",
        "owner": "postgres",
        "is_unique": True,
        "is_primary": False,
        "is_valid": True,
        "is_ready": True,
        "size_bytes": 16384,
    }


def test_view_mapper_supports_regular_and_materialized_views() -> None:
    view = map_view_info(_view_row())
    materialized = map_view_info(_view_row("customer_mv", relkind="m"))

    assert view.kind is ViewKind.VIEW
    assert materialized.kind is ViewKind.MATERIALIZED_VIEW
    assert view.name == QualifiedName(schema="public", name="customer_view")


def test_view_mapper_rejects_unknown_relkind() -> None:
    with pytest.raises(InternalError):
        map_view_info(_view_row(relkind="?"))


def test_build_view_description() -> None:
    description = build_view_description(
        _view_row(),
        (_column_row(),),
        {"definition": "SELECT id FROM public.customers;"},
    )

    assert description.view.name.name == "customer_view"
    assert description.columns[0].name == "id"
    assert description.definition == "SELECT id FROM public.customers;"


def test_index_mapper_and_description() -> None:
    index = map_index_info(_index_row())
    description = build_index_description(
        _index_row(),
        {
            "definition": (
                "CREATE UNIQUE INDEX customers_email_idx "
                "ON public.customers USING btree (email)"
            ),
            "predicate": "email IS NOT NULL",
        },
    )

    assert index.method == "btree"
    assert index.unique is True
    assert index.table == QualifiedName(schema="public", name="customers")
    assert description.predicate == "email IS NOT NULL"


def test_index_mapper_rejects_invalid_boolean() -> None:
    row = _index_row()
    row["is_valid"] = "yes"

    with pytest.raises(InternalError):
        map_index_info(row)


def test_index_description_requires_detail_row() -> None:
    with pytest.raises(InternalError):
        build_index_description(_index_row(), None)


def test_catalog_adapter_lists_and_describes_views() -> None:
    executor = FakeExecutor(
        one_by_id={
            "PG_GET_VIEW": _view_row(),
            "PG_GET_VIEW_DEFINITION": {
                "definition": "SELECT id FROM public.customers;"
            },
        },
        many_by_id={"PG_LIST_VIEWS": (_view_row(),), "PG_GET_VIEW_COLUMNS": (_column_row(),)},
    )
    adapter = PostgreSQLCatalogAdapter(executor)  # type: ignore[arg-type]

    views = adapter.list_views(schema="public")
    description = adapter.describe_view(
        QualifiedName(schema="public", name="customer_view")
    )

    assert views[0].kind is ViewKind.VIEW
    assert executor.calls[0][1] == (False, "public", "public")
    assert description.definition == "SELECT id FROM public.customers;"
    assert [call[2] for call in executor.calls[1:]] == [
        "PG_GET_VIEW",
        "PG_GET_VIEW_COLUMNS",
        "PG_GET_VIEW_DEFINITION",
    ]


def test_catalog_adapter_view_missing_and_cross_database() -> None:
    adapter = PostgreSQLCatalogAdapter(FakeExecutor())  # type: ignore[arg-type]

    with pytest.raises(ResourceNotFoundError):
        adapter.describe_view(QualifiedName(schema="public", name="missing"))

    with pytest.raises(CapabilityNotAvailableError):
        adapter.describe_view(
            QualifiedName(
                database="other",
                schema="public",
                name="customer_view",
            )
        )


def test_catalog_adapter_lists_and_describes_indexes() -> None:
    executor = FakeExecutor(
        one_by_id={
            "PG_GET_INDEX": _index_row(),
            "PG_GET_INDEX_DETAIL": {
                "definition": (
                    "CREATE UNIQUE INDEX customers_email_idx "
                    "ON public.customers USING btree (email)"
                ),
                "predicate": "email IS NOT NULL",
            },
        },
        many_by_id={"PG_LIST_INDEXES": (_index_row(),)},
    )
    adapter = PostgreSQLCatalogAdapter(executor)  # type: ignore[arg-type]

    indexes = adapter.list_indexes(schema="public", table="customers")
    description = adapter.describe_index(
        QualifiedName(schema="public", name="customers_email_idx")
    )

    assert indexes[0].unique is True
    assert executor.calls[0][1] == (
        False,
        "public",
        "public",
        "customers",
        "customers",
    )
    assert description.index.method == "btree"
    assert description.predicate == "email IS NOT NULL"
    assert [call[2] for call in executor.calls[1:]] == [
        "PG_GET_INDEX",
        "PG_GET_INDEX_DETAIL",
    ]


def test_catalog_adapter_index_missing_and_cross_database() -> None:
    adapter = PostgreSQLCatalogAdapter(FakeExecutor())  # type: ignore[arg-type]

    with pytest.raises(ResourceNotFoundError):
        adapter.describe_index(QualifiedName(schema="public", name="missing"))

    with pytest.raises(CapabilityNotAvailableError):
        adapter.describe_index(
            QualifiedName(
                database="other",
                schema="public",
                name="customers_idx",
            )
        )

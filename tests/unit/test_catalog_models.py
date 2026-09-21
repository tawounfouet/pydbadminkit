"""Unit tests for catalog read models."""

from dataclasses import FrozenInstanceError

import pytest

from pydbadminkit.domain.catalog import (
    ColumnInfo,
    ConstraintInfo,
    ConstraintType,
    DatabaseInfo,
    IndexDescription,
    IndexInfo,
    SchemaInfo,
    ServerInfo,
    TableDescription,
    TableInfo,
    ViewDescription,
    ViewInfo,
    ViewKind,
)
from pydbadminkit.domain.common import DatabaseEngine, DatabaseVersion, QualifiedName

pytestmark = pytest.mark.unit


def test_server_info_is_immutable() -> None:
    info = ServerInfo(
        engine=DatabaseEngine.POSTGRESQL,
        version=DatabaseVersion(18),
        current_database="postgres",
        current_user="postgres",
    )

    with pytest.raises(FrozenInstanceError):
        info.current_database = "other"  # type: ignore[misc]


def test_database_info_rejects_negative_size() -> None:
    with pytest.raises(ValueError):
        DatabaseInfo(name="analytics", size_bytes=-1)


def test_schema_info_rejects_blank_name() -> None:
    with pytest.raises(ValueError):
        SchemaInfo(name=" ")


def test_table_info_rejects_negative_estimate() -> None:
    with pytest.raises(ValueError):
        TableInfo(
            name=QualifiedName(schema="public", name="customers"),
            estimated_rows=-1,
        )


def test_column_position_starts_at_one() -> None:
    with pytest.raises(ValueError):
        ColumnInfo(
            name="id",
            position=0,
            data_type="bigint",
            nullable=False,
        )


def test_table_description_uses_immutable_tuples() -> None:
    table = TableInfo(name=QualifiedName(schema="public", name="customers"))
    column = ColumnInfo(
        name="id",
        position=1,
        data_type="bigint",
        nullable=False,
    )
    constraint = ConstraintInfo(
        name="customers_pkey",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("id",),
    )
    description = TableDescription(
        table=table,
        columns=(column,),
        constraints=(constraint,),
    )

    assert description.columns == (column,)
    assert description.constraints == (constraint,)


def test_view_description_uses_immutable_columns() -> None:
    view = ViewInfo(
        name=QualifiedName(schema="public", name="customer_view"),
        kind=ViewKind.MATERIALIZED_VIEW,
    )
    column = ColumnInfo(
        name="id",
        position=1,
        data_type="bigint",
        nullable=True,
    )
    description = ViewDescription(
        view=view,
        columns=(column,),
        definition="SELECT 1 AS id",
    )

    assert description.view.kind is ViewKind.MATERIALIZED_VIEW
    assert description.columns == (column,)


def test_index_info_validates_method_and_size() -> None:
    name = QualifiedName(schema="public", name="customers_idx")
    table = QualifiedName(schema="public", name="customers")

    with pytest.raises(ValueError):
        IndexInfo(name=name, table=table, method=" ")

    with pytest.raises(ValueError):
        IndexInfo(name=name, table=table, method="btree", size_bytes=-1)


def test_index_description_requires_definition() -> None:
    index = IndexInfo(
        name=QualifiedName(schema="public", name="customers_idx"),
        table=QualifiedName(schema="public", name="customers"),
        method="btree",
    )

    with pytest.raises(ValueError):
        IndexDescription(index=index, definition=" ")

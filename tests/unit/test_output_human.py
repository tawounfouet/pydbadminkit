"""Unit tests for initial human renderers."""

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
from pydbadminkit.domain.common import (
    CapabilityAvailability,
    CapabilityStatus,
    DatabaseEngine,
    DatabaseVersion,
    QualifiedName,
)
from pydbadminkit.output.human import (
    render_capability_info,
    render_capability_list,
    render_database_info,
    render_database_list,
    render_index_description,
    render_index_list,
    render_schema_info,
    render_schema_list,
    render_server_info,
    render_table_description,
    render_table_list,
    render_view_description,
    render_view_list,
)

pytestmark = pytest.mark.unit


def test_server_renderer() -> None:
    rendered = render_server_info(
        ServerInfo(
            engine=DatabaseEngine.POSTGRESQL,
            version=DatabaseVersion(18),
            current_database="postgres",
            current_user="postgres",
        )
    )
    assert "Engine: postgresql" in rendered
    assert "Version: 18" in rendered


def test_database_renderers() -> None:
    database = DatabaseInfo(
        name="analytics",
        owner="postgres",
        encoding="UTF8",
        collation="C.UTF-8",
        allow_connections=True,
        connection_limit=-1,
        size_bytes=1024,
    )

    table = render_database_list((database,))
    detail = render_database_info(database)

    assert table.startswith("NAME\tOWNER")
    assert "analytics\tpostgres\tUTF8\tyes\t1024" in table
    assert "Allow connections: yes" in detail
    assert "Connection limit: -1" in detail


def test_schema_renderers() -> None:
    public = SchemaInfo(name="public", owner="postgres")
    system = SchemaInfo(name="pg_catalog", owner="postgres", is_system=True)

    listing = render_schema_list((public, system))
    detail = render_schema_info(public)

    assert "public\tpostgres\tno" in listing
    assert "pg_catalog\tpostgres\tyes" in listing
    assert "Name: public" in detail


def test_table_renderers() -> None:
    table = TableInfo(
        name=QualifiedName(schema="public", name="customers"),
        owner="postgres",
        estimated_rows=42,
        size_bytes=8192,
    )
    description = TableDescription(
        table=table,
        columns=(
            ColumnInfo(
                name="id",
                position=1,
                data_type="bigint",
                nullable=False,
            ),
            ColumnInfo(
                name="email",
                position=2,
                data_type="text",
                nullable=False,
                default="'unknown'::text",
            ),
        ),
        constraints=(
            ConstraintInfo(
                name="customers_pkey",
                constraint_type=ConstraintType.PRIMARY_KEY,
                columns=("id",),
                definition="PRIMARY KEY (id)",
            ),
        ),
    )

    listing = render_table_list((table,))
    detail = render_table_description(description)

    assert "public.customers\tpostgres\ttable\t42\t8192" in listing
    assert "COLUMNS" in detail
    assert "1\tid\tbigint\tno" in detail
    assert "CONSTRAINTS" in detail
    assert "customers_pkey\tprimary_key\tid\tPRIMARY KEY (id)" in detail


def test_view_renderers() -> None:
    view = ViewInfo(
        name=QualifiedName(schema="public", name="customer_view"),
        owner="postgres",
        kind=ViewKind.VIEW,
    )
    description = ViewDescription(
        view=view,
        columns=(
            ColumnInfo(
                name="id",
                position=1,
                data_type="bigint",
                nullable=True,
            ),
        ),
        definition="SELECT id FROM public.customers;",
    )

    listing = render_view_list((view,))
    detail = render_view_description(description)

    assert "public.customer_view\tpostgres\tview" in listing
    assert "Kind: view" in detail
    assert "1\tid\tbigint\tyes" in detail
    assert "SELECT id FROM public.customers;" in detail


def test_index_renderers() -> None:
    index = IndexInfo(
        name=QualifiedName(schema="public", name="customers_email_idx"),
        table=QualifiedName(schema="public", name="customers"),
        method="btree",
        owner="postgres",
        unique=True,
        size_bytes=16384,
    )
    description = IndexDescription(
        index=index,
        definition="CREATE UNIQUE INDEX customers_email_idx ON public.customers USING btree (email)",
        predicate="email IS NOT NULL",
    )

    listing = render_index_list((index,))
    detail = render_index_description(description)

    assert "public.customers_email_idx\tpublic.customers\tbtree\tyes\tno" in listing
    assert "Method: btree" in detail
    assert "Unique: yes" in detail
    assert "Predicate: email IS NOT NULL" in detail
    assert "CREATE UNIQUE INDEX" in detail


def test_renderers_handle_unknown_optional_values() -> None:
    database = DatabaseInfo(name="empty")
    rendered = render_database_info(database)
    assert "Allow connections: -" in rendered
    assert "Size bytes: -" in rendered


def test_capability_renderers() -> None:
    available = CapabilityStatus(
        name="catalog.view.list",
        availability=CapabilityAvailability.AVAILABLE,
    )
    unavailable = CapabilityStatus(
        name="runtime.session.list",
        availability=CapabilityAvailability.UNKNOWN,
        reason="Not implemented.",
    )

    listing = render_capability_list((available, unavailable))
    detail = render_capability_info(available)

    assert "catalog.view.list\tavailable\t-" in listing
    assert "runtime.session.list\tunknown\tNot implemented." in listing
    assert "Available: yes" in detail

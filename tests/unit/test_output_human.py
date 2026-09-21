"""Unit tests for initial human renderers."""

import pytest

from pydbadminkit.domain.catalog import DatabaseInfo, ServerInfo
from pydbadminkit.domain.common import (
    CapabilityAvailability,
    CapabilityStatus,
    DatabaseEngine,
    DatabaseVersion,
)
from pydbadminkit.output.human import (
    render_capability_info,
    render_capability_list,
    render_database_info,
    render_database_list,
    render_server_info,
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


def test_renderers_handle_unknown_optional_values() -> None:
    database = DatabaseInfo(name="empty")
    rendered = render_database_info(database)
    assert "Allow connections: -" in rendered
    assert "Size bytes: -" in rendered


def test_capability_renderers() -> None:
    available = CapabilityStatus(
        name="server.info",
        availability=CapabilityAvailability.AVAILABLE,
    )
    unavailable = CapabilityStatus(
        name="catalog.table.list",
        availability=CapabilityAvailability.UNKNOWN,
        reason="Not implemented.",
    )

    listing = render_capability_list((available, unavailable))
    detail = render_capability_info(available)

    assert "server.info\tavailable\t-" in listing
    assert "catalog.table.list\tunknown\tNot implemented." in listing
    assert "Available: yes" in detail

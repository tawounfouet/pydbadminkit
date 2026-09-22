"""Unit tests for human-readable runtime output."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.domain.runtime import QueryInfo, SessionInfo, SessionState, TransactionInfo
from pydbadminkit.output.human import (
    render_query_list,
    render_session_list,
    render_transaction_list,
)

pytestmark = [pytest.mark.unit, pytest.mark.runtime]


def test_render_session_list() -> None:
    rendered = render_session_list(
        (
            SessionInfo(
                pid=101,
                database="analytics",
                username="app",
                state=SessionState.IDLE,
                wait_event_type="Client",
                wait_event="ClientRead",
            ),
        )
    )

    assert "PID\tDATABASE\tUSER" in rendered
    assert "Client:ClientRead" in rendered


def test_render_query_list_collapses_multiline_sql() -> None:
    rendered = render_query_list(
        (
            QueryInfo(
                pid=102,
                database="analytics",
                username="app",
                state=SessionState.ACTIVE,
                elapsed_ms=12.345,
                query_text="SELECT *\nFROM orders",
            ),
        )
    )

    assert "12.35" in rendered
    assert "SELECT * FROM orders" in rendered


def test_render_transaction_list() -> None:
    rendered = render_transaction_list(
        (
            TransactionInfo(
                pid=103,
                database="analytics",
                transaction_started_at=datetime(2026, 9, 22, 16, 0, tzinfo=UTC),
                elapsed_ms=1000.0,
                backend_xid="735",
            ),
        )
    )

    assert "XID" in rendered
    assert "735" in rendered

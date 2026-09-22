"""Unit tests for runtime domain models."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from pydbadminkit.domain.runtime import QueryInfo, SessionInfo, SessionState, TransactionInfo

pytestmark = [pytest.mark.unit, pytest.mark.runtime]


def test_runtime_models_accept_valid_values() -> None:
    started_at = datetime(2026, 9, 22, 16, 0, tzinfo=UTC)

    session = SessionInfo(pid=101, state=SessionState.ACTIVE)
    query = QueryInfo(pid=102, elapsed_ms=12.5, state=SessionState.ACTIVE)
    transaction = TransactionInfo(
        pid=103,
        transaction_started_at=started_at,
        elapsed_ms=50.0,
        state=SessionState.IDLE_IN_TRANSACTION,
    )

    assert session.pid == 101
    assert query.elapsed_ms == 12.5
    assert transaction.transaction_started_at == started_at


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: SessionInfo(pid=0), "session pid"),
        (lambda: QueryInfo(pid=-1), "query pid"),
        (lambda: QueryInfo(pid=1, elapsed_ms=-0.1), "query elapsed_ms"),
        (
            lambda: TransactionInfo(
                pid=1,
                transaction_started_at=datetime(2026, 9, 22, tzinfo=UTC),
                elapsed_ms=-1.0,
            ),
            "transaction elapsed_ms",
        ),
    ],
)
def test_runtime_models_reject_invalid_values(
    factory: Callable[[], object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()

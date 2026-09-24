"""Unit tests for PostgreSQL restore target database adapter."""

from unittest.mock import MagicMock

import pytest

from pydbadminkit.adapters.postgresql.restore_database import (
    PostgreSQLRestoreDatabaseAdapter,
)
from pydbadminkit.domain.common import DatabaseEngine, EnvironmentName
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SecretValue,
    SSLConfig,
    TimeoutConfig,
)
from pydbadminkit.errors import InternalError

pytestmark = [pytest.mark.unit, pytest.mark.postgresql, pytest.mark.restore]


def _config() -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("local"),
        engine=DatabaseEngine.POSTGRESQL,
        host="127.0.0.1",
        port=5432,
        database="postgres",
        username="postgres",
        password=SecretValue("secret"),
        environment=EnvironmentName.TESTING,
        read_only=False,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(connect_seconds=5),
    )


def _adapter(row: object = None):
    executor = MagicMock()
    executor.fetch_one.return_value = row
    factory = MagicMock()
    adapter = PostgreSQLRestoreDatabaseAdapter(
        executor=executor,
        connection_factory=factory,
        config=_config(),
    )
    return adapter, executor, factory


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"exists": True}, True),
        ({"exists": False}, False),
    ],
)
def test_target_exists_maps_postgresql_result(row: dict[str, bool], expected: bool) -> None:
    adapter, executor, _factory = _adapter(row)

    assert adapter.target_exists("target") is expected
    executor.fetch_one.assert_called_once()
    assert executor.fetch_one.call_args.kwargs["query_id"] == "restore.target.exists"


@pytest.mark.parametrize("row", [None, {}])
def test_target_exists_rejects_unexpected_result(row: object) -> None:
    adapter, _executor, _factory = _adapter(row)

    with pytest.raises(InternalError, match="unexpected result"):
        adapter.target_exists("target")


def test_create_target_executes_safe_create_database_statement() -> None:
    adapter, executor, _factory = _adapter()

    adapter.create_target("target")

    executor.execute.assert_called_once()
    assert executor.execute.call_args.kwargs["query_id"] == "restore.target.create"


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        (None, False),
        (("target",), False),
        (("target", False), False),
        (("other", True), False),
        (("target", True), True),
    ],
)
def test_verify_target_checks_database_identity_and_public_schema(
    row: tuple[object, ...] | None,
    expected: bool,
) -> None:
    adapter, _executor, factory = _adapter()

    connection = MagicMock()
    cursor = MagicMock()
    factory.connect.return_value.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = row

    assert adapter.verify_target("target") is expected

    resolved = factory.connect.call_args.args[0]
    assert resolved.database == "target"
    cursor.execute.assert_called_once()

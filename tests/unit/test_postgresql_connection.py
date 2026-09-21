"""Unit tests for PostgreSQL connection adapter behavior."""

from typing import Any

import psycopg
import pytest

from pydbadminkit.adapters.postgresql.connection import (
    PostgreSQLConnectionFactory,
    PostgreSQLConnectionTester,
)
from pydbadminkit.adapters.postgresql.errors import translate_connection_error
from pydbadminkit.domain.common import DatabaseEngine, EnvironmentName
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SecretValue,
    SSLConfig,
    SSLMode,
    TimeoutConfig,
)
from pydbadminkit.errors import (
    AuthenticationError,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
    InternalError,
)
from pydbadminkit.errors.context import ErrorContext

pytestmark = pytest.mark.unit


def _config() -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("unit"),
        engine=DatabaseEngine.POSTGRESQL,
        host="localhost",
        port=5432,
        database="postgres",
        username="postgres",
        password=SecretValue("secret"),
        environment=EnvironmentName.TESTING,
        read_only=False,
        ssl=SSLConfig(
            mode=SSLMode.VERIFY_FULL,
            root_cert="/tmp/ca.crt",
            cert="/tmp/client.crt",
            key="/tmp/client.key",
        ),
        timeouts=TimeoutConfig(connect_seconds=3),
    )


class FakeCursor:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.row = row
        self.executed = False

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, _query: str) -> None:
        self.executed = True

    def fetchone(self) -> tuple[object, ...] | None:
        return self.row


class FakeConnection:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self._cursor = FakeCursor(row)

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self._cursor


class FakeFactory:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self._connection = FakeConnection(row)

    def connect(self, _config: ResolvedConnectionConfig) -> FakeConnection:
        return self._connection


class FakeDriverError(Exception):
    def __init__(self, message: str, sqlstate: str | None = None) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate


def test_factory_builds_conninfo_without_exposing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    sentinel = object()

    def fake_make_conninfo(**kwargs: object) -> str:
        captured.update(kwargs)
        return "safe-conninfo"

    def fake_connect(conninfo: str, *, autocommit: bool) -> object:
        captured["conninfo"] = conninfo
        captured["autocommit"] = autocommit
        return sentinel

    monkeypatch.setattr(psycopg.conninfo, "make_conninfo", fake_make_conninfo)
    monkeypatch.setattr(psycopg, "connect", fake_connect)

    result = PostgreSQLConnectionFactory().connect(_config())

    assert result is sentinel
    assert captured["password"] == "secret"
    assert captured["sslrootcert"] == "/tmp/ca.crt"
    assert captured["sslcert"] == "/tmp/client.crt"
    assert captured["sslkey"] == "/tmp/client.key"
    assert captured["autocommit"] is True


def test_connection_tester_maps_safe_result() -> None:
    tester = PostgreSQLConnectionTester(FakeFactory((180001, "postgres", "postgres")))

    result = tester.test(_config())

    assert result.version.major == 18
    assert result.version.minor == 1
    assert result.current_database == "postgres"
    assert result.current_user == "postgres"


def test_connection_tester_rejects_unexpected_row() -> None:
    tester = PostgreSQLConnectionTester(FakeFactory(None))

    with pytest.raises(InternalError):
        tester.test(_config())


@pytest.mark.parametrize(
    ("driver_error", "expected_type"),
    [
        (FakeDriverError("bad password", "28P01"), AuthenticationError),
        (FakeDriverError("connection timeout"), DatabaseConnectionTimeoutError),
        (FakeDriverError("connection refused"), DatabaseConnectionError),
    ],
)
def test_translate_connection_error(
    driver_error: FakeDriverError,
    expected_type: type[Exception],
) -> None:
    translated = translate_connection_error(
        driver_error,  # type: ignore[arg-type]
        context=ErrorContext(operation="connection.open"),
    )
    assert isinstance(translated, expected_type)

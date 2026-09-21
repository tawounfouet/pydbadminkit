"""Unit tests for the shared PostgreSQL executor."""

from typing import Any

import psycopg
import pytest

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.domain.common import DatabaseEngine, EnvironmentName
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SSLConfig,
    SSLMode,
    TimeoutConfig,
)
from pydbadminkit.errors import DatabaseOperationError

pytestmark = pytest.mark.unit


def _config() -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("unit"),
        engine=DatabaseEngine.POSTGRESQL,
        host="localhost",
        port=5432,
        database="postgres",
        username="postgres",
        password=None,
        environment=EnvironmentName.TESTING,
        read_only=True,
        ssl=SSLConfig(mode=SSLMode.DISABLE),
        timeouts=TimeoutConfig(),
    )


class FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.query: str | None = None
        self.params: tuple[object, ...] | None = None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
    ) -> None:
        self.query = query
        self.params = params

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows


class FakeConnection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.cursor_instance = FakeCursor(rows)

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self, *, row_factory: object = None) -> FakeCursor:
        del row_factory
        return self.cursor_instance


class FakeFactory:
    def __init__(
        self,
        rows: list[dict[str, Any]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.rows = rows or []
        self.error = error

    def connect(self, _config: ResolvedConnectionConfig) -> FakeConnection:
        if self.error is not None:
            raise self.error
        return FakeConnection(self.rows)


def test_executor_fetch_all_and_one() -> None:
    executor = PostgreSQLExecutor(
        FakeFactory(rows=[{"name": "a"}, {"name": "b"}]),  # type: ignore[arg-type]
        _config(),
    )

    rows = executor.fetch_all("SELECT 1", ("x",), query_id="TEST_QUERY")
    first = executor.fetch_one("SELECT 1", query_id="TEST_QUERY")

    assert rows == ({"name": "a"}, {"name": "b"})
    assert first == {"name": "a"}


def test_executor_fetch_one_returns_none_for_empty_result() -> None:
    executor = PostgreSQLExecutor(FakeFactory(), _config())  # type: ignore[arg-type]
    assert executor.fetch_one("SELECT 1", query_id="EMPTY") is None


def test_executor_translates_psycopg_operation_error() -> None:
    executor = PostgreSQLExecutor(
        FakeFactory(error=psycopg.OperationalError("boom")),  # type: ignore[arg-type]
        _config(),
    )

    with pytest.raises(DatabaseOperationError):
        executor.fetch_all("SELECT 1", query_id="BROKEN")

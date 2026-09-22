"""Integration tests for PostgreSQL runtime inspection CLI."""

import json
import os
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [pytest.mark.integration, pytest.mark.postgresql, pytest.mark.runtime]

runner = CliRunner()


def _host() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_HOST", "127.0.0.1")


def _port() -> int:
    return int(os.getenv("PYDBADMIN_TEST_POSTGRES_PORT", "5432"))


def _database() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_DATABASE", "pydbadmin_test")


def _user() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_USER", "postgres")


def _password() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", "postgres")


def _connect() -> psycopg.Connection[tuple[object, ...]]:
    return psycopg.connect(
        host=_host(),
        port=_port(),
        dbname=_database(),
        user=_user(),
        password=_password(),
        autocommit=True,
    )


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
[connections.local]
engine = "postgresql"
host = "{_host()}"
port = {_port()}
database = "{_database()}"
username = "{_user()}"
environment = "testing"
ssl_mode = "disable"
connect_timeout_seconds = 5

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_TEST_POSTGRES_PASSWORD"
""".strip(),
        encoding="utf-8",
    )
    return path


def _base_args(config: Path) -> list[str]:
    return [
        "--connection",
        "local",
        "--config",
        str(config),
    ]


def _wait_until_blocked(waiter_pid: int, blocker_pid: int) -> None:
    deadline = time.monotonic() + 5.0
    with _connect() as connection, connection.cursor() as cursor:
        while time.monotonic() < deadline:
            cursor.execute(
                """
                SELECT %s = ANY(pg_catalog.pg_blocking_pids(%s))
                """,
                (blocker_pid, waiter_pid),
            )
            row = cursor.fetchone()
            if row is not None and row[0] is True:
                return
            time.sleep(0.05)
    raise AssertionError("waiter did not enter the expected blocked state")


@pytest.fixture
def blocking_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[int, int]]:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    advisory_key = 941726
    ready = threading.Event()
    waiter_pid: list[int] = []
    waiter_errors: list[Exception] = []

    blocker = _connect()
    blocker_cursor = blocker.cursor()
    blocker_cursor.execute("SELECT pg_catalog.pg_backend_pid()")
    blocker_row = blocker_cursor.fetchone()
    assert blocker_row is not None
    blocker_pid = int(blocker_row[0])
    blocker_cursor.execute(
        "SELECT pg_catalog.pg_advisory_lock(%s::bigint)",
        (advisory_key,),
    )

    def run_waiter() -> None:
        try:
            with _connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT pg_catalog.pg_backend_pid()")
                row = cursor.fetchone()
                assert row is not None
                waiter_pid.append(int(row[0]))
                ready.set()
                cursor.execute(
                    "SELECT pg_catalog.pg_advisory_lock(%s::bigint)",
                    (advisory_key,),
                )
                cursor.execute(
                    "SELECT pg_catalog.pg_advisory_unlock(%s::bigint)",
                    (advisory_key,),
                )
        except Exception as error:
            waiter_errors.append(error)
            ready.set()

    waiter = threading.Thread(target=run_waiter, daemon=True)
    waiter.start()

    assert ready.wait(timeout=5.0)
    if waiter_errors:
        raise waiter_errors[0]
    assert waiter_pid

    _wait_until_blocked(waiter_pid[0], blocker_pid)

    try:
        yield blocker_pid, waiter_pid[0]
    finally:
        blocker_cursor.execute(
            "SELECT pg_catalog.pg_advisory_unlock(%s::bigint)",
            (advisory_key,),
        )
        blocker_cursor.close()
        blocker.close()
        waiter.join(timeout=5.0)
        assert not waiter.is_alive()
        if waiter_errors:
            raise waiter_errors[0]


def test_session_list_includes_current_session_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "session", "list", "--include-self"],
    )

    assert result.exit_code == 0, result.output
    assert "PID\tDATABASE\tUSER" in result.stdout
    assert _database() in result.stdout
    assert _user() in result.stdout


def test_query_list_json_exposes_current_query_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "--output",
            "json",
            "query",
            "list",
            "--include-self",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed
    assert parsed[0]["database"] == _database()
    assert parsed[0]["state"] == "active"


def test_transaction_list_includes_current_transaction_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "transaction", "list", "--include-self"],
    )

    assert result.exit_code == 0, result.output
    assert "PID\tDATABASE\tUSER\tSTATE\tELAPSED_MS" in result.stdout
    assert _database() in result.stdout


def test_wait_and_waiting_lock_commands_detect_real_contention(
    tmp_path: Path,
    blocking_pair: tuple[int, int],
) -> None:
    _, waiter_pid = blocking_pair
    config = _config(tmp_path)

    waits = runner.invoke(
        app,
        [
            *_base_args(config),
            "wait",
            "list",
            "--database",
            _database(),
            "--type",
            "Lock",
        ],
    )
    locks = runner.invoke(
        app,
        [
            *_base_args(config),
            "lock",
            "list",
            "--database",
            _database(),
            "--waiting-only",
        ],
    )

    assert waits.exit_code == 0, waits.output
    assert str(waiter_pid) in waits.stdout
    assert "Lock" in waits.stdout

    assert locks.exit_code == 0, locks.output
    assert str(waiter_pid) in locks.stdout
    assert "advisory" in locks.stdout
    assert "no" in locks.stdout


def test_blocking_list_json_detects_blocker_edge(
    tmp_path: Path,
    blocking_pair: tuple[int, int],
) -> None:
    blocker_pid, waiter_pid = blocking_pair
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "--output",
            "json",
            "blocking",
            "list",
            "--database",
            _database(),
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    matching = [
        item
        for item in parsed
        if item["root_pid"] == waiter_pid
        and item["blocked_pid"] == waiter_pid
        and item["blocking_pid"] == blocker_pid
    ]
    assert matching
    assert matching[0]["depth"] == 1

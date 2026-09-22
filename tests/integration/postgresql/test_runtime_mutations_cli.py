"""PostgreSQL guarded Runtime mutation integration tests."""

import json
import os
import threading
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.postgresql,
    pytest.mark.runtime,
    pytest.mark.destructive,
]

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
read_only = false
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
    return ["--connection", "local", "--config", str(config)]


def _backend_exists(pid: int) -> bool:
    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid = %s)",
            (pid,),
        )
        row = cursor.fetchone()
        return row is not None and row[0] is True


def _start_sleep_backend() -> tuple[int, threading.Thread, list[str]]:
    ready = threading.Event()
    pid_box: list[int] = []
    outcomes: list[str] = []

    def worker() -> None:
        try:
            with _connect() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT pg_catalog.pg_backend_pid()")
                row = cursor.fetchone()
                assert row is not None
                pid_box.append(int(row[0]))
                ready.set()
                try:
                    cursor.execute("SELECT pg_catalog.pg_sleep(30)")
                    outcomes.append("completed")
                except psycopg.Error:
                    outcomes.append("interrupted")
                    try:
                        cursor.execute("SELECT 1")
                        outcomes.append("alive")
                    except psycopg.Error:
                        outcomes.append("closed")
        except psycopg.Error:
            outcomes.append("connection-error")
            ready.set()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    assert ready.wait(timeout=5.0)
    assert pid_box
    return pid_box[0], thread, outcomes


def _cleanup_backend(pid: int) -> None:
    if not _backend_exists(pid):
        return
    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT pg_catalog.pg_terminate_backend(%s)", (pid,))


@pytest.fixture
def runtime_mutation_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[Path, Path]]:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    audit_path = tmp_path / "runtime-audit.jsonl"
    monkeypatch.setenv("PYDBADMIN_AUDIT_PATH", str(audit_path))
    yield _config(tmp_path), audit_path


def test_query_cancel_interrupts_query_but_keeps_session_usable(
    runtime_mutation_environment: tuple[Path, Path],
) -> None:
    config, audit_path = runtime_mutation_environment
    pid, thread, outcomes = _start_sleep_backend()

    try:
        result = runner.invoke(
            app,
            [*_base_args(config), "--yes", "query", "cancel", str(pid)],
        )

        assert result.exit_code == 0, result.output
        assert "Status: succeeded" in result.stdout
        thread.join(timeout=5.0)
        assert not thread.is_alive()
        assert "interrupted" in outcomes
        assert "alive" in outcomes
    finally:
        _cleanup_backend(pid)

    events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [item["event_type"] for item in events[-2:]] == [
        "started",
        "succeeded",
    ]
    assert events[-1]["operation"] == "runtime.query.cancel"
    assert events[-1]["target"] == f"pid:{pid}"


def test_session_terminate_disconnects_target_backend(
    runtime_mutation_environment: tuple[Path, Path],
) -> None:
    config, audit_path = runtime_mutation_environment
    pid, thread, outcomes = _start_sleep_backend()

    try:
        result = runner.invoke(
            app,
            [*_base_args(config), "--yes", "session", "terminate", str(pid)],
        )

        assert result.exit_code == 0, result.output
        assert "Status: succeeded" in result.stdout
        thread.join(timeout=5.0)
        assert not thread.is_alive()
        assert "interrupted" in outcomes or "connection-error" in outcomes
        assert _backend_exists(pid) is False
    finally:
        _cleanup_backend(pid)

    events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [item["event_type"] for item in events[-2:]] == [
        "started",
        "succeeded",
    ]
    assert events[-1]["operation"] == "runtime.session.terminate"
    assert events[-1]["target"] == f"pid:{pid}"

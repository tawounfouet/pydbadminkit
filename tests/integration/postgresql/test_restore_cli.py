"""PostgreSQL logical restore integration tests."""

import json
import os
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.postgresql,
    pytest.mark.restore,
    pytest.mark.destructive,
]

runner = CliRunner()

_TARGETS = (
    "pydbadmin_restore_custom",
    "pydbadmin_restore_plain",
    "pydbadmin_restore_existing",
)


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


def _connect(database: str) -> psycopg.Connection[tuple[object, ...]]:
    return psycopg.connect(
        host=_host(),
        port=_port(),
        dbname=database,
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


def _drop_database(name: str) -> None:
    with _connect("postgres") as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT pg_catalog.pg_terminate_backend(pid)
            FROM pg_catalog.pg_stat_activity
            WHERE datname = %s
              AND pid <> pg_backend_pid()
            """,
            (name,),
        )
        cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))


def _create_database(name: str) -> None:
    _drop_database(name)
    with _connect("postgres") as connection, connection.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


def _seed_source() -> None:
    with _connect(_database()) as connection, connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS public.restore_probe")
        cursor.execute(
            """
            CREATE TABLE public.restore_probe (
                id integer PRIMARY KEY,
                payload text NOT NULL
            )
            """
        )
        cursor.execute("INSERT INTO public.restore_probe (id, payload) VALUES (42, 'restored')")


def _assert_probe(database: str) -> None:
    with _connect(database) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, payload FROM public.restore_probe ORDER BY id")
        assert cursor.fetchall() == [(42, "restored")]


@pytest.fixture
def restore_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    audit_path = tmp_path / "restore-audit.jsonl"
    monkeypatch.setenv("PYDBADMIN_AUDIT_PATH", str(audit_path))
    for target in _TARGETS:
        _drop_database(target)
    _seed_source()
    yield _config(tmp_path), audit_path
    for target in _TARGETS:
        _drop_database(target)


def test_custom_backup_restores_to_new_database(
    tmp_path: Path,
    restore_environment: tuple[Path, Path],
) -> None:
    config, audit_path = restore_environment
    backup_path = tmp_path / "source.dump"

    backup = runner.invoke(
        app,
        [
            *_base_args(config),
            "backup",
            "create",
            _database(),
            "--format",
            "custom",
            "--output-path",
            str(backup_path),
        ],
    )
    restore = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "backup",
            "restore",
            str(backup_path),
            "--database",
            "pydbadmin_restore_custom",
            "--create",
        ],
    )

    assert backup.exit_code == 0, backup.output
    assert restore.exit_code == 0, restore.output
    assert "Verification: passed" in restore.output
    _assert_probe("pydbadmin_restore_custom")

    events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [event["event_type"] for event in events[-2:]] == [
        "started",
        "succeeded",
    ]
    assert events[-1]["operation"] == "backup.restore"


def test_plain_sql_backup_restores_with_psql(
    tmp_path: Path,
    restore_environment: tuple[Path, Path],
) -> None:
    config, _audit_path = restore_environment
    backup_path = tmp_path / "source.sql"

    backup = runner.invoke(
        app,
        [
            *_base_args(config),
            "backup",
            "create",
            _database(),
            "--format",
            "plain_sql",
            "--output-path",
            str(backup_path),
        ],
    )
    restore = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "backup",
            "restore",
            str(backup_path),
            "--database",
            "pydbadmin_restore_plain",
            "--create",
        ],
    )

    assert backup.exit_code == 0, backup.output
    assert restore.exit_code == 0, restore.output
    assert "Tool: psql" in restore.output
    _assert_probe("pydbadmin_restore_plain")


def test_existing_target_is_blocked_until_custom_clean_is_explicit(
    tmp_path: Path,
    restore_environment: tuple[Path, Path],
) -> None:
    config, _audit_path = restore_environment
    backup_path = tmp_path / "source.dump"

    backup = runner.invoke(
        app,
        [
            *_base_args(config),
            "backup",
            "create",
            _database(),
            "--format",
            "custom",
            "--output-path",
            str(backup_path),
        ],
    )
    assert backup.exit_code == 0, backup.output

    _create_database("pydbadmin_restore_existing")

    blocked = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "backup",
            "restore",
            str(backup_path),
            "--database",
            "pydbadmin_restore_existing",
        ],
    )
    assert blocked.exit_code == 8
    assert "implicit overwrite is blocked" in blocked.output

    cleaned = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "backup",
            "restore",
            str(backup_path),
            "--database",
            "pydbadmin_restore_existing",
            "--clean",
        ],
    )
    assert cleaned.exit_code == 0, cleaned.output
    _assert_probe("pydbadmin_restore_existing")

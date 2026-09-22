"""PostgreSQL maintenance integration tests."""

import json
import os
from pathlib import Path

import psycopg
import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.postgresql,
    pytest.mark.maintenance,
    pytest.mark.destructive,
]

runner = CliRunner()

_TABLE = "pydbadmin_maintenance_probe"
_INDEX = "pydbadmin_maintenance_probe_payload_idx"


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


@pytest.fixture
def maintenance_objects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    audit_path = tmp_path / "maintenance-audit.jsonl"
    monkeypatch.setenv("PYDBADMIN_AUDIT_PATH", str(audit_path))

    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE IF EXISTS public."{_TABLE}"')
        cursor.execute(
            f"""
            CREATE TABLE public."{_TABLE}" (
                id integer PRIMARY KEY,
                payload text NOT NULL
            )
            """
        )
        cursor.executemany(
            f'INSERT INTO public."{_TABLE}" (id, payload) VALUES (%s, %s)',
            [(index, f"value-{index % 10}") for index in range(1, 501)],
        )
        cursor.execute(
            f'CREATE INDEX "{_INDEX}" ON public."{_TABLE}" (payload)'
        )
        cursor.execute(
            f'DELETE FROM public."{_TABLE}" WHERE id % 5 = 0'
        )

    yield _config(tmp_path), audit_path

    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE IF EXISTS public."{_TABLE}"')


def test_vacuum_analyze_and_reindex_execute_with_autocommit(
    maintenance_objects: tuple[Path, Path],
) -> None:
    config, audit_path = maintenance_objects

    vacuum = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "postgres",
            "vacuum",
            "--table",
            f"public.{_TABLE}",
            "--analyze",
            "--statement-timeout",
            "30",
            "--lock-timeout",
            "5",
        ],
    )
    analyze = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "postgres",
            "analyze",
            "--table",
            f"public.{_TABLE}",
            "--column",
            "payload",
        ],
    )
    reindex_index = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "postgres",
            "reindex",
            "--index",
            f"public.{_INDEX}",
            "--concurrently",
        ],
    )
    reindex_table = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "postgres",
            "reindex",
            "--table",
            f"public.{_TABLE}",
        ],
    )

    assert vacuum.exit_code == 0, vacuum.output
    assert analyze.exit_code == 0, analyze.output
    assert reindex_index.exit_code == 0, reindex_index.output
    assert reindex_table.exit_code == 0, reindex_table.output

    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute(f'SELECT count(*) FROM public."{_TABLE}"')
        assert cursor.fetchone() == (400,)
        cursor.execute(
            """
            SELECT indisvalid
            FROM pg_catalog.pg_index
            WHERE indexrelid = %s::regclass
            """,
            (f"public.{_INDEX}",),
        )
        assert cursor.fetchone() == (True,)

    events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    succeeded = [
        event
        for event in events
        if event["event_type"] == "succeeded"
        and event["operation"].startswith("maintenance.")
    ]
    assert len(succeeded) == 4


def test_maintenance_dry_run_and_progress_commands(
    maintenance_objects: tuple[Path, Path],
) -> None:
    config, _audit_path = maintenance_objects

    dry_run = runner.invoke(
        app,
        [
            *_base_args(config),
            "--dry-run",
            "--output",
            "json",
            "postgres",
            "vacuum",
            "--table",
            f"public.{_TABLE}",
            "--full",
        ],
    )
    vacuum_progress = runner.invoke(
        app,
        [
            *_base_args(config),
            "--output",
            "json",
            "postgres",
            "progress",
            "vacuum",
        ],
    )
    reindex_progress = runner.invoke(
        app,
        [
            *_base_args(config),
            "--output",
            "json",
            "postgres",
            "progress",
            "reindex",
        ],
    )

    assert dry_run.exit_code == 0, dry_run.output
    plan = json.loads(dry_run.stdout)
    assert plan["operation"] == "maintenance.vacuum"
    assert plan["target"] == f"public.{_TABLE}"

    assert vacuum_progress.exit_code == 0, vacuum_progress.output
    assert reindex_progress.exit_code == 0, reindex_progress.output
    assert isinstance(json.loads(vacuum_progress.stdout), list)
    assert isinstance(json.loads(reindex_progress.stdout), list)

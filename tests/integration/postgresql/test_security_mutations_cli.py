"""PostgreSQL guarded security mutation integration tests."""

import json
import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.postgresql,
    pytest.mark.security,
    pytest.mark.destructive,
]

runner = CliRunner()

_APP_ROLE = "pydbadmin_mutation_app"
_READER_ROLE = "pydbadmin_mutation_reader"
_CRITICAL_ROLE = "pydbadmin_mutation_super"
_DRY_ROLE = "pydbadmin_mutation_dry"


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


def _config(tmp_path: Path, *, read_only: bool = False) -> Path:
    path = tmp_path / ("readonly.toml" if read_only else "config.toml")
    path.write_text(
        f"""
[connections.local]
engine = "postgresql"
host = "{_host()}"
port = {_port()}
database = "{_database()}"
username = "{_user()}"
environment = "testing"
read_only = {str(read_only).lower()}
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


def _connect() -> psycopg.Connection[tuple[object, ...]]:
    return psycopg.connect(
        host=_host(),
        port=_port(),
        dbname=_database(),
        user=_user(),
        password=_password(),
        autocommit=True,
    )


def _role_exists(name: str) -> bool:
    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (name,))
        return cursor.fetchone() is not None


@pytest.fixture
def mutation_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[Path, Path]]:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setenv("PYDBADMIN_AUDIT_PATH", str(audit_path))

    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_mutation_target")
        for name in (_APP_ROLE, _READER_ROLE, _CRITICAL_ROLE, _DRY_ROLE):
            cursor.execute(f'DROP ROLE IF EXISTS "{name}"')
        cursor.execute(
            """
            CREATE TABLE public.pydbadmin_mutation_target (
                id bigint PRIMARY KEY,
                payload text
            )
            """
        )
        cursor.execute(f'CREATE ROLE "{_READER_ROLE}" NOLOGIN')

    yield _config(tmp_path), audit_path

    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_mutation_target")
        for name in (_APP_ROLE, _READER_ROLE, _CRITICAL_ROLE, _DRY_ROLE):
            cursor.execute(f'DROP ROLE IF EXISTS "{name}"')


def test_dry_run_returns_plan_without_creating_role(
    mutation_environment: tuple[Path, Path],
) -> None:
    config, audit_path = mutation_environment

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "--dry-run",
            "--output",
            "json",
            "role",
            "create",
            _DRY_ROLE,
            "--login",
        ],
    )

    assert result.exit_code == 0, result.output
    plan = json.loads(result.stdout)
    assert plan["operation"] == "security.role.create"
    assert plan["target"] == _DRY_ROLE
    assert plan["risk"] == "medium"
    assert _role_exists(_DRY_ROLE) is False
    assert audit_path.exists() is False


def test_role_create_alter_membership_access_revoke_and_drop(
    mutation_environment: tuple[Path, Path],
) -> None:
    config, audit_path = mutation_environment

    create = runner.invoke(
        app,
        [*_base_args(config), "--yes", "role", "create", _APP_ROLE, "--login"],
    )
    alter = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "role",
            "alter",
            _APP_ROLE,
            "--createdb",
            "enable",
        ],
    )
    membership_add = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "role",
            "membership-add",
            _READER_ROLE,
            _APP_ROLE,
        ],
    )
    access_grant = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "access",
            "grant",
            "--role",
            _APP_ROLE,
            "--object",
            "public.pydbadmin_mutation_target",
            "--access",
            "SELECT",
        ],
    )

    assert create.exit_code == 0, create.output
    assert alter.exit_code == 0, alter.output
    assert membership_add.exit_code == 0, membership_add.output
    assert access_grant.exit_code == 0, access_grant.output

    with _connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolcanlogin, rolcreatedb FROM pg_roles WHERE rolname = %s",
            (_APP_ROLE,),
        )
        assert cursor.fetchone() == (True, True)
        cursor.execute(
            "SELECT pg_has_role(%s, %s, 'MEMBER')",
            (_APP_ROLE, _READER_ROLE),
        )
        assert cursor.fetchone() == (True,)
        cursor.execute(
            "SELECT has_table_privilege(%s, %s, 'SELECT')",
            (_APP_ROLE, "public.pydbadmin_mutation_target"),
        )
        assert cursor.fetchone() == (True,)

    access_revoke = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "access",
            "revoke",
            "--role",
            _APP_ROLE,
            "--object",
            "public.pydbadmin_mutation_target",
            "--access",
            "SELECT",
        ],
    )
    membership_remove = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "role",
            "membership-remove",
            _READER_ROLE,
            _APP_ROLE,
        ],
    )
    drop = runner.invoke(
        app,
        [*_base_args(config), "--yes", "role", "drop", _APP_ROLE],
    )

    assert access_revoke.exit_code == 0, access_revoke.output
    assert membership_remove.exit_code == 0, membership_remove.output
    assert drop.exit_code == 0, drop.output
    assert _role_exists(_APP_ROLE) is False

    lines = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    operations = {item["operation"] for item in lines}
    assert "security.role.create" in operations
    assert "security.role.alter" in operations
    assert "security.membership.add" in operations
    assert "security.access.grant" in operations
    assert "security.access.revoke" in operations
    assert "security.membership.remove" in operations
    assert "security.role.drop" in operations
    assert all("password" not in json.dumps(item).lower() for item in lines)


def test_yes_does_not_bypass_typed_target_confirmation(
    mutation_environment: tuple[Path, Path],
) -> None:
    config, _audit_path = mutation_environment

    blocked = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "--non-interactive",
            "role",
            "create",
            _CRITICAL_ROLE,
            "--superuser",
        ],
    )

    assert blocked.exit_code == 7
    assert _role_exists(_CRITICAL_ROLE) is False

    created = runner.invoke(
        app,
        [
            *_base_args(config),
            "--non-interactive",
            "role",
            "create",
            _CRITICAL_ROLE,
            "--superuser",
            "--confirm-target",
            _CRITICAL_ROLE,
        ],
    )

    assert created.exit_code == 0, created.output
    assert _role_exists(_CRITICAL_ROLE) is True

    dropped = runner.invoke(
        app,
        [*_base_args(config), "--yes", "role", "drop", _CRITICAL_ROLE],
    )
    assert dropped.exit_code == 0, dropped.output


def test_read_only_profile_blocks_mutation(
    mutation_environment: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    _config_path, _audit_path = mutation_environment
    config = _config(tmp_path, read_only=True)

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "--non-interactive",
            "role",
            "create",
            _APP_ROLE,
        ],
    )

    assert result.exit_code == 7
    assert "read-only" in result.output.lower()
    assert _role_exists(_APP_ROLE) is False

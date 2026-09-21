"""PostgreSQL role security CLI integration tests."""

import json
import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from typer.testing import CliRunner

from pydbadminkit.adapters.postgresql.queries.access import LIST_DIRECT_RELATION_ACCESS
from pydbadminkit.cli.app import app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.postgresql,
    pytest.mark.security,
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


@pytest.fixture
def security_roles(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())

    with (
        psycopg.connect(
            host=_host(),
            port=_port(),
            dbname=_database(),
            user=_user(),
            password=_password(),
            autocommit=True,
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_security_target")
        cursor.execute("DROP ROLE IF EXISTS pydbadmin_app")
        cursor.execute("DROP ROLE IF EXISTS pydbadmin_reader")
        cursor.execute("CREATE ROLE pydbadmin_reader NOLOGIN")
        cursor.execute(
            """
            CREATE ROLE pydbadmin_app
            LOGIN
            VALID UNTIL '2030-01-01 00:00:00+00'
            """
        )
        cursor.execute("GRANT pydbadmin_reader TO pydbadmin_app")
        cursor.execute(
            """
            CREATE TABLE public.pydbadmin_security_target (
                id bigint PRIMARY KEY,
                payload text
            )
            """
        )
        cursor.execute(
            """
            GRANT SELECT, UPDATE
            ON TABLE public.pydbadmin_security_target
            TO pydbadmin_app
            """
        )

    yield

    with (
        psycopg.connect(
            host=_host(),
            port=_port(),
            dbname=_database(),
            user=_user(),
            password=_password(),
            autocommit=True,
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_security_target")
        cursor.execute("DROP ROLE IF EXISTS pydbadmin_app")
        cursor.execute("DROP ROLE IF EXISTS pydbadmin_reader")


def test_role_list_filters_login_roles(
    tmp_path: Path,
    security_roles: None,
) -> None:
    del security_roles
    config = _config(tmp_path)

    listing = runner.invoke(app, [*_base_args(config), "role", "list"])
    login_only = runner.invoke(
        app,
        [*_base_args(config), "role", "list", "--login-only"],
    )

    assert listing.exit_code == 0, listing.output
    assert "pydbadmin_reader" in listing.stdout
    assert "pydbadmin_app" in listing.stdout
    assert "pg_monitor" not in listing.stdout

    assert login_only.exit_code == 0, login_only.output
    assert "pydbadmin_app" in login_only.stdout
    assert "pydbadmin_reader" not in login_only.stdout


def test_role_describe_exposes_membership_graph(
    tmp_path: Path,
    security_roles: None,
) -> None:
    del security_roles
    config = _config(tmp_path)

    app_role = runner.invoke(
        app,
        [*_base_args(config), "role", "describe", "pydbadmin_app"],
    )
    reader_role = runner.invoke(
        app,
        [*_base_args(config), "role", "describe", "pydbadmin_reader"],
    )

    assert app_role.exit_code == 0, app_role.output
    assert "Login: yes" in app_role.stdout
    assert "MEMBER OF" in app_role.stdout
    assert "pydbadmin_reader" in app_role.stdout

    assert reader_role.exit_code == 0, reader_role.output
    assert "MEMBERS" in reader_role.stdout
    assert "pydbadmin_app" in reader_role.stdout


def test_role_describe_json_serializes_valid_until(
    tmp_path: Path,
    security_roles: None,
) -> None:
    del security_roles
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "--output",
            "json",
            "role",
            "describe",
            "pydbadmin_app",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert parsed["role"]["name"] == "pydbadmin_app"
    assert parsed["role"]["can_login"] is True
    assert parsed["role"]["valid_until"].startswith("2030-01-01T00:00:00")


def test_role_describe_missing_returns_not_found(
    tmp_path: Path,
    security_roles: None,
) -> None:
    del security_roles
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "role", "describe", "__missing_role__"],
    )

    assert result.exit_code == 5
    assert "was not found or is not visible" in result.output


def test_access_list_exposes_explicit_relation_entries(
    tmp_path: Path,
    security_roles: None,
) -> None:
    del security_roles
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "access",
            "list",
            "--role",
            "pydbadmin_app",
            "--schema",
            "public",
            "--object",
            "pydbadmin_security_target",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "public.pydbadmin_security_target" in result.stdout
    assert "\tSELECT\t" in result.stdout
    assert "\tUPDATE\t" in result.stdout
    assert "pydbadmin_reader" not in result.stdout


def test_access_list_json_is_machine_readable(
    tmp_path: Path,
    security_roles: None,
) -> None:
    del security_roles
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "--output",
            "json",
            "access",
            "list",
            "--role",
            "pydbadmin_app",
            "--object",
            "pydbadmin_security_target",
        ],
    )

    assert result.exit_code == 0, result.output
    parsed = json.loads(result.stdout)
    assert {item["access_type"] for item in parsed} == {"SELECT", "UPDATE"}
    assert all(item["principal"] == "pydbadmin_app" for item in parsed)
    assert all(item["object"]["object_type"] == "table" for item in parsed)


def test_direct_access_query_executes_natively(
    security_roles: None,
) -> None:
    del security_roles

    with (
        psycopg.connect(
            host=_host(),
            port=_port(),
            dbname=_database(),
            user=_user(),
            password=_password(),
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            LIST_DIRECT_RELATION_ACCESS,
            (
                "pydbadmin_app",
                False,
                "public",
                "public",
                "pydbadmin_security_target",
                "pydbadmin_security_target",
            ),
        )
        rows = cursor.fetchall()

    assert len(rows) == 2

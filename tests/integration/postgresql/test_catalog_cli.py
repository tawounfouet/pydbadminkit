"""Integration tests for PostgreSQL catalog CLI slices."""

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [pytest.mark.integration, pytest.mark.postgresql]

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
def catalog_objects(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
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
        cursor.execute(
            "DROP MATERIALIZED VIEW IF EXISTS public.pydbadmin_customer_mv"
        )
        cursor.execute("DROP VIEW IF EXISTS public.pydbadmin_customer_view")
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_customers")
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_accounts")
        cursor.execute(
            """
            CREATE TABLE public.pydbadmin_accounts (
                id bigint PRIMARY KEY,
                code text NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE public.pydbadmin_customers (
                id bigint PRIMARY KEY,
                account_id bigint NOT NULL,
                email text NOT NULL UNIQUE,
                display_name text DEFAULT 'anonymous',
                CONSTRAINT pydbadmin_customers_account_fk
                    FOREIGN KEY (account_id)
                    REFERENCES public.pydbadmin_accounts(id)
            )
            """
        )
        cursor.execute(
            """
            COMMENT ON COLUMN public.pydbadmin_customers.email
            IS 'customer email address'
            """
        )
        cursor.execute(
            """
            CREATE VIEW public.pydbadmin_customer_view AS
            SELECT id, email, display_name
            FROM public.pydbadmin_customers
            """
        )
        cursor.execute(
            """
            CREATE MATERIALIZED VIEW public.pydbadmin_customer_mv AS
            SELECT id, email
            FROM public.pydbadmin_customers
            WITH NO DATA
            """
        )
        cursor.execute(
            """
            CREATE INDEX pydbadmin_customers_display_idx
            ON public.pydbadmin_customers (display_name)
            WHERE display_name IS NOT NULL
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
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_customers")
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_accounts")


def test_server_info_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    result = runner.invoke(app, [*_base_args(config), "server", "info"])

    assert result.exit_code == 0, result.output
    assert "Engine: postgresql" in result.stdout
    assert "Version: 18" in result.stdout
    assert f"Database: {_database()}" in result.stdout


def test_database_list_and_describe_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    listing = runner.invoke(app, [*_base_args(config), "database", "list"])
    detail = runner.invoke(
        app,
        [*_base_args(config), "database", "describe", _database()],
    )

    assert listing.exit_code == 0, listing.output
    assert "NAME\tOWNER\tENCODING" in listing.stdout
    assert _database() in listing.stdout

    assert detail.exit_code == 0, detail.output
    assert f"Name: {_database()}" in detail.stdout
    assert f"Owner: {_user()}" in detail.stdout
    assert "Encoding: UTF8" in detail.stdout


def test_database_describe_missing_returns_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "database", "describe", "__missing_database__"],
    )

    assert result.exit_code == 5
    assert "was not found or is not visible" in result.output


def test_schema_list_and_describe_cli(
    tmp_path: Path,
    catalog_objects: None,
) -> None:
    del catalog_objects
    config = _config(tmp_path)

    listing = runner.invoke(app, [*_base_args(config), "schema", "list"])
    detail = runner.invoke(
        app,
        [*_base_args(config), "schema", "describe", "public"],
    )
    with_system = runner.invoke(
        app,
        [*_base_args(config), "schema", "list", "--include-system"],
    )

    assert listing.exit_code == 0, listing.output
    assert "public" in listing.stdout
    assert "pg_catalog" not in listing.stdout

    assert detail.exit_code == 0, detail.output
    assert "Name: public" in detail.stdout
    assert "System: no" in detail.stdout

    assert with_system.exit_code == 0, with_system.output
    assert "pg_catalog" in with_system.stdout


def test_table_list_and_describe_cli(
    tmp_path: Path,
    catalog_objects: None,
) -> None:
    del catalog_objects
    config = _config(tmp_path)

    listing = runner.invoke(
        app,
        [*_base_args(config), "table", "list", "--schema", "public"],
    )
    detail = runner.invoke(
        app,
        [
            *_base_args(config),
            "table",
            "describe",
            "public.pydbadmin_customers",
        ],
    )

    assert listing.exit_code == 0, listing.output
    assert "public.pydbadmin_customers" in listing.stdout
    assert "public.pydbadmin_accounts" in listing.stdout

    assert detail.exit_code == 0, detail.output
    assert "Name: public.pydbadmin_customers" in detail.stdout
    assert "COLUMNS" in detail.stdout
    assert "email\ttext\tno" in detail.stdout
    assert "'anonymous'::text" in detail.stdout
    assert "CONSTRAINTS" in detail.stdout
    assert "primary_key" in detail.stdout
    assert "unique" in detail.stdout
    assert "foreign_key" in detail.stdout
    assert "pydbadmin_customers_account_fk" in detail.stdout


def test_table_describe_defaults_to_public_schema(
    tmp_path: Path,
    catalog_objects: None,
) -> None:
    del catalog_objects
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "table", "describe", "pydbadmin_customers"],
    )

    assert result.exit_code == 0, result.output
    assert "Name: public.pydbadmin_customers" in result.stdout


def test_table_describe_missing_returns_not_found(
    tmp_path: Path,
    catalog_objects: None,
) -> None:
    del catalog_objects
    config = _config(tmp_path)

    result = runner.invoke(
        app,
        [*_base_args(config), "table", "describe", "public.__missing_table__"],
    )

    assert result.exit_code == 5
    assert "was not found or is not visible" in result.output


def test_view_list_and_describe_cli(
    tmp_path: Path,
    catalog_objects: None,
) -> None:
    del catalog_objects
    config = _config(tmp_path)

    listing = runner.invoke(
        app,
        [*_base_args(config), "view", "list", "--schema", "public"],
    )
    detail = runner.invoke(
        app,
        [
            *_base_args(config),
            "view",
            "describe",
            "public.pydbadmin_customer_view",
        ],
    )
    materialized = runner.invoke(
        app,
        [
            *_base_args(config),
            "view",
            "describe",
            "public.pydbadmin_customer_mv",
        ],
    )

    assert listing.exit_code == 0, listing.output
    assert "public.pydbadmin_customer_view" in listing.stdout
    assert "public.pydbadmin_customer_mv" in listing.stdout
    assert "materialized_view" in listing.stdout

    assert detail.exit_code == 0, detail.output
    assert "Kind: view" in detail.stdout
    assert "COLUMNS" in detail.stdout
    assert "DEFINITION" in detail.stdout
    assert "pydbadmin_customers" in detail.stdout

    assert materialized.exit_code == 0, materialized.output
    assert "Kind: materialized_view" in materialized.stdout


def test_index_list_and_describe_cli(
    tmp_path: Path,
    catalog_objects: None,
) -> None:
    del catalog_objects
    config = _config(tmp_path)

    listing = runner.invoke(
        app,
        [
            *_base_args(config),
            "index",
            "list",
            "--schema",
            "public",
            "--table",
            "pydbadmin_customers",
        ],
    )
    detail = runner.invoke(
        app,
        [
            *_base_args(config),
            "index",
            "describe",
            "public.pydbadmin_customers_display_idx",
        ],
    )

    assert listing.exit_code == 0, listing.output
    assert "public.pydbadmin_customers_display_idx" in listing.stdout
    assert "btree" in listing.stdout

    assert detail.exit_code == 0, detail.output
    assert "Method: btree" in detail.stdout
    assert "Predicate:" in detail.stdout
    assert "display_name IS NOT NULL" in detail.stdout
    assert "DEFINITION" in detail.stdout
    assert "CREATE INDEX" in detail.stdout


def test_view_and_index_missing_return_not_found(
    tmp_path: Path,
    catalog_objects: None,
) -> None:
    del catalog_objects
    config = _config(tmp_path)

    view = runner.invoke(
        app,
        [*_base_args(config), "view", "describe", "public.__missing_view__"],
    )
    index = runner.invoke(
        app,
        [*_base_args(config), "index", "describe", "public.__missing_index__"],
    )

    assert view.exit_code == 5
    assert index.exit_code == 5


def test_capability_cli() -> None:
    listing = runner.invoke(app, ["capability", "list"])
    detail = runner.invoke(app, ["capability", "get", "catalog.table.describe"])

    assert listing.exit_code == 0
    assert "catalog.table.list\tavailable" in listing.stdout
    assert "catalog.view.list\tavailable" in listing.stdout
    assert "catalog.index.list\tavailable" in listing.stdout
    assert "runtime.session.list\tunknown" in listing.stdout
    assert detail.exit_code == 0
    assert "Available: yes" in detail.stdout

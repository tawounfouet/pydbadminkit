"""Integration tests for PostgreSQL Monitoring Core."""

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from pydbadminkit.bootstrap import build_monitoring_service
from pydbadminkit.domain.common import QualifiedName

pytestmark = [pytest.mark.integration, pytest.mark.postgresql]


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


@pytest.fixture
def monitoring_objects(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
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
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_monitoring_events")
        cursor.execute(
            """
            CREATE TABLE public.pydbadmin_monitoring_events (
                id bigint PRIMARY KEY,
                category text NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX pydbadmin_monitoring_events_category_idx
            ON public.pydbadmin_monitoring_events (category)
            """
        )
        cursor.execute(
            """
            INSERT INTO public.pydbadmin_monitoring_events (id, category)
            VALUES (1, 'a'), (2, 'b'), (3, 'a')
            """
        )
        cursor.execute("ANALYZE public.pydbadmin_monitoring_events")

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
        cursor.execute("DROP TABLE IF EXISTS public.pydbadmin_monitoring_events")


def test_monitoring_core_reads_real_postgresql_statistics(
    tmp_path: Path,
    monitoring_objects: None,
) -> None:
    del monitoring_objects
    service = build_monitoring_service("local", _config(tmp_path))

    connections = service.get_connection_statistics()
    databases = service.get_database_sizes()
    tables = service.get_table_statistics(
        QualifiedName(schema="public", name="pydbadmin_monitoring_events")
    )
    indexes = service.get_index_statistics(
        QualifiedName(
            schema="public",
            name="pydbadmin_monitoring_events_category_idx",
        )
    )
    metrics = service.collect_metrics()

    assert connections.total >= 1
    assert connections.max_connections is not None
    assert connections.utilization_ratio is not None
    assert any(item.database == _database() and item.size_bytes > 0 for item in databases)
    assert len(tables) == 1
    assert tables[0].table.name == "pydbadmin_monitoring_events"
    assert tables[0].live_tuples is not None
    assert len(indexes) == 1
    assert indexes[0].index.name == "pydbadmin_monitoring_events_category_idx"
    assert indexes[0].size_bytes is not None
    assert any(metric.name == "connections.total" for metric in metrics)
    assert any(metric.name == "database.size_bytes" for metric in metrics)

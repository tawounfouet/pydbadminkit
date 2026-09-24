"""Repository-level SQL injection hardening regression tests."""

from typing import Any

import pytest
from psycopg import sql

from pydbadminkit.adapters.postgresql.maintenance import (
    _analyze_query,
    _reindex_query,
    _vacuum_query,
)
from pydbadminkit.adapters.postgresql.restore_database import (
    PostgreSQLRestoreDatabaseAdapter,
)
from pydbadminkit.adapters.postgresql.security import PostgreSQLSecurityAdapter
from pydbadminkit.domain.common import DatabaseEngine, EnvironmentName, QualifiedName
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SSLConfig,
    TimeoutConfig,
)
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    ReindexCommand,
    ReindexTargetType,
    VacuumCommand,
)
from pydbadminkit.domain.security import (
    AccessType,
    CreateRoleCommand,
    RelationAccessCommand,
)

pytestmark = [pytest.mark.unit, pytest.mark.postgresql, pytest.mark.security]


class CaptureExecutor:
    def __init__(self) -> None:
        self.queries: list[object] = []

    def execute(
        self,
        query: Any,
        params: tuple[object, ...] | None = None,
        *,
        query_id: str,
    ) -> int:
        del params, query_id
        self.queries.append(query)
        return 0


def _render(query: object) -> str:
    assert isinstance(query, sql.Composable)
    return query.as_string()


def _config() -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("local"),
        engine=DatabaseEngine.POSTGRESQL,
        host="127.0.0.1",
        port=5432,
        database="postgres",
        username="postgres",
        password=None,
        environment=EnvironmentName.TESTING,
        read_only=False,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(),
    )


def test_role_identifier_payload_is_quoted_not_interpolated() -> None:
    executor = CaptureExecutor()
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]
    payload = 'app"; DROP ROLE postgres; --'

    adapter.create_role(CreateRoleCommand(name=payload))

    rendered = _render(executor.queries[0])
    assert rendered.startswith('CREATE ROLE "app""; DROP ROLE postgres; --" ')
    assert 'CREATE ROLE app";' not in rendered


def test_relation_and_principal_payloads_are_identifiers() -> None:
    executor = CaptureExecutor()
    adapter = PostgreSQLSecurityAdapter(executor)  # type: ignore[arg-type]
    command = RelationAccessCommand(
        principal='reader"; DROP ROLE postgres; --',
        access_type=AccessType.SELECT,
        object=QualifiedName(
            schema='public"; DROP SCHEMA public; --',
            name='orders"; DROP TABLE orders; --',
        ),
    )

    adapter.grant_access(command)

    rendered = _render(executor.queries[0])
    assert rendered == (
        'GRANT SELECT ON TABLE '
        '"public""; DROP SCHEMA public; --"."orders""; DROP TABLE orders; --" '
        'TO "reader""; DROP ROLE postgres; --"'
    )


def test_restore_database_payload_is_quoted_identifier() -> None:
    executor = CaptureExecutor()
    adapter = PostgreSQLRestoreDatabaseAdapter(
        executor=executor,  # type: ignore[arg-type]
        connection_factory=object(),  # type: ignore[arg-type]
        config=_config(),
    )

    adapter.create_target('target"; DROP DATABASE postgres; --')

    assert _render(executor.queries[0]) == (
        'CREATE DATABASE "target""; DROP DATABASE postgres; --"'
    )


def test_maintenance_relation_and_column_payloads_are_quoted() -> None:
    relation = QualifiedName(
        schema='public"; DROP SCHEMA public; --',
        name='events"; DROP TABLE events; --',
    )
    column = 'payload"; DROP TABLE events; --'

    vacuum = _render(_vacuum_query(VacuumCommand(table=relation)))
    analyze = _render(
        _analyze_query(
            AnalyzeCommand(
                table=relation,
                columns=(column,),
            )
        )
    )

    quoted_relation = (
        '"public""; DROP SCHEMA public; --"."events""; DROP TABLE events; --"'
    )
    assert vacuum == f"VACUUM {quoted_relation}"
    assert analyze == f'ANALYZE {quoted_relation} ("payload""; DROP TABLE events; --")'


def test_reindex_target_type_is_whitelisted_and_identifier_is_quoted() -> None:
    command = ReindexCommand(
        target_type=ReindexTargetType.INDEX,
        target=QualifiedName(
            schema="public",
            name='idx"; DROP INDEX idx; --',
        ),
        concurrently=True,
    )

    rendered = _render(_reindex_query(command))

    assert rendered == 'REINDEX INDEX CONCURRENTLY "public"."idx""; DROP INDEX idx; --"'

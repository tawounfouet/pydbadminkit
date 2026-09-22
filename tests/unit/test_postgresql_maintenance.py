"""Unit tests for PostgreSQL maintenance adapter."""

from dataclasses import dataclass
from typing import Any

import pytest

from pydbadminkit.adapters.postgresql.maintenance import PostgreSQLMaintenanceAdapter
from pydbadminkit.domain.common import (
    DatabaseEngine,
    DatabaseVersion,
    EnvironmentName,
    QualifiedName,
)
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SSLConfig,
    TimeoutConfig,
)
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    MaintenanceOperationType,
    ReindexCommand,
    ReindexTargetType,
    VacuumCommand,
)
from pydbadminkit.errors import CapabilityNotAvailableError, ResourceNotFoundError

pytestmark = [pytest.mark.unit, pytest.mark.postgresql, pytest.mark.maintenance]


@dataclass
class CursorSpec:
    one: tuple[object, ...] | None = None
    many: tuple[tuple[object, ...], ...] = ()


class FakeCursor:
    def __init__(self, spec: CursorSpec) -> None:
        self.spec = spec
        self.calls: list[tuple[object, tuple[object, ...] | None]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(
        self,
        query: Any,
        params: tuple[object, ...] | None = None,
    ) -> None:
        self.calls.append((query, params))

    def fetchone(self) -> tuple[object, ...] | None:
        return self.spec.one

    def fetchall(self) -> tuple[tuple[object, ...], ...]:
        return self.spec.many


class FakeConnection:
    def __init__(self, spec: CursorSpec) -> None:
        self.cursor_instance = FakeCursor(spec)

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self.cursor_instance


class FakeFactory:
    def __init__(self, *specs: CursorSpec) -> None:
        self.specs = list(specs)
        self.connections: list[FakeConnection] = []

    def connect(self, _config: ResolvedConnectionConfig) -> FakeConnection:
        spec = self.specs.pop(0) if self.specs else CursorSpec()
        connection = FakeConnection(spec)
        self.connections.append(connection)
        return connection


def _config() -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("local"),
        engine=DatabaseEngine.POSTGRESQL,
        host="127.0.0.1",
        port=5432,
        database="pydbadmin_test",
        username="postgres",
        password=None,
        environment=EnvironmentName.TESTING,
        read_only=False,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(),
    )


def _adapter(
    factory: FakeFactory,
    *,
    server_major: int = 18,
) -> PostgreSQLMaintenanceAdapter:
    return PostgreSQLMaintenanceAdapter(
        connection_factory=factory,  # type: ignore[arg-type]
        config=_config(),
        server_version=DatabaseVersion(server_major),
    )


def test_vacuum_validates_target_and_applies_session_timeouts() -> None:
    factory = FakeFactory(CursorSpec(one=("r",)), CursorSpec())
    adapter = _adapter(factory)

    operation = adapter.vacuum(
        VacuumCommand(
            table=QualifiedName(schema="public", name="events"),
            freeze=True,
            analyze=True,
            statement_timeout_seconds=60,
            lock_timeout_seconds=5,
        )
    )

    execution_calls = factory.connections[1].cursor_instance.calls
    assert operation.operation_type is MaintenanceOperationType.VACUUM
    assert len(execution_calls) == 3
    assert execution_calls[0][1] == ("statement_timeout", "60s")
    assert execution_calls[1][1] == ("lock_timeout", "5s")


def test_database_wide_analyze_executes_without_relation_preflight() -> None:
    factory = FakeFactory(CursorSpec())
    adapter = _adapter(factory)

    operation = adapter.analyze(AnalyzeCommand())

    assert operation.operation_type is MaintenanceOperationType.ANALYZE
    assert len(factory.connections) == 1


def test_missing_or_wrong_relation_type_is_rejected() -> None:
    missing = _adapter(FakeFactory(CursorSpec(one=None)))
    with pytest.raises(ResourceNotFoundError):
        missing.validate_analyze(
            AnalyzeCommand(table=QualifiedName(schema="public", name="missing"))
        )

    wrong_type = _adapter(FakeFactory(CursorSpec(one=("i",))))
    with pytest.raises(ResourceNotFoundError):
        wrong_type.validate_vacuum(
            VacuumCommand(table=QualifiedName(schema="public", name="events_idx"))
        )


def test_cross_database_target_is_rejected_before_connection() -> None:
    factory = FakeFactory()
    adapter = _adapter(factory)

    with pytest.raises(CapabilityNotAvailableError):
        adapter.validate_vacuum(
            VacuumCommand(
                table=QualifiedName(
                    database="other",
                    schema="public",
                    name="events",
                )
            )
        )

    assert factory.connections == []


def test_reindex_concurrently_is_version_aware() -> None:
    adapter = _adapter(
        FakeFactory(CursorSpec(one=("i",))),
        server_major=11,
    )

    with pytest.raises(CapabilityNotAvailableError):
        adapter.validate_reindex(
            ReindexCommand(
                target_type=ReindexTargetType.INDEX,
                target=QualifiedName(schema="public", name="events_idx"),
                concurrently=True,
            )
        )


def test_reindex_table_executes_after_target_validation() -> None:
    factory = FakeFactory(CursorSpec(one=("r",)), CursorSpec())
    adapter = _adapter(factory)

    operation = adapter.reindex(
        ReindexCommand(
            target_type=ReindexTargetType.TABLE,
            target=QualifiedName(schema="public", name="events"),
        )
    )

    assert operation.operation_type is MaintenanceOperationType.REINDEX
    assert len(factory.connections) == 2


def test_maintenance_progress_maps_reliable_counters() -> None:
    vacuum_factory = FakeFactory(
        CursorSpec(
            many=(
                (101, "public", "events", "scanning heap", 50, 100),
                (102, None, None, "initializing", 0, 0),
            )
        )
    )
    vacuum = _adapter(vacuum_factory).list_vacuum_progress()

    assert vacuum[0].pid == 101
    assert str(vacuum[0].target) == "public.events"
    assert vacuum[0].percent == 50.0
    assert vacuum[1].percent is None

    reindex_factory = FakeFactory(
        CursorSpec(many=((201, "public", "events_idx", "building index", 9, 10),))
    )
    reindex = _adapter(reindex_factory).list_reindex_progress()

    assert reindex[0].operation_type is MaintenanceOperationType.REINDEX
    assert reindex[0].percent == 90.0

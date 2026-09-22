"""Unit tests for maintenance domain models."""

from datetime import UTC, datetime

import pytest

from pydbadminkit.domain.common import OperationStatus, QualifiedName
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    MaintenanceOperation,
    MaintenanceOperationType,
    MaintenanceProgress,
    ReindexCommand,
    ReindexTargetType,
    VacuumCommand,
)

pytestmark = [pytest.mark.unit, pytest.mark.maintenance]


def test_maintenance_models_accept_supported_commands() -> None:
    table = QualifiedName(schema="public", name="events")

    vacuum = VacuumCommand(
        table=table,
        freeze=True,
        analyze=True,
        statement_timeout_seconds=60,
        lock_timeout_seconds=5,
    )
    analyze = AnalyzeCommand(
        table=table,
        columns=("created_at",),
    )
    reindex = ReindexCommand(
        target_type=ReindexTargetType.TABLE,
        target=table,
        concurrently=True,
    )
    operation = MaintenanceOperation(
        operation_type=MaintenanceOperationType.VACUUM,
        target=table,
        started_at=datetime(2026, 9, 22, tzinfo=UTC),
        finished_at=datetime(2026, 9, 22, tzinfo=UTC),
        status=OperationStatus.SUCCEEDED,
        duration_ms=12,
    )
    progress = MaintenanceProgress(
        operation_type=MaintenanceOperationType.VACUUM,
        pid=42,
        target=table,
        phase="scanning heap",
        completed=50,
        total=100,
        percent=50.0,
    )

    assert vacuum.analyze is True
    assert analyze.columns == ("created_at",)
    assert reindex.target_type is ReindexTargetType.TABLE
    assert operation.duration_ms == 12
    assert progress.percent == 50.0


@pytest.mark.parametrize(
    "factory",
    [
        lambda: VacuumCommand(statement_timeout_seconds=0),
        lambda: VacuumCommand(lock_timeout_seconds=-1),
        lambda: AnalyzeCommand(columns=("id",)),
        lambda: AnalyzeCommand(
            table=QualifiedName(name="events"),
            columns=("",),
        ),
        lambda: ReindexCommand(
            target_type=ReindexTargetType.INDEX,
            target=QualifiedName(name="idx"),
            statement_timeout_seconds=0,
        ),
        lambda: MaintenanceOperation(
            operation_type=MaintenanceOperationType.ANALYZE,
            target=None,
            started_at=datetime(2026, 9, 22, tzinfo=UTC),
            finished_at=None,
            status=OperationStatus.FAILED,
            duration_ms=-1,
        ),
        lambda: MaintenanceProgress(
            operation_type=MaintenanceOperationType.REINDEX,
            pid=0,
            target=None,
            phase=None,
            completed=None,
            total=None,
            percent=None,
        ),
        lambda: MaintenanceProgress(
            operation_type=MaintenanceOperationType.REINDEX,
            pid=1,
            target=None,
            phase=None,
            completed=-1,
            total=1,
            percent=0,
        ),
        lambda: MaintenanceProgress(
            operation_type=MaintenanceOperationType.REINDEX,
            pid=1,
            target=None,
            phase=None,
            completed=1,
            total=1,
            percent=101,
        ),
    ],
)
def test_maintenance_models_reject_invalid_values(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]

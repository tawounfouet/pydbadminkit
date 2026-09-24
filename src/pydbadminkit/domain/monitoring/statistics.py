"""Point-in-time database monitoring statistics."""

from dataclasses import dataclass
from datetime import datetime

from pydbadminkit.domain.common import QualifiedName


def _require_non_negative(value: int | None, field: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field} must be >= 0")


@dataclass(frozen=True, slots=True)
class ConnectionStatistics:
    """Current PostgreSQL connection utilization facts."""

    total: int
    active: int
    idle: int
    idle_in_transaction: int
    max_connections: int | None
    utilization_ratio: float | None

    def __post_init__(self) -> None:
        for field, value in (
            ("total", self.total),
            ("active", self.active),
            ("idle", self.idle),
            ("idle_in_transaction", self.idle_in_transaction),
            ("max_connections", self.max_connections),
        ):
            _require_non_negative(value, field)
        if self.max_connections == 0:
            raise ValueError("max_connections must be > 0 when provided")
        if self.utilization_ratio is not None and self.utilization_ratio < 0:
            raise ValueError("utilization_ratio must be >= 0")


@dataclass(frozen=True, slots=True)
class DatabaseSizeMetric:
    """Current logical database size."""

    database: str
    size_bytes: int

    def __post_init__(self) -> None:
        if not self.database or self.database.isspace():
            raise ValueError("database must not be blank")
        _require_non_negative(self.size_bytes, "size_bytes")


@dataclass(frozen=True, slots=True)
class TableSizeMetric:
    """Current table storage footprint."""

    table: QualifiedName
    data_bytes: int | None
    index_bytes: int | None
    total_bytes: int | None

    def __post_init__(self) -> None:
        _require_non_negative(self.data_bytes, "data_bytes")
        _require_non_negative(self.index_bytes, "index_bytes")
        _require_non_negative(self.total_bytes, "total_bytes")


@dataclass(frozen=True, slots=True)
class TableStatistics:
    """Point-in-time PostgreSQL table statistics observation."""

    table: QualifiedName
    estimated_rows: int | None = None
    sequential_scans: int | None = None
    index_scans: int | None = None
    live_tuples: int | None = None
    dead_tuples: int | None = None
    inserted_rows: int | None = None
    updated_rows: int | None = None
    deleted_rows: int | None = None
    last_vacuum: datetime | None = None
    last_autovacuum: datetime | None = None
    last_analyze: datetime | None = None
    last_autoanalyze: datetime | None = None

    def __post_init__(self) -> None:
        for field, value in (
            ("estimated_rows", self.estimated_rows),
            ("sequential_scans", self.sequential_scans),
            ("index_scans", self.index_scans),
            ("live_tuples", self.live_tuples),
            ("dead_tuples", self.dead_tuples),
            ("inserted_rows", self.inserted_rows),
            ("updated_rows", self.updated_rows),
            ("deleted_rows", self.deleted_rows),
        ):
            _require_non_negative(value, field)


@dataclass(frozen=True, slots=True)
class IndexStatistics:
    """Point-in-time PostgreSQL index statistics observation."""

    index: QualifiedName
    table: QualifiedName
    scans: int | None = None
    tuples_read: int | None = None
    tuples_fetched: int | None = None
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        for field, value in (
            ("scans", self.scans),
            ("tuples_read", self.tuples_read),
            ("tuples_fetched", self.tuples_fetched),
            ("size_bytes", self.size_bytes),
        ):
            _require_non_negative(value, field)

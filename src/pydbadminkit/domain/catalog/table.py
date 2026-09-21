"""Table catalog models."""

from dataclasses import dataclass
from enum import StrEnum

from pydbadminkit.domain.catalog.column import ColumnInfo
from pydbadminkit.domain.common.names import QualifiedName


class TableKind(StrEnum):
    """Cross-engine table kinds used by the initial catalog."""

    TABLE = "table"
    PARTITIONED_TABLE = "partitioned_table"
    FOREIGN_TABLE = "foreign_table"


class ConstraintType(StrEnum):
    """Common relational constraint types."""

    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    CHECK = "check"
    EXCLUSION = "exclusion"


@dataclass(frozen=True, slots=True)
class ConstraintInfo:
    """Minimal immutable constraint description."""

    name: str
    constraint_type: ConstraintType
    columns: tuple[str, ...] = ()
    definition: str | None = None

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("constraint name must not be blank")


@dataclass(frozen=True, slots=True)
class TableInfo:
    """Read-only summary of a table."""

    name: QualifiedName
    owner: str | None = None
    kind: TableKind = TableKind.TABLE
    estimated_rows: int | None = None
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        if self.estimated_rows is not None and self.estimated_rows < 0:
            raise ValueError("estimated_rows must be >= 0")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")


@dataclass(frozen=True, slots=True)
class TableDescription:
    """Detailed immutable table description."""

    table: TableInfo
    columns: tuple[ColumnInfo, ...]
    constraints: tuple[ConstraintInfo, ...] = ()

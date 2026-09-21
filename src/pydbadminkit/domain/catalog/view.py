"""View catalog models."""

from dataclasses import dataclass
from enum import StrEnum

from pydbadminkit.domain.catalog.column import ColumnInfo
from pydbadminkit.domain.common.names import QualifiedName


class ViewKind(StrEnum):
    """Cross-engine view kinds."""

    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"


@dataclass(frozen=True, slots=True)
class ViewInfo:
    """Read-only summary of a database view."""

    name: QualifiedName
    owner: str | None = None
    kind: ViewKind = ViewKind.VIEW


@dataclass(frozen=True, slots=True)
class ViewDescription:
    """Detailed immutable view description."""

    view: ViewInfo
    columns: tuple[ColumnInfo, ...]
    definition: str | None = None

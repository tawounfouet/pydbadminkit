"""Map PostgreSQL view metadata to public domain models."""

from collections.abc import Mapping

from pydbadminkit.adapters.postgresql.mappers.table import map_column_info
from pydbadminkit.domain.catalog import ColumnInfo, ViewDescription, ViewInfo, ViewKind
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.errors import InternalError

_VIEW_KIND_BY_RELKIND = {
    "v": ViewKind.VIEW,
    "m": ViewKind.MATERIALIZED_VIEW,
}


def map_view_info(row: Mapping[str, object]) -> ViewInfo:
    """Map one PostgreSQL view summary."""

    try:
        owner = row.get("owner")
        return ViewInfo(
            name=QualifiedName(
                schema=str(row["schema_name"]),
                name=str(row["name"]),
            ),
            owner=None if owner is None else str(owner),
            kind=_VIEW_KIND_BY_RELKIND[str(row["relkind"])],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL view row mapping failed.") from error


def build_view_description(
    view_row: Mapping[str, object],
    column_rows: tuple[Mapping[str, object], ...],
    definition_row: Mapping[str, object] | None,
) -> ViewDescription:
    """Build one detailed view aggregate."""

    definition: str | None = None
    if definition_row is not None:
        raw_definition = definition_row.get("definition")
        if raw_definition is not None:
            definition = str(raw_definition)

    columns: tuple[ColumnInfo, ...] = tuple(map_column_info(row) for row in column_rows)
    return ViewDescription(
        view=map_view_info(view_row),
        columns=columns,
        definition=definition,
    )

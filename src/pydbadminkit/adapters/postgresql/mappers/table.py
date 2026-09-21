"""Map PostgreSQL table metadata to public domain models."""

from collections.abc import Mapping, Sequence

from pydbadminkit.domain.catalog import (
    ColumnInfo,
    ConstraintInfo,
    ConstraintType,
    TableDescription,
    TableInfo,
    TableKind,
)
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.errors import InternalError

_TABLE_KIND_BY_RELKIND = {
    "r": TableKind.TABLE,
    "p": TableKind.PARTITIONED_TABLE,
    "f": TableKind.FOREIGN_TABLE,
}

_CONSTRAINT_TYPE_BY_CODE = {
    "p": ConstraintType.PRIMARY_KEY,
    "f": ConstraintType.FOREIGN_KEY,
    "u": ConstraintType.UNIQUE,
    "c": ConstraintType.CHECK,
    "x": ConstraintType.EXCLUSION,
}


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid integer value")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError("expected integer-compatible value")


def _required_int(value: object) -> int:
    result = _optional_int(value)
    if result is None:
        raise TypeError("integer value is required")
    return result


def _required_bool(value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError("boolean value is required")
    return value


def map_table_info(row: Mapping[str, object]) -> TableInfo:
    """Map one pg_class relation summary."""

    try:
        relkind = str(row["relkind"])
        kind = _TABLE_KIND_BY_RELKIND[relkind]
        schema_name = str(row["schema_name"])
        owner = row.get("owner")
        return TableInfo(
            name=QualifiedName(
                schema=schema_name,
                name=str(row["name"]),
            ),
            owner=None if owner is None else str(owner),
            kind=kind,
            estimated_rows=_optional_int(row.get("estimated_rows")),
            size_bytes=_optional_int(row.get("size_bytes")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL table row mapping failed.") from error


def map_column_info(row: Mapping[str, object]) -> ColumnInfo:
    """Map one pg_attribute row."""

    try:
        default_expression = row.get("default_expression")
        comment = row.get("comment")
        return ColumnInfo(
            name=str(row["name"]),
            position=_required_int(row["position"]),
            data_type=str(row["data_type"]),
            nullable=_required_bool(row["nullable"]),
            default=None if default_expression is None else str(default_expression),
            identity=_required_bool(row["identity"]),
            generated=_required_bool(row["generated"]),
            comment=None if comment is None else str(comment),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL column row mapping failed.") from error


def map_constraint_info(row: Mapping[str, object]) -> ConstraintInfo:
    """Map one pg_constraint row."""

    try:
        constraint_type = _CONSTRAINT_TYPE_BY_CODE[str(row["constraint_type"])]
        raw_columns = row.get("columns", ())
        if not isinstance(raw_columns, Sequence) or isinstance(raw_columns, (str, bytes)):
            raise TypeError("constraint columns must be a sequence")
        definition = row.get("definition")
        return ConstraintInfo(
            name=str(row["name"]),
            constraint_type=constraint_type,
            columns=tuple(str(column) for column in raw_columns),
            definition=None if definition is None else str(definition),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL constraint row mapping failed.") from error


def build_table_description(
    table_row: Mapping[str, object],
    column_rows: tuple[Mapping[str, object], ...],
    constraint_rows: tuple[Mapping[str, object], ...],
) -> TableDescription:
    """Build one detailed table aggregate."""

    return TableDescription(
        table=map_table_info(table_row),
        columns=tuple(map_column_info(row) for row in column_rows),
        constraints=tuple(map_constraint_info(row) for row in constraint_rows),
    )

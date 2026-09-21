"""Map PostgreSQL index metadata to public domain models."""

from collections.abc import Mapping

from pydbadminkit.domain.catalog import IndexDescription, IndexInfo
from pydbadminkit.domain.common import QualifiedName
from pydbadminkit.errors import InternalError


def _required_bool(value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError("boolean value is required")
    return value


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


def map_index_info(row: Mapping[str, object]) -> IndexInfo:
    """Map one pg_index summary row."""

    try:
        owner = row.get("owner")
        return IndexInfo(
            name=QualifiedName(
                schema=str(row["schema_name"]),
                name=str(row["name"]),
            ),
            table=QualifiedName(
                schema=str(row["table_schema"]),
                name=str(row["table_name"]),
            ),
            method=str(row["method"]),
            owner=None if owner is None else str(owner),
            unique=_required_bool(row["is_unique"]),
            primary=_required_bool(row["is_primary"]),
            valid=_required_bool(row["is_valid"]),
            ready=_required_bool(row["is_ready"]),
            size_bytes=_optional_int(row.get("size_bytes")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL index row mapping failed.") from error


def build_index_description(
    index_row: Mapping[str, object],
    detail_row: Mapping[str, object] | None,
) -> IndexDescription:
    """Build one detailed index aggregate."""

    if detail_row is None:
        raise InternalError("PostgreSQL index detail query returned no row.")

    try:
        definition = str(detail_row["definition"])
        predicate = detail_row.get("predicate")
        return IndexDescription(
            index=map_index_info(index_row),
            definition=definition,
            predicate=None if predicate is None else str(predicate),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL index detail mapping failed.") from error

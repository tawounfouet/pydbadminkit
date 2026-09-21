"""Map PostgreSQL schema rows to public domain models."""

from collections.abc import Mapping

from pydbadminkit.domain.catalog import SchemaInfo
from pydbadminkit.errors import InternalError


def map_schema_info(row: Mapping[str, object]) -> SchemaInfo:
    """Map one pg_namespace row."""

    try:
        is_system = row["is_system"]
        if not isinstance(is_system, bool):
            raise TypeError("is_system must be boolean")
        owner = row.get("owner")
        return SchemaInfo(
            name=str(row["name"]),
            owner=None if owner is None else str(owner),
            is_system=is_system,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL schema row mapping failed.") from error

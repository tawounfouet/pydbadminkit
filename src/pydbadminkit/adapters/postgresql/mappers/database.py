"""Map PostgreSQL database rows to public domain models."""

from collections.abc import Mapping

from pydbadminkit.domain.catalog import DatabaseInfo
from pydbadminkit.errors import InternalError


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise TypeError("expected bool or None")


def map_database_info(row: Mapping[str, object]) -> DatabaseInfo:
    """Map a PostgreSQL pg_database row to DatabaseInfo."""

    try:
        return DatabaseInfo(
            name=str(row["name"]),
            owner=_optional_str(row.get("owner")),
            encoding=_optional_str(row.get("encoding")),
            collation=_optional_str(row.get("collation")),
            allow_connections=_optional_bool(row.get("allow_connections")),
            connection_limit=_optional_int(row.get("connection_limit")),
            size_bytes=_optional_int(row.get("size_bytes")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL database row mapping failed.") from error

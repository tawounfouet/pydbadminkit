"""Map PostgreSQL role metadata to security domain models."""

from collections.abc import Mapping
from datetime import datetime

from pydbadminkit.domain.security import RoleInfo, RoleMembership
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
    raise TypeError("integer value is required")


def _optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    raise TypeError("datetime value is required")


def map_role_info(row: Mapping[str, object]) -> RoleInfo:
    """Map one pg_roles row."""

    try:
        name = str(row["name"])
        return RoleInfo(
            name=name,
            can_login=_required_bool(row["can_login"]),
            is_superuser=_required_bool(row["is_superuser"]),
            can_create_db=_required_bool(row["can_create_db"]),
            can_create_role=_required_bool(row["can_create_role"]),
            can_replicate=_required_bool(row["can_replicate"]),
            inherit=_required_bool(row["inherit"]),
            connection_limit=_optional_int(row.get("connection_limit")),
            valid_until=_optional_datetime(row.get("valid_until")),
            bypass_rls=_required_bool(row["bypass_rls"]),
            is_system=name.startswith("pg_"),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL role row mapping failed.") from error


def map_role_membership(row: Mapping[str, object]) -> RoleMembership:
    """Map one pg_auth_members row."""

    try:
        grantor = row.get("grantor_name")
        return RoleMembership(
            role=str(row["role_name"]),
            member=str(row["member_name"]),
            grantor=None if grantor is None else str(grantor),
            admin_option=_required_bool(row["admin_option"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL role membership mapping failed.") from error

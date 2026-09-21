"""Map PostgreSQL ownership rows."""

from collections.abc import Mapping

from pydbadminkit.domain.common import DatabaseObjectRef, DatabaseObjectType, QualifiedName
from pydbadminkit.domain.security import OwnershipInfo
from pydbadminkit.errors import InternalError


def map_ownership(row: Mapping[str, object]) -> OwnershipInfo:
    """Map one PostgreSQL ownership row."""

    try:
        object_type = DatabaseObjectType(str(row["object_type"]))
        schema_name = row.get("schema_name")
        return OwnershipInfo(
            owner=str(row["owner"]),
            object=DatabaseObjectRef(
                object_type=object_type,
                name=QualifiedName(
                    schema=None if schema_name is None else str(schema_name),
                    name=str(row["object_name"]),
                ),
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL ownership row mapping failed.") from error

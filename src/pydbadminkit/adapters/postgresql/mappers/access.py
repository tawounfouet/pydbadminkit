"""Map PostgreSQL ACL entries to direct access models."""

from collections.abc import Mapping

from pydbadminkit.domain.common import DatabaseObjectRef, DatabaseObjectType, QualifiedName
from pydbadminkit.domain.security import AccessType, DirectAccess
from pydbadminkit.errors import InternalError

_OBJECT_TYPE_BY_RELKIND = {
    "r": DatabaseObjectType.TABLE,
    "p": DatabaseObjectType.TABLE,
    "f": DatabaseObjectType.TABLE,
    "v": DatabaseObjectType.VIEW,
    "m": DatabaseObjectType.VIEW,
}


def map_direct_access(row: Mapping[str, object]) -> DirectAccess:
    """Map one explicit PostgreSQL ACL entry."""

    try:
        issuer = row.get("issuer")
        return DirectAccess(
            principal=str(row["principal"]),
            access_type=AccessType(str(row["access_type"]).upper()),
            object=DatabaseObjectRef(
                object_type=_OBJECT_TYPE_BY_RELKIND[str(row["relkind"])],
                name=QualifiedName(
                    schema=str(row["schema_name"]),
                    name=str(row["object_name"]),
                ),
            ),
            issuer=None if issuer is None else str(issuer),
            delegable=_required_bool(row["delegable"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL access row mapping failed.") from error


def _required_bool(value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError("boolean value is required")
    return value

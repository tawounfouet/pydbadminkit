"""Map PostgreSQL effective access rows."""

from collections.abc import Mapping

from pydbadminkit.domain.common import DatabaseObjectRef, DatabaseObjectType, QualifiedName
from pydbadminkit.domain.security import AccessSource, AccessType, EffectiveAccess
from pydbadminkit.errors import InternalError

_OBJECT_TYPE_BY_RELKIND = {
    "r": DatabaseObjectType.TABLE,
    "p": DatabaseObjectType.TABLE,
    "f": DatabaseObjectType.TABLE,
    "v": DatabaseObjectType.VIEW,
    "m": DatabaseObjectType.VIEW,
}

_SOURCE_FIELDS = (
    ("source_direct", AccessSource.DIRECT),
    ("source_inherited", AccessSource.INHERITED),
    ("source_public", AccessSource.PUBLIC),
    ("source_owner", AccessSource.OWNER),
    ("source_superuser", AccessSource.SUPERUSER),
)


def map_effective_access(row: Mapping[str, object]) -> EffectiveAccess:
    """Map one effective-access row with source attribution."""

    try:
        sources = tuple(source for field, source in _SOURCE_FIELDS if _required_bool(row[field]))
        return EffectiveAccess(
            principal=str(row["principal"]),
            access_type=AccessType(str(row["access_type"]).upper()),
            object=DatabaseObjectRef(
                object_type=_OBJECT_TYPE_BY_RELKIND[str(row["relkind"])],
                name=QualifiedName(
                    schema=str(row["schema_name"]),
                    name=str(row["object_name"]),
                ),
            ),
            sources=sources,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL effective access row mapping failed.") from error


def _required_bool(value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError("boolean value is required")
    return value

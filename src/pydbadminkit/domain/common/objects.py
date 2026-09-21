"""Generic database object references."""

from dataclasses import dataclass
from enum import StrEnum

from pydbadminkit.domain.common.names import QualifiedName


class DatabaseObjectType(StrEnum):
    """Initial cross-engine object types."""

    SERVER = "server"
    DATABASE = "database"
    SCHEMA = "schema"
    TABLE = "table"
    VIEW = "view"
    INDEX = "index"


@dataclass(frozen=True, slots=True)
class DatabaseObjectRef:
    """Typed logical reference to a database object."""

    object_type: DatabaseObjectType
    name: QualifiedName

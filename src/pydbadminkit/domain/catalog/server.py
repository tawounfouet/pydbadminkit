"""Server catalog models."""

from dataclasses import dataclass

from pydbadminkit.domain.common.database_version import DatabaseVersion
from pydbadminkit.domain.common.engine import DatabaseEngine


@dataclass(frozen=True, slots=True)
class ServerInfo:
    """Read-only summary of the connected database server."""

    engine: DatabaseEngine
    version: DatabaseVersion
    current_database: str | None = None
    current_user: str | None = None

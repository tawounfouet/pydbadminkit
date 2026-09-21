"""Map PostgreSQL server rows to public domain models."""

from collections.abc import Mapping

from pydbadminkit.adapters.postgresql.version import parse_server_version_num
from pydbadminkit.domain.catalog import ServerInfo
from pydbadminkit.domain.common import DatabaseEngine
from pydbadminkit.errors import InternalError


def map_server_info(row: Mapping[str, object]) -> ServerInfo:
    """Map a validated PostgreSQL server-info row."""

    try:
        raw_version = int(row["server_version_num"])
        current_database = str(row["current_database"])
        current_user = str(row["current_user"])
    except (KeyError, TypeError, ValueError) as error:
        raise InternalError("PostgreSQL server-info mapping failed.") from error

    return ServerInfo(
        engine=DatabaseEngine.POSTGRESQL,
        version=parse_server_version_num(raw_version).version,
        current_database=current_database,
        current_user=current_user,
    )

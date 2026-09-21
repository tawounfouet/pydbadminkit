"""PostgreSQL ServerPort implementation."""

from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.mappers.server import map_server_info
from pydbadminkit.adapters.postgresql.queries.server import SERVER_INFO, SERVER_INFO_QUERY_ID
from pydbadminkit.domain.catalog import ServerInfo
from pydbadminkit.errors import InternalError


class PostgreSQLServerAdapter:
    """Inspect the currently connected PostgreSQL server."""

    def __init__(self, executor: PostgreSQLExecutor) -> None:
        self._executor = executor

    def get_info(self) -> ServerInfo:
        row = self._executor.fetch_one(SERVER_INFO, query_id=SERVER_INFO_QUERY_ID)
        if row is None:
            raise InternalError("PostgreSQL server-info query returned no row.")
        return map_server_info(row)

"""Server application service."""

from pydbadminkit.domain.catalog.server import ServerInfo
from pydbadminkit.ports.server import ServerPort


class ServerService:
    """Application boundary for server inspection."""

    def __init__(self, server_port: ServerPort) -> None:
        self._server_port = server_port

    def get_info(self) -> ServerInfo:
        """Return server information from the configured adapter."""

        return self._server_port.get_info()

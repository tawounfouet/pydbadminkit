"""Database server inspection port."""

from typing import Protocol

from pydbadminkit.domain.catalog.server import ServerInfo


class ServerPort(Protocol):
    """Database server inspection contract."""

    def get_info(self) -> ServerInfo:
        """Return information about the currently connected server."""
        ...

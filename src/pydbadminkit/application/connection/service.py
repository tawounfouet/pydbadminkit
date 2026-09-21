"""Connection application service."""

from pydbadminkit.application.connection.resolver import ConnectionConfigResolver
from pydbadminkit.domain.connection.result import ConnectionTestResult
from pydbadminkit.ports.connection import ConnectionTesterPort


class ConnectionService:
    """Application boundary for connection operations."""

    def __init__(
        self,
        resolver: ConnectionConfigResolver,
        tester: ConnectionTesterPort,
    ) -> None:
        self._resolver = resolver
        self._tester = tester

    def test(self, profile_name: str) -> ConnectionTestResult:
        """Resolve and test one named connection profile."""

        return self._tester.test(self._resolver.resolve(profile_name))

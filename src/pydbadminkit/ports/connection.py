"""Connection testing port."""

from typing import Protocol

from pydbadminkit.domain.connection.resolved import ResolvedConnectionConfig
from pydbadminkit.domain.connection.result import ConnectionTestResult


class ConnectionTesterPort(Protocol):
    """Engine adapter contract for validating a resolved connection."""

    def test(self, config: ResolvedConnectionConfig) -> ConnectionTestResult:
        """Open the connection, verify it, and return safe diagnostics."""
        ...

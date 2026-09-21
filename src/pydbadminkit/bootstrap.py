"""Application dependency wiring.

The initial bootstrap is intentionally explicit and PostgreSQL-first.
"""

from pathlib import Path

from pydbadminkit.adapters.postgresql.connection import (
    PostgreSQLConnectionFactory,
    PostgreSQLConnectionTester,
)
from pydbadminkit.application.connection import ConnectionConfigResolver, ConnectionService
from pydbadminkit.infrastructure.config import (
    TomlConnectionProfileRepository,
    default_config_path,
)
from pydbadminkit.infrastructure.secrets import EnvironmentSecretProvider


def build_connection_service(config_path: Path | None = None) -> ConnectionService:
    """Build the initial PostgreSQL-first connection service."""

    repository = TomlConnectionProfileRepository(config_path or default_config_path())
    resolver = ConnectionConfigResolver(
        repository=repository,
        secret_providers=(EnvironmentSecretProvider(),),
    )
    factory = PostgreSQLConnectionFactory()
    tester = PostgreSQLConnectionTester(factory)
    return ConnectionService(resolver=resolver, tester=tester)

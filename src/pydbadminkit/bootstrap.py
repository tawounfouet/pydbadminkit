"""Application dependency wiring.

The initial bootstrap is intentionally explicit and PostgreSQL-first.
"""

from pathlib import Path

from pydbadminkit.adapters.postgresql import (
    PostgreSQLCapabilityAdapter,
    PostgreSQLCatalogAdapter,
    PostgreSQLConnectionFactory,
    PostgreSQLConnectionTester,
    PostgreSQLExecutor,
    PostgreSQLSecurityAdapter,
    PostgreSQLServerAdapter,
)
from pydbadminkit.application.capability import CapabilityService
from pydbadminkit.application.catalog import CatalogService
from pydbadminkit.application.connection import ConnectionConfigResolver, ConnectionService
from pydbadminkit.application.security import SecurityService
from pydbadminkit.application.server import ServerService
from pydbadminkit.domain.connection import ResolvedConnectionConfig
from pydbadminkit.infrastructure.config import (
    TomlConnectionProfileRepository,
    default_config_path,
)
from pydbadminkit.infrastructure.secrets import EnvironmentSecretProvider


def _build_connection_resolver(config_path: Path | None = None) -> ConnectionConfigResolver:
    repository = TomlConnectionProfileRepository(config_path or default_config_path())
    return ConnectionConfigResolver(
        repository=repository,
        secret_providers=(EnvironmentSecretProvider(),),
    )


def resolve_connection(
    profile_name: str,
    config_path: Path | None = None,
) -> ResolvedConnectionConfig:
    """Resolve one named connection profile."""

    return _build_connection_resolver(config_path).resolve(profile_name)


def build_connection_service(config_path: Path | None = None) -> ConnectionService:
    """Build the PostgreSQL-first connection service."""

    resolver = _build_connection_resolver(config_path)
    factory = PostgreSQLConnectionFactory()
    tester = PostgreSQLConnectionTester(factory)
    return ConnectionService(resolver=resolver, tester=tester)


def build_server_service(
    profile_name: str,
    config_path: Path | None = None,
) -> ServerService:
    """Build a server inspection service for one resolved profile."""

    config = resolve_connection(profile_name, config_path)
    executor = PostgreSQLExecutor(PostgreSQLConnectionFactory(), config)
    return ServerService(PostgreSQLServerAdapter(executor))


def build_catalog_service(
    profile_name: str,
    config_path: Path | None = None,
) -> CatalogService:
    """Build a catalog inspection service for one resolved profile."""

    config = resolve_connection(profile_name, config_path)
    executor = PostgreSQLExecutor(PostgreSQLConnectionFactory(), config)
    return CatalogService(PostgreSQLCatalogAdapter(executor))


def build_security_service(
    profile_name: str,
    config_path: Path | None = None,
) -> SecurityService:
    """Build a read-only security inspection service."""

    config = resolve_connection(profile_name, config_path)
    executor = PostgreSQLExecutor(PostgreSQLConnectionFactory(), config)
    return SecurityService(PostgreSQLSecurityAdapter(executor))


def build_capability_service() -> CapabilityService:
    """Build PostgreSQL capability discovery for the current release."""

    return CapabilityService(PostgreSQLCapabilityAdapter())

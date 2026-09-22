"""Application dependency wiring.

The initial bootstrap is intentionally explicit and PostgreSQL-first.
"""

from pathlib import Path

from pydbadminkit.adapters.postgresql import (
    PostgreSQLBackupAdapter,
    PostgreSQLCapabilityAdapter,
    PostgreSQLCatalogAdapter,
    PostgreSQLConnectionFactory,
    PostgreSQLConnectionTester,
    PostgreSQLExecutor,
    PostgreSQLRuntimeAdapter,
    PostgreSQLSecurityAdapter,
    PostgreSQLServerAdapter,
)
from pydbadminkit.application.capability import CapabilityService
from pydbadminkit.application.catalog import CatalogService
from pydbadminkit.application.connection import ConnectionConfigResolver, ConnectionService
from pydbadminkit.application.operations import BackupService, BackupValidationService
from pydbadminkit.application.runtime import RuntimeMutationService, RuntimeService
from pydbadminkit.application.security import SecurityMutationService, SecurityService
from pydbadminkit.application.server import ServerService
from pydbadminkit.domain.connection import ResolvedConnectionConfig
from pydbadminkit.infrastructure.audit import JsonlAuditSink, default_audit_path
from pydbadminkit.infrastructure.backup_files import LocalBackupFileStore
from pydbadminkit.infrastructure.config import (
    TomlConnectionProfileRepository,
    default_config_path,
)
from pydbadminkit.infrastructure.process import SubprocessRunner
from pydbadminkit.infrastructure.secrets import EnvironmentSecretProvider
from pydbadminkit.infrastructure.tools import PathToolResolver


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


def build_backup_service(
    profile_name: str,
    config_path: Path | None = None,
) -> BackupService:
    """Build logical PostgreSQL backup orchestration for one profile."""

    config = resolve_connection(profile_name, config_path)
    executor = PostgreSQLExecutor(PostgreSQLConnectionFactory(), config)
    runner = SubprocessRunner()
    file_store = LocalBackupFileStore()
    backup_adapter = PostgreSQLBackupAdapter(
        runner=runner,
        tool_resolver=PathToolResolver(runner),
        file_store=file_store,
        config=config,
        server_port=PostgreSQLServerAdapter(executor),
    )
    return BackupService(
        backup_port=backup_adapter,
        audit_port=JsonlAuditSink(default_audit_path()),
        config=config,
    )


def build_backup_validation_service() -> BackupValidationService:
    """Build connection-free local backup validation."""

    runner = SubprocessRunner()
    file_store = LocalBackupFileStore()
    backup_adapter = PostgreSQLBackupAdapter(
        runner=runner,
        tool_resolver=PathToolResolver(runner),
        file_store=file_store,
    )
    return BackupValidationService(
        backup_port=backup_adapter,
        file_store=file_store,
    )


def build_runtime_service(
    profile_name: str,
    config_path: Path | None = None,
) -> RuntimeService:
    """Build a read-only runtime inspection service."""

    config = resolve_connection(profile_name, config_path)
    executor = PostgreSQLExecutor(PostgreSQLConnectionFactory(), config)
    return RuntimeService(PostgreSQLRuntimeAdapter(executor))


def build_runtime_mutation_service(
    profile_name: str,
    config_path: Path | None = None,
) -> RuntimeMutationService:
    """Build guarded PostgreSQL runtime mutation orchestration."""

    config = resolve_connection(profile_name, config_path)
    executor = PostgreSQLExecutor(PostgreSQLConnectionFactory(), config)
    return RuntimeMutationService(
        mutation_port=PostgreSQLRuntimeAdapter(executor),
        audit_port=JsonlAuditSink(default_audit_path()),
        config=config,
    )


def build_security_service(
    profile_name: str,
    config_path: Path | None = None,
) -> SecurityService:
    """Build a read-only security inspection service."""

    config = resolve_connection(profile_name, config_path)
    executor = PostgreSQLExecutor(PostgreSQLConnectionFactory(), config)
    return SecurityService(PostgreSQLSecurityAdapter(executor))


def build_security_mutation_service(
    profile_name: str,
    config_path: Path | None = None,
) -> SecurityMutationService:
    """Build guarded PostgreSQL security mutation orchestration."""

    config = resolve_connection(profile_name, config_path)
    executor = PostgreSQLExecutor(PostgreSQLConnectionFactory(), config)
    return SecurityMutationService(
        mutation_port=PostgreSQLSecurityAdapter(executor),
        audit_port=JsonlAuditSink(default_audit_path()),
        config=config,
    )


def build_capability_service() -> CapabilityService:
    """Build PostgreSQL capability discovery for the current release."""

    runner = SubprocessRunner()
    return CapabilityService(PostgreSQLCapabilityAdapter(tool_resolver=PathToolResolver(runner)))

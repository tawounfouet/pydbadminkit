"""Resolve persisted connection profiles into runtime configuration."""

from collections.abc import Iterable

from pydbadminkit.domain.connection.profile import ConnectionProfileName
from pydbadminkit.domain.connection.resolved import ResolvedConnectionConfig
from pydbadminkit.domain.connection.secrets import SecretValue
from pydbadminkit.errors import SecretResolutionError
from pydbadminkit.ports.config import ConfigRepositoryPort
from pydbadminkit.ports.secrets import SecretProviderPort


class ConnectionConfigResolver:
    """Resolve a profile and its referenced secret for adapter use."""

    def __init__(
        self,
        repository: ConfigRepositoryPort,
        secret_providers: Iterable[SecretProviderPort],
    ) -> None:
        self._repository = repository
        self._secret_providers = {provider.name: provider for provider in secret_providers}

    def resolve(self, profile_name: str) -> ResolvedConnectionConfig:
        name = ConnectionProfileName(profile_name)
        profile = self._repository.get_connection_profile(name)

        password: SecretValue | None = None
        if profile.secret is not None:
            provider = self._secret_providers.get(profile.secret.provider)
            if provider is None:
                raise SecretResolutionError(
                    f"Secret provider '{profile.secret.provider}' is not registered."
                )
            password = provider.resolve(profile.secret)

        return ResolvedConnectionConfig(
            name=profile.name,
            engine=profile.engine,
            host=profile.host,
            port=profile.port,
            database=profile.database,
            username=profile.username,
            password=password,
            environment=profile.environment,
            read_only=profile.read_only,
            ssl=profile.ssl,
            timeouts=profile.timeouts,
        )

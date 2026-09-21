"""Configuration repository port."""

from typing import Protocol

from pydbadminkit.domain.connection.profile import ConnectionProfile, ConnectionProfileName


class ConfigRepositoryPort(Protocol):
    """Connection-profile configuration contract."""

    def get_connection_profile(self, name: ConnectionProfileName) -> ConnectionProfile:
        """Return one configured connection profile."""
        ...

    def list_connection_profiles(self) -> tuple[ConnectionProfile, ...]:
        """Return configured profiles in deterministic name order."""
        ...

"""Secret provider port."""

from typing import Protocol

from pydbadminkit.domain.connection.secrets import SecretReference, SecretValue


class SecretProviderPort(Protocol):
    """Resolve secret references without exposing provider internals."""

    @property
    def name(self) -> str:
        """Provider identifier used by SecretReference."""
        ...

    def resolve(self, reference: SecretReference) -> SecretValue:
        """Resolve a secret reference."""
        ...

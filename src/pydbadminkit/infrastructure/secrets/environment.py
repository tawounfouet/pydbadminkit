"""Environment-variable secret provider."""

import os

from pydbadminkit.domain.connection.secrets import SecretReference, SecretValue
from pydbadminkit.errors import SecretResolutionError


class EnvironmentSecretProvider:
    """Resolve secrets from process environment variables."""

    name = "env"

    def resolve(self, reference: SecretReference) -> SecretValue:
        if reference.provider != self.name:
            raise SecretResolutionError(
                f"Secret reference provider '{reference.provider}' cannot be handled by '{self.name}'."
            )

        value = os.getenv(reference.reference)
        if value is None:
            raise SecretResolutionError(
                f"Environment variable '{reference.reference}' is not defined."
            )
        return SecretValue(value)

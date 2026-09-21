"""Secret references.

This module deliberately models references to secrets, never resolved secret values.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SecretReference:
    """Reference describing where a secret must be resolved."""

    provider: str
    reference: str

    def __post_init__(self) -> None:
        if not self.provider or self.provider.isspace():
            raise ValueError("secret provider must not be blank")
        if not self.reference or self.reference.isspace():
            raise ValueError("secret reference must not be blank")

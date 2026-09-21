"""Secret references and redacted runtime secret values."""

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


class SecretValue:
    """In-memory secret wrapper whose string representations are always redacted."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        """Return the raw value only at the infrastructure/adapter boundary."""

        return self._value

    def __repr__(self) -> str:
        return "SecretValue(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"

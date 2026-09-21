"""Connection profile identity."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConnectionProfileName:
    """Validated connection profile name."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or self.value.isspace():
            raise ValueError("connection profile name must not be blank")

    def __str__(self) -> str:
        return self.value

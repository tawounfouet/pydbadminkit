"""Schema catalog models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SchemaInfo:
    """Read-only summary of a database schema."""

    name: str
    owner: str | None = None
    is_system: bool = False

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("schema name must not be blank")

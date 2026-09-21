"""Database catalog models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatabaseInfo:
    """Read-only summary of a database visible to the current principal."""

    name: str
    owner: str | None = None
    encoding: str | None = None
    collation: str | None = None
    allow_connections: bool | None = None
    connection_limit: int | None = None
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("database name must not be blank")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")

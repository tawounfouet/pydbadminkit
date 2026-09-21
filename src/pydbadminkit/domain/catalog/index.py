"""Index catalog models."""

from dataclasses import dataclass

from pydbadminkit.domain.common.names import QualifiedName


@dataclass(frozen=True, slots=True)
class IndexInfo:
    """Read-only summary of a database index."""

    name: QualifiedName
    table: QualifiedName
    method: str
    owner: str | None = None
    unique: bool = False
    primary: bool = False
    valid: bool = True
    ready: bool = True
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        if not self.method or self.method.isspace():
            raise ValueError("index method must not be blank")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")


@dataclass(frozen=True, slots=True)
class IndexDescription:
    """Detailed immutable index description."""

    index: IndexInfo
    definition: str
    predicate: str | None = None

    def __post_init__(self) -> None:
        if not self.definition or self.definition.isspace():
            raise ValueError("index definition must not be blank")

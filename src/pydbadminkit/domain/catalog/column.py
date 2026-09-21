"""Column catalog models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ColumnInfo:
    """Read-only description of a table column."""

    name: str
    position: int
    data_type: str
    nullable: bool
    default: str | None = None
    identity: bool = False
    generated: bool = False
    comment: str | None = None

    def __post_init__(self) -> None:
        if not self.name or self.name.isspace():
            raise ValueError("column name must not be blank")
        if self.position < 1:
            raise ValueError("column position must be >= 1")
        if not self.data_type or self.data_type.isspace():
            raise ValueError("data_type must not be blank")

"""Logical database object names."""

from dataclasses import dataclass


def _require_non_blank(value: str, field: str) -> None:
    if not value or value.isspace():
        raise ValueError(f"{field} must not be blank")


@dataclass(frozen=True, slots=True)
class QualifiedName:
    """Logical object name independent of SQL quoting rules."""

    name: str
    schema: str | None = None
    database: str | None = None

    def __post_init__(self) -> None:
        _require_non_blank(self.name, "name")
        if self.schema is not None:
            _require_non_blank(self.schema, "schema")
        if self.database is not None:
            _require_non_blank(self.database, "database")

    def __str__(self) -> str:
        parts = (value for value in (self.database, self.schema, self.name) if value is not None)
        return ".".join(parts)


def parse_qualified_name(value: str) -> QualifiedName:
    """Parse name, schema.name, or database.schema.name.

    SQL-quoted identifiers are intentionally outside the initial parser scope.
    """

    _require_non_blank(value, "qualified name")
    parts = value.split(".")
    if any(not part or part.isspace() for part in parts):
        raise ValueError("qualified name contains a blank component")

    if len(parts) == 1:
        return QualifiedName(name=parts[0])
    if len(parts) == 2:
        return QualifiedName(schema=parts[0], name=parts[1])
    if len(parts) == 3:
        return QualifiedName(database=parts[0], schema=parts[1], name=parts[2])

    raise ValueError("qualified name must contain at most three components")

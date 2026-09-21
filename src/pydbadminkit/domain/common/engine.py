"""Supported database engines."""

from enum import StrEnum


class DatabaseEngine(StrEnum):
    """Database engine identifiers used by the public domain model."""

    POSTGRESQL = "postgresql"

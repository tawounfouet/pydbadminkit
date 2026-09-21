"""CLI output format contract."""

from enum import StrEnum


class OutputFormat(StrEnum):
    """Supported CLI output formats."""

    TABLE = "table"
    JSON = "json"
    YAML = "yaml"

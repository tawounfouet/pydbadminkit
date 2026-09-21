"""Shared CLI execution context."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CLIContext:
    """Global CLI options propagated to subcommands."""

    connection_profile: str | None = None
    config_path: Path | None = None

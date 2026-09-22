"""External process execution port."""

from collections.abc import Mapping
from typing import Protocol

from pydbadminkit.domain.operations import ProcessResult


class ProcessRunnerPort(Protocol):
    """Run one validated executable without invoking a shell."""

    def run(
        self,
        args: list[str],
        env: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        """Execute one child process."""
        ...

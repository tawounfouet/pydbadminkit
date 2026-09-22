"""External PostgreSQL tool resolution."""

import shutil

from pydbadminkit.domain.operations import ExternalTool
from pydbadminkit.ports.process import ProcessRunnerPort


class PathToolResolver:
    """Resolve native utilities from PATH and query their version."""

    def __init__(self, runner: ProcessRunnerPort) -> None:
        self._runner = runner

    def resolve(self, name: str) -> ExternalTool:
        if not name or name.isspace():
            raise ValueError("tool name must not be blank")
        if any(separator in name for separator in ("/", "\\")):
            raise ValueError("tool name must not contain path separators")

        path = shutil.which(name)
        if path is None:
            return ExternalTool(
                name=name,
                path=None,
                version=None,
                available=False,
            )

        result = self._runner.run([path, "--version"], timeout_seconds=10)
        version = None
        if result.return_code == 0:
            version = _first_non_blank_line(result.stdout, result.stderr)

        return ExternalTool(
            name=name,
            path=path,
            version=version,
            available=True,
        )


def _first_non_blank_line(*values: str) -> str | None:
    for value in values:
        for line in value.splitlines():
            if line.strip():
                return line.strip()
    return None

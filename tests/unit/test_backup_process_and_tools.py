"""Unit tests for process execution and tool resolution."""

import sys
from collections.abc import Mapping

import pytest

from pydbadminkit.domain.operations import ProcessResult
from pydbadminkit.errors import OperationTimeoutError
from pydbadminkit.infrastructure.process import SubprocessRunner
from pydbadminkit.infrastructure.tools import PathToolResolver

pytestmark = [pytest.mark.unit, pytest.mark.backup]


class FakeRunner:
    def __init__(self, result: ProcessResult) -> None:
        self.result = result
        self.calls: list[tuple[list[str], Mapping[str, str] | None, float | None]] = []

    def run(
        self,
        args: list[str],
        env: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        self.calls.append((args, env, timeout_seconds))
        return self.result


def test_subprocess_runner_executes_without_shell() -> None:
    result = SubprocessRunner().run(
        [sys.executable, "-c", "print('backup-ok')"],
        timeout_seconds=5,
    )

    assert result.return_code == 0
    assert result.stdout.strip() == "backup-ok"
    assert result.duration_ms >= 0


def test_subprocess_runner_maps_timeout() -> None:
    with pytest.raises(OperationTimeoutError):
        SubprocessRunner().run(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            timeout_seconds=0.05,
        )


def test_tool_resolver_reports_missing_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pydbadminkit.infrastructure.tools.shutil.which",
        lambda name: None,
    )
    runner = FakeRunner(ProcessResult(0, "", "", 1))

    tool = PathToolResolver(runner).resolve("pg_dump")

    assert tool.available is False
    assert tool.path is None
    assert runner.calls == []


def test_tool_resolver_reads_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "pydbadminkit.infrastructure.tools.shutil.which",
        lambda name: "/usr/bin/pg_dump",
    )
    runner = FakeRunner(
        ProcessResult(
            return_code=0,
            stdout="pg_dump (PostgreSQL) 18.1\n",
            stderr="",
            duration_ms=1,
        )
    )

    tool = PathToolResolver(runner).resolve("pg_dump")

    assert tool.available is True
    assert tool.version == "pg_dump (PostgreSQL) 18.1"
    assert runner.calls[0][0] == ["/usr/bin/pg_dump", "--version"]

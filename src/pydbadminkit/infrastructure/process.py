"""Secret-safe child process execution."""

import os
import subprocess
from collections.abc import Mapping
from pathlib import Path
from time import perf_counter

from pydbadminkit.domain.operations import ProcessResult
from pydbadminkit.errors import ExternalToolError, OperationTimeoutError


class SubprocessRunner:
    """Run external tools with argument arrays and no shell."""

    def run(
        self,
        args: list[str],
        env: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        if not args or not args[0]:
            raise ValueError("process args require an executable")

        child_env = os.environ.copy()
        if env is not None:
            child_env.update(env)

        started = perf_counter()
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=child_env,
            shell=False,
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as error:
            _terminate_process(process)
            tool_name = Path(args[0]).name
            raise OperationTimeoutError(
                f"External process '{tool_name}' exceeded its timeout."
            ) from error
        except KeyboardInterrupt as error:
            _terminate_process(process)
            tool_name = Path(args[0]).name
            raise ExternalToolError(
                f"External process '{tool_name}' was interrupted by the operator."
            ) from error

        duration_ms = int((perf_counter() - started) * 1000)
        return ProcessResult(
            return_code=process.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
        )


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()

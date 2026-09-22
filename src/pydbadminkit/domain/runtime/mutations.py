"""Runtime mutation command and adapter-result models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CancelQueryCommand:
    """Request cancellation of the current query for one backend PID."""

    pid: int

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("cancel query pid must be > 0")


@dataclass(frozen=True, slots=True)
class TerminateSessionCommand:
    """Request termination of one client backend session."""

    pid: int

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("terminate session pid must be > 0")


@dataclass(frozen=True, slots=True)
class BackendSignalResult:
    """Atomic adapter result for one guarded backend signal request."""

    pid: int
    target_exists: bool
    self_target: bool
    client_backend: bool
    changed: bool
    backend_type: str | None = None
    active_query: bool | None = None

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("backend signal pid must be > 0")

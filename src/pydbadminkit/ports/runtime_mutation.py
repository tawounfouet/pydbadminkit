"""Runtime mutation port."""

from typing import Protocol

from pydbadminkit.domain.runtime import (
    BackendSignalResult,
    CancelQueryCommand,
    TerminateSessionCommand,
)


class RuntimeMutationPort(Protocol):
    """Engine-specific execution contract for guarded runtime mutations."""

    def cancel_query(self, command: CancelQueryCommand) -> BackendSignalResult:
        """Request cancellation of one backend's current query."""
        ...

    def terminate_session(self, command: TerminateSessionCommand) -> BackendSignalResult:
        """Request termination of one client backend session."""
        ...

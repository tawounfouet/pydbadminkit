"""Unit tests for runtime mutation domain models."""

import pytest

from pydbadminkit.domain.runtime import (
    BackendSignalResult,
    CancelQueryCommand,
    TerminateSessionCommand,
)

pytestmark = [pytest.mark.unit, pytest.mark.runtime]


def test_runtime_mutation_models_accept_valid_values() -> None:
    cancel = CancelQueryCommand(pid=101)
    terminate = TerminateSessionCommand(pid=102)
    result = BackendSignalResult(
        pid=101,
        target_exists=True,
        self_target=False,
        client_backend=True,
        changed=True,
        backend_type="client backend",
        active_query=True,
    )

    assert cancel.pid == 101
    assert terminate.pid == 102
    assert result.changed is True
    assert result.active_query is True


@pytest.mark.parametrize(
    "factory",
    [
        lambda: CancelQueryCommand(pid=0),
        lambda: TerminateSessionCommand(pid=-1),
        lambda: BackendSignalResult(
            pid=0,
            target_exists=True,
            self_target=False,
            client_backend=True,
            changed=False,
        ),
    ],
)
def test_runtime_mutation_models_reject_invalid_pid(factory: object) -> None:
    with pytest.raises(ValueError, match="pid"):
        factory()  # type: ignore[operator]

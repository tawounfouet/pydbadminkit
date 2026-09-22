"""Stable 0.4.0 Runtime Administration public-contract tests."""

import pytest

from pydbadminkit.adapters.postgresql.capabilities import PostgreSQLCapabilityAdapter
from pydbadminkit.application.runtime import RuntimeMutationService, RuntimeService
from pydbadminkit.domain.common import CapabilityAvailability
from pydbadminkit.domain.runtime import (
    BackendSignalResult,
    BlockingRelation,
    CancelQueryCommand,
    LockInfo,
    QueryInfo,
    SessionInfo,
    SessionState,
    TerminateSessionCommand,
    TransactionInfo,
    WaitInfo,
)
from pydbadminkit.ports import RuntimeMutationPort, RuntimePort

pytestmark = [pytest.mark.unit, pytest.mark.runtime]


def test_runtime_public_api_exports_stable_040_symbols() -> None:
    exported = {
        BackendSignalResult,
        BlockingRelation,
        CancelQueryCommand,
        LockInfo,
        QueryInfo,
        RuntimeMutationPort,
        RuntimeMutationService,
        RuntimePort,
        RuntimeService,
        SessionInfo,
        SessionState,
        TerminateSessionCommand,
        TransactionInfo,
        WaitInfo,
    }

    assert len(exported) == 14


def test_runtime_040_capabilities_are_available() -> None:
    adapter = PostgreSQLCapabilityAdapter()
    names = {
        "runtime.session.list",
        "runtime.query.list",
        "runtime.transaction.list",
        "runtime.wait.list",
        "runtime.lock.list",
        "runtime.blocking.list",
        "runtime.query.cancel",
        "runtime.session.terminate",
    }

    statuses = {name: adapter.get_capability(name) for name in names}

    assert set(statuses) == names
    assert all(
        status.availability is CapabilityAvailability.AVAILABLE for status in statuses.values()
    )


def test_runtime_mutation_commands_keep_stable_operation_names() -> None:
    assert CancelQueryCommand(pid=101).pid == 101
    assert TerminateSessionCommand(pid=102).pid == 102

    operation_names = {
        "runtime.query.cancel",
        "runtime.session.terminate",
    }

    capabilities = {
        item.name
        for item in PostgreSQLCapabilityAdapter().list_capabilities()
        if item.name.startswith("runtime.")
    }

    assert operation_names <= capabilities

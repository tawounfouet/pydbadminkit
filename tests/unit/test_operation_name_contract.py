"""Stable guarded mutation operation-name contract."""

import pytest

from pydbadminkit.domain.common import OperationName

pytestmark = pytest.mark.unit

EXPECTED_OPERATION_NAMES = (
    "backup.create",
    "backup.restore",
    "maintenance.analyze",
    "maintenance.reindex",
    "maintenance.vacuum",
    "runtime.query.cancel",
    "runtime.session.terminate",
    "security.access.grant",
    "security.access.revoke",
    "security.membership.add",
    "security.membership.remove",
    "security.role.alter",
    "security.role.create",
    "security.role.drop",
)


def test_operation_names_match_frozen_contract() -> None:
    assert tuple(operation.value for operation in OperationName) == EXPECTED_OPERATION_NAMES

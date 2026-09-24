"""Stable CLI process exit-code contract."""

import pytest

from pydbadminkit.cli.errors import exit_code_for_error
from pydbadminkit.errors import (
    AuthenticationError,
    AuthorizationError,
    BackupError,
    CapabilityNotAvailableError,
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
    DatabaseOperationError,
    ExternalToolError,
    InternalError,
    MaintenanceError,
    OperationTimeoutError,
    PyDBAdminError,
    ResourceNotFoundError,
    RestoreError,
    SafetyPolicyError,
    ValidationError,
)

pytestmark = [pytest.mark.unit, pytest.mark.cli]


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (PyDBAdminError("failure"), 1),
        (ValidationError("invalid"), 1),
        (DatabaseOperationError("database failure"), 1),
        (InternalError("internal failure"), 1),
        (ConfigurationError("configuration failure"), 2),
        (DatabaseConnectionError("connection failure"), 3),
        (AuthenticationError("authentication failure"), 4),
        (AuthorizationError("authorization failure"), 4),
        (ResourceNotFoundError("missing"), 5),
        (CapabilityNotAvailableError("unsupported"), 6),
        (SafetyPolicyError("denied"), 7),
        (ExternalToolError("tool failure"), 8),
        (BackupError("backup failure"), 8),
        (RestoreError("restore failure"), 8),
        (MaintenanceError("maintenance failure"), 8),
        (DatabaseConnectionTimeoutError("connection timeout"), 9),
        (OperationTimeoutError("operation timeout"), 9),
    ],
)
def test_error_exit_codes_are_frozen(error: PyDBAdminError, expected: int) -> None:
    assert exit_code_for_error(error) == expected

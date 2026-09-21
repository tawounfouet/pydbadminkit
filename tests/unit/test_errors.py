"""Unit tests for the public error model."""

import pytest

from pydbadminkit.domain.common import DatabaseEngine, EnvironmentName
from pydbadminkit.errors import (
    DatabaseConnectionTimeoutError,
    PyDBAdminError,
    ResourceNotFoundError,
)
from pydbadminkit.errors.codes import ErrorCode
from pydbadminkit.errors.context import ErrorContext

pytestmark = pytest.mark.unit


def test_error_preserves_safe_context() -> None:
    context = ErrorContext(
        operation="catalog.database.list",
        engine=DatabaseEngine.POSTGRESQL,
        environment=EnvironmentName.DEVELOPMENT,
    )
    error = PyDBAdminError("failed", context=context)

    assert str(error) == "failed"
    assert error.context is context


def test_database_connection_timeout_is_retryable() -> None:
    error = DatabaseConnectionTimeoutError("timeout")
    assert error.retryable is True
    assert error.code is ErrorCode.CONNECTION_TIMEOUT


def test_resource_not_found_has_stable_machine_code() -> None:
    error = ResourceNotFoundError("missing")
    assert error.code is ErrorCode.RESOURCE_NOT_FOUND

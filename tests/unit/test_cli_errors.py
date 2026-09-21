"""Unit tests for CLI error-to-exit-code mapping."""

import pytest

from pydbadminkit.cli.errors import exit_code_for_error
from pydbadminkit.errors import (
    AuthenticationError,
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
    ResourceNotFoundError,
)

pytestmark = pytest.mark.unit


def test_cli_error_exit_codes() -> None:
    assert exit_code_for_error(ConfigurationError("bad config")) == 2
    assert exit_code_for_error(DatabaseConnectionError("offline")) == 3
    assert exit_code_for_error(AuthenticationError("bad auth")) == 4
    assert exit_code_for_error(ResourceNotFoundError("missing")) == 5
    assert exit_code_for_error(DatabaseConnectionTimeoutError("timeout")) == 9

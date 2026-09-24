"""Stable machine error-code contract."""

import re

import pytest

from pydbadminkit.errors import ErrorCode

pytestmark = pytest.mark.unit

EXPECTED_ERROR_CODES = (
    "CONFIGURATION_ERROR",
    "PROFILE_NOT_FOUND",
    "SECRET_RESOLUTION_ERROR",
    "CONNECTION_ERROR",
    "CONNECTION_TIMEOUT",
    "AUTHENTICATION_ERROR",
    "AUTHORIZATION_ERROR",
    "DATABASE_OPERATION_ERROR",
    "RESOURCE_NOT_FOUND",
    "RESOURCE_ALREADY_EXISTS",
    "CAPABILITY_UNAVAILABLE",
    "VALIDATION_ERROR",
    "SAFETY_POLICY_ERROR",
    "POLICY_DENIED",
    "CONFIRMATION_REQUIRED",
    "AUDIT_UNAVAILABLE",
    "BACKUP_ERROR",
    "BACKUP_VALIDATION_ERROR",
    "RESTORE_ERROR",
    "RESTORE_VALIDATION_ERROR",
    "MAINTENANCE_ERROR",
    "CHECKSUM_MISMATCH",
    "FILE_COLLISION",
    "UNSAFE_PATH",
    "EXTERNAL_TOOL_ERROR",
    "TOOL_NOT_FOUND",
    "TOOL_VERSION_MISMATCH",
    "TOOL_EXECUTION_ERROR",
    "OPERATION_TIMEOUT",
    "INTERNAL_ERROR",
)


def test_error_codes_match_frozen_contract() -> None:
    assert tuple(code.value for code in ErrorCode) == EXPECTED_ERROR_CODES


def test_error_code_names_equal_wire_values() -> None:
    for code in ErrorCode:
        assert code.name == code.value
        assert re.fullmatch(r"[A-Z][A-Z0-9_]*", code.value)

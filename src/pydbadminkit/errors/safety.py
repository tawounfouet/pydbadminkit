"""Safety and audit errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class SafetyPolicyError(PyDBAdminError):
    """Base class for mutation safety failures."""

    code = ErrorCode.SAFETY_POLICY_ERROR


class PolicyDeniedError(SafetyPolicyError):
    """A safety policy explicitly denied the operation."""

    code = ErrorCode.POLICY_DENIED


class ConfirmationRequiredError(SafetyPolicyError):
    """Required proof of operator intent was not supplied."""

    code = ErrorCode.CONFIRMATION_REQUIRED


class AuditUnavailableError(SafetyPolicyError):
    """Audit persistence is unavailable for a mutation."""

    code = ErrorCode.AUDIT_UNAVAILABLE

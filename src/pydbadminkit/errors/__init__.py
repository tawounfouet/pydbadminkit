"""Public PyDBAdminKit error hierarchy."""

from pydbadminkit.errors.backup import (
    BackupError,
    BackupValidationError,
    ChecksumMismatchError,
    FileCollisionError,
    UnsafePathError,
)
from pydbadminkit.errors.base import PyDBAdminError, ValidationError
from pydbadminkit.errors.capability import CapabilityNotAvailableError
from pydbadminkit.errors.configuration import (
    ConfigurationError,
    ProfileNotFoundError,
    SecretResolutionError,
)
from pydbadminkit.errors.connection import (
    AuthenticationError,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
)
from pydbadminkit.errors.database import DatabaseOperationError
from pydbadminkit.errors.internal import InternalError
from pydbadminkit.errors.operation import OperationTimeoutError
from pydbadminkit.errors.resource import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from pydbadminkit.errors.safety import (
    AuditUnavailableError,
    ConfirmationRequiredError,
    PolicyDeniedError,
    SafetyPolicyError,
)
from pydbadminkit.errors.security import AuthorizationError
from pydbadminkit.errors.tools import (
    ExternalToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolVersionMismatchError,
)

__all__ = [
    "AuditUnavailableError",
    "AuthenticationError",
    "AuthorizationError",
    "BackupError",
    "BackupValidationError",
    "CapabilityNotAvailableError",
    "ChecksumMismatchError",
    "ConfigurationError",
    "ConfirmationRequiredError",
    "DatabaseConnectionError",
    "DatabaseConnectionTimeoutError",
    "DatabaseOperationError",
    "ExternalToolError",
    "FileCollisionError",
    "InternalError",
    "OperationTimeoutError",
    "PolicyDeniedError",
    "ProfileNotFoundError",
    "PyDBAdminError",
    "ResourceAlreadyExistsError",
    "ResourceNotFoundError",
    "SafetyPolicyError",
    "SecretResolutionError",
    "ToolExecutionError",
    "ToolNotFoundError",
    "ToolVersionMismatchError",
    "UnsafePathError",
    "ValidationError",
]

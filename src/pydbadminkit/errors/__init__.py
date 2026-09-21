"""Public PyDBAdminKit error hierarchy."""

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

__all__ = [
    "AuditUnavailableError",
    "AuthenticationError",
    "AuthorizationError",
    "CapabilityNotAvailableError",
    "ConfigurationError",
    "ConfirmationRequiredError",
    "DatabaseConnectionError",
    "DatabaseConnectionTimeoutError",
    "DatabaseOperationError",
    "InternalError",
    "PolicyDeniedError",
    "ProfileNotFoundError",
    "PyDBAdminError",
    "ResourceAlreadyExistsError",
    "ResourceNotFoundError",
    "SafetyPolicyError",
    "SecretResolutionError",
    "ValidationError",
]

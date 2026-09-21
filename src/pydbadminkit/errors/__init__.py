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
from pydbadminkit.errors.security import AuthorizationError

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "CapabilityNotAvailableError",
    "ConfigurationError",
    "DatabaseConnectionError",
    "DatabaseConnectionTimeoutError",
    "DatabaseOperationError",
    "InternalError",
    "ProfileNotFoundError",
    "PyDBAdminError",
    "ResourceAlreadyExistsError",
    "ResourceNotFoundError",
    "SecretResolutionError",
    "ValidationError",
]

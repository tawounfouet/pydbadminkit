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
from pydbadminkit.errors.internal import InternalError
from pydbadminkit.errors.resource import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)

__all__ = [
    "AuthenticationError",
    "CapabilityNotAvailableError",
    "ConfigurationError",
    "DatabaseConnectionError",
    "DatabaseConnectionTimeoutError",
    "InternalError",
    "ProfileNotFoundError",
    "PyDBAdminError",
    "ResourceAlreadyExistsError",
    "ResourceNotFoundError",
    "SecretResolutionError",
    "ValidationError",
]

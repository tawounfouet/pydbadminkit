"""Configuration-related public errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class ConfigurationError(PyDBAdminError):
    """Invalid or unusable PyDBAdminKit configuration."""

    code = ErrorCode.CONFIGURATION_ERROR


class ProfileNotFoundError(ConfigurationError):
    """Requested connection profile does not exist."""

    code = ErrorCode.PROFILE_NOT_FOUND


class SecretResolutionError(ConfigurationError):
    """A configured secret reference could not be resolved."""

    code = ErrorCode.SECRET_RESOLUTION_ERROR

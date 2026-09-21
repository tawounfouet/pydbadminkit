"""Database connection errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class DatabaseConnectionError(PyDBAdminError):
    """Database connection could not be established or maintained."""

    code = ErrorCode.CONNECTION_ERROR


class DatabaseConnectionTimeoutError(DatabaseConnectionError):
    """Database connection did not complete before its deadline."""

    code = ErrorCode.CONNECTION_TIMEOUT
    retryable = True


class AuthenticationError(DatabaseConnectionError):
    """Database authentication failed."""

    code = ErrorCode.AUTHENTICATION_ERROR

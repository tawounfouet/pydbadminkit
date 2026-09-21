"""Security and authorization errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class AuthorizationError(PyDBAdminError):
    """Authenticated principal is not authorized for an operation."""

    code = ErrorCode.AUTHORIZATION_ERROR

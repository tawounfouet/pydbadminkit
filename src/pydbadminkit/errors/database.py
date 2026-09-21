"""Database-operation errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class DatabaseOperationError(PyDBAdminError):
    """Database operation failed without a more specific public error."""

    code = ErrorCode.DATABASE_OPERATION_ERROR

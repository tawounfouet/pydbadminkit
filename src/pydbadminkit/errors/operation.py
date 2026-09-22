"""Long-running operation errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class OperationTimeoutError(PyDBAdminError):
    """A long-running operation exceeded its explicit timeout."""

    code = ErrorCode.OPERATION_TIMEOUT

"""Unexpected internal error type."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class InternalError(PyDBAdminError):
    """Unexpected PyDBAdminKit failure that is not a user/domain error."""

    code = ErrorCode.INTERNAL_ERROR

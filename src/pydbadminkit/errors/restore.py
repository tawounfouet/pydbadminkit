"""Restore operation errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class RestoreError(PyDBAdminError):
    """Base class for logical restore failures."""

    code = ErrorCode.RESTORE_ERROR


class RestoreValidationError(RestoreError):
    """Restore preflight or post-restore verification failed."""

    code = ErrorCode.RESTORE_VALIDATION_ERROR

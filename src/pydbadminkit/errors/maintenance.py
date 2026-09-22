"""Maintenance operation errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class MaintenanceError(PyDBAdminError):
    """Base class for maintenance failures."""

    code = ErrorCode.MAINTENANCE_ERROR

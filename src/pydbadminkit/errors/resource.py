"""Resource lookup errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class ResourceNotFoundError(PyDBAdminError):
    """Requested database resource is missing or not visible."""

    code = ErrorCode.RESOURCE_NOT_FOUND


class ResourceAlreadyExistsError(PyDBAdminError):
    """Requested resource creation conflicts with an existing resource."""

    code = ErrorCode.RESOURCE_ALREADY_EXISTS

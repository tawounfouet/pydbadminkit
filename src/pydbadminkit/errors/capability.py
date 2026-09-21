"""Capability-related public errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class CapabilityNotAvailableError(PyDBAdminError):
    """A requested capability cannot be used in the current context."""

    code = ErrorCode.CAPABILITY_UNAVAILABLE

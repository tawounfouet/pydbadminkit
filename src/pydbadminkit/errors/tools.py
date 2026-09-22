"""External PostgreSQL tool errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class ExternalToolError(PyDBAdminError):
    """Base class for native-tool failures."""

    code = ErrorCode.EXTERNAL_TOOL_ERROR


class ToolNotFoundError(ExternalToolError):
    """A required native executable could not be resolved."""

    code = ErrorCode.TOOL_NOT_FOUND


class ToolVersionMismatchError(ExternalToolError):
    """Resolved native-tool version is incompatible with the requested operation."""

    code = ErrorCode.TOOL_VERSION_MISMATCH


class ToolExecutionError(ExternalToolError):
    """Native tool returned a non-zero process result."""

    code = ErrorCode.TOOL_EXECUTION_ERROR

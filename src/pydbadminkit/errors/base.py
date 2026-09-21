"""Base error types."""

from typing import ClassVar

from pydbadminkit.errors.codes import ErrorCode
from pydbadminkit.errors.context import ErrorContext


class PyDBAdminError(Exception):
    """Root exception for expected PyDBAdminKit operational failures."""

    code: ClassVar[ErrorCode] = ErrorCode.INTERNAL_ERROR
    retryable: ClassVar[bool] = False

    def __init__(
        self,
        message: str,
        *,
        context: ErrorContext | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context
        self.hint = hint

    def __str__(self) -> str:
        return self.message


class ValidationError(PyDBAdminError):
    """Invalid operation input crossing an application boundary."""

    code = ErrorCode.VALIDATION_ERROR

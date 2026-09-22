"""Backup operation errors."""

from pydbadminkit.errors.base import PyDBAdminError
from pydbadminkit.errors.codes import ErrorCode


class BackupError(PyDBAdminError):
    """Base class for logical backup failures."""

    code = ErrorCode.BACKUP_ERROR


class BackupValidationError(BackupError):
    """Backup artifact validation failed."""

    code = ErrorCode.BACKUP_VALIDATION_ERROR


class ChecksumMismatchError(BackupValidationError):
    """Stored and computed backup checksums differ."""

    code = ErrorCode.CHECKSUM_MISMATCH


class FileCollisionError(BackupError):
    """Backup destination would overwrite an existing artifact unexpectedly."""

    code = ErrorCode.FILE_COLLISION


class UnsafePathError(BackupError):
    """Backup destination is not safe or writable."""

    code = ErrorCode.UNSAFE_PATH

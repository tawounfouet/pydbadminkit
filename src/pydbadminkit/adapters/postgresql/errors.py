"""Translate Psycopg errors into public PyDBAdminKit errors."""

import psycopg

from pydbadminkit.errors import (
    AuthenticationError,
    AuthorizationError,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
    DatabaseOperationError,
    PyDBAdminError,
)
from pydbadminkit.errors.context import ErrorContext

_AUTHENTICATION_SQLSTATES = {"28000", "28P01"}
_INSUFFICIENT_PRIVILEGE_SQLSTATE = "42501"


def translate_connection_error(
    error: psycopg.Error,
    *,
    context: ErrorContext,
) -> PyDBAdminError:
    """Translate one Psycopg connection error without leaking raw credentials."""

    if error.sqlstate in _AUTHENTICATION_SQLSTATES:
        return AuthenticationError(
            "Database authentication failed.",
            context=context,
            hint="Verify the configured username and secret reference.",
        )

    if "timeout" in str(error).casefold():
        return DatabaseConnectionTimeoutError(
            "Database connection timed out.",
            context=context,
        )

    return DatabaseConnectionError(
        "Unable to connect to the database.",
        context=context,
    )


def translate_database_error(
    error: psycopg.Error,
    *,
    context: ErrorContext,
) -> PyDBAdminError:
    """Translate an established-session database error into the public hierarchy."""

    if error.sqlstate == _INSUFFICIENT_PRIVILEGE_SQLSTATE:
        return AuthorizationError(
            "The current database principal is not authorized for this operation.",
            context=context,
        )

    return DatabaseOperationError(
        "The database operation failed.",
        context=context,
    )

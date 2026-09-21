"""Translate Psycopg connection errors into public PyDBAdminKit errors."""

import psycopg

from pydbadminkit.errors import (
    AuthenticationError,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
    PyDBAdminError,
)
from pydbadminkit.errors.context import ErrorContext

_AUTHENTICATION_SQLSTATES = {"28000", "28P01"}


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

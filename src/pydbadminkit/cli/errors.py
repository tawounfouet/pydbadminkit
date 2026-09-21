"""CLI error mapping."""

import typer

from pydbadminkit.errors import (
    AuthenticationError,
    CapabilityNotAvailableError,
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseConnectionTimeoutError,
    PyDBAdminError,
    ResourceNotFoundError,
)


def exit_code_for_error(error: PyDBAdminError) -> int:
    """Map public exceptions to stable initial CLI exit codes."""

    if isinstance(error, ConfigurationError):
        return 2
    if isinstance(error, DatabaseConnectionTimeoutError):
        return 9
    if isinstance(error, AuthenticationError):
        return 4
    if isinstance(error, DatabaseConnectionError):
        return 3
    if isinstance(error, ResourceNotFoundError):
        return 5
    if isinstance(error, CapabilityNotAvailableError):
        return 6
    return 1


def fail_with_error(error: PyDBAdminError) -> None:
    """Render a concise safe CLI error and exit."""

    typer.echo(f"Error: {error}", err=True)
    if error.hint:
        typer.echo(f"Hint: {error.hint}", err=True)
    raise typer.Exit(exit_code_for_error(error))

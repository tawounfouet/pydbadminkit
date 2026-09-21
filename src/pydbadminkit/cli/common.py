"""Shared CLI command helpers."""

import typer

from pydbadminkit.cli.context import CLIContext


def require_cli_context(ctx: typer.Context) -> CLIContext:
    """Return the initialized root CLI context or exit with a usage error."""

    root_context = ctx.find_root().obj
    if not isinstance(root_context, CLIContext):
        typer.echo("Error: CLI context was not initialized.", err=True)
        raise typer.Exit(2)
    return root_context


def require_connection_profile(ctx: typer.Context) -> tuple[CLIContext, str]:
    """Return CLI context and selected profile name."""

    root_context = require_cli_context(ctx)
    if root_context.connection_profile is None:
        typer.echo("Error: Select a profile with --connection.", err=True)
        raise typer.Exit(2)
    return root_context, root_context.connection_profile

"""Connection CLI commands."""

import typer

from pydbadminkit.bootstrap import build_connection_service
from pydbadminkit.cli.context import CLIContext
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.errors import PyDBAdminError

connection_app = typer.Typer(
    name="connection",
    no_args_is_help=True,
    help="Inspect and validate database connections.",
)


@connection_app.command("test")
def test_connection(ctx: typer.Context) -> None:
    """Test the selected connection profile."""

    root_context = ctx.find_root().obj
    if not isinstance(root_context, CLIContext):
        typer.echo("Error: CLI context was not initialized.", err=True)
        raise typer.Exit(2)
    if root_context.connection_profile is None:
        typer.echo("Error: Select a profile with --connection.", err=True)
        raise typer.Exit(2)

    service = build_connection_service(root_context.config_path)
    try:
        result = service.test(root_context.connection_profile)
    except PyDBAdminError as error:
        fail_with_error(error)

    typer.echo("Connection OK")
    typer.echo(f"Engine: {result.engine.value}")
    typer.echo(f"Version: {result.version}")
    typer.echo(f"Database: {result.current_database}")
    typer.echo(f"User: {result.current_user}")
    typer.echo(f"Latency: {result.latency_ms:.2f} ms")

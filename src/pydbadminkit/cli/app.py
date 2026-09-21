"""Root Typer application."""

from pathlib import Path
from typing import Annotated

import typer

from pydbadminkit.cli.commands.connection import connection_app
from pydbadminkit.cli.commands.database import database_app
from pydbadminkit.cli.commands.server import server_app
from pydbadminkit.cli.context import CLIContext
from pydbadminkit.version import __version__

app = typer.Typer(
    name="pydbadmin",
    no_args_is_help=True,
    help="CLI-first, Python-first database administration toolkit.",
)
app.add_typer(connection_app, name="connection")
app.add_typer(server_app, name="server")
app.add_typer(database_app, name="database")


def _version_callback(value: bool) -> bool:
    if value:
        typer.echo(f"pydbadminkit {__version__}")
        raise typer.Exit()
    return value


@app.callback()
def main(
    ctx: typer.Context,
    connection: Annotated[
        str | None,
        typer.Option(
            "--connection",
            "-c",
            help="Connection profile name.",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            help="Path to config.toml.",
        ),
    ] = None,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the installed PyDBAdminKit version and exit.",
        ),
    ] = False,
) -> None:
    """PyDBAdminKit command-line interface."""

    ctx.obj = CLIContext(
        connection_profile=connection,
        config_path=config,
    )

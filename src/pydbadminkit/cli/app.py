"""Root Typer application."""

from pathlib import Path
from typing import Annotated

import typer

from pydbadminkit.cli.commands.capability import capability_app
from pydbadminkit.cli.commands.connection import connection_app
from pydbadminkit.cli.commands.database import database_app
from pydbadminkit.cli.commands.index import index_app
from pydbadminkit.cli.commands.schema import schema_app
from pydbadminkit.cli.commands.server import server_app
from pydbadminkit.cli.commands.table import table_app
from pydbadminkit.cli.commands.view import view_app
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
app.add_typer(schema_app, name="schema")
app.add_typer(table_app, name="table")
app.add_typer(view_app, name="view")
app.add_typer(index_app, name="index")
app.add_typer(capability_app, name="capability")


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

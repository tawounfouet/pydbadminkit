"""Root Typer application."""

from pathlib import Path
from typing import Annotated

import typer

from pydbadminkit.cli.commands.access import access_app
from pydbadminkit.cli.commands.backup import backup_app
from pydbadminkit.cli.commands.blocking import blocking_app
from pydbadminkit.cli.commands.capability import capability_app
from pydbadminkit.cli.commands.connection import connection_app
from pydbadminkit.cli.commands.database import database_app
from pydbadminkit.cli.commands.effective_access import effective_access_app
from pydbadminkit.cli.commands.index import index_app
from pydbadminkit.cli.commands.lock import lock_app
from pydbadminkit.cli.commands.ownership import ownership_app
from pydbadminkit.cli.commands.postgres import postgres_app
from pydbadminkit.cli.commands.query import query_app
from pydbadminkit.cli.commands.role import role_app
from pydbadminkit.cli.commands.schema import schema_app
from pydbadminkit.cli.commands.server import server_app
from pydbadminkit.cli.commands.session import session_app
from pydbadminkit.cli.commands.table import table_app
from pydbadminkit.cli.commands.transaction import transaction_app
from pydbadminkit.cli.commands.view import view_app
from pydbadminkit.cli.commands.wait import wait_app
from pydbadminkit.cli.context import CLIContext
from pydbadminkit.output.format import OutputFormat
from pydbadminkit.version import __version__

app = typer.Typer(
    name="pydbadmin",
    no_args_is_help=True,
    help="CLI-first, Python-first database administration toolkit.",
)
app.add_typer(connection_app, name="connection")
app.add_typer(backup_app, name="backup")
app.add_typer(server_app, name="server")
app.add_typer(database_app, name="database")
app.add_typer(schema_app, name="schema")
app.add_typer(table_app, name="table")
app.add_typer(view_app, name="view")
app.add_typer(index_app, name="index")
app.add_typer(role_app, name="role")
app.add_typer(access_app, name="access")
app.add_typer(effective_access_app, name="effective-access")
app.add_typer(ownership_app, name="ownership")
app.add_typer(postgres_app, name="postgres")
app.add_typer(session_app, name="session")
app.add_typer(query_app, name="query")
app.add_typer(transaction_app, name="transaction")
app.add_typer(wait_app, name="wait")
app.add_typer(lock_app, name="lock")
app.add_typer(blocking_app, name="blocking")
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
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--output",
            "-o",
            help="Output format: table, json, or yaml.",
        ),
    ] = OutputFormat.TABLE,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Plan mutations without changing the database."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Approve simple/explicit confirmations."),
    ] = False,
    non_interactive: Annotated[
        bool,
        typer.Option("--non-interactive", help="Never prompt for confirmation."),
    ] = False,
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
        output_format=output,
        dry_run=dry_run,
        assume_yes=yes,
        non_interactive=non_interactive,
    )

"""Database catalog CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_database_info, render_database_list

database_app = typer.Typer(
    name="database",
    no_args_is_help=True,
    help="Inspect databases visible through the selected connection.",
)


@database_app.command("list")
def list_databases(ctx: typer.Context) -> None:
    """List visible non-template databases."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        databases = build_catalog_service(profile_name, root_context.config_path).list_databases()
    except PyDBAdminError as error:
        fail_with_error(error)

    typer.echo(render_database_list(databases))


@database_app.command("describe")
def describe_database(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Exact database name.")],
) -> None:
    """Describe one visible database."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        database = build_catalog_service(profile_name, root_context.config_path).get_database(name)
    except PyDBAdminError as error:
        fail_with_error(error)

    typer.echo(render_database_info(database))

"""Table catalog CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_table_description, render_table_list

table_app = typer.Typer(
    name="table",
    no_args_is_help=True,
    help="Inspect tables in the selected database.",
)


@table_app.command("list")
def list_tables(
    ctx: typer.Context,
    schema: Annotated[
        str | None,
        typer.Option("--schema", help="Restrict results to one schema."),
    ] = None,
    include_system: Annotated[
        bool,
        typer.Option("--include-system", help="Include PostgreSQL system schemas."),
    ] = False,
) -> None:
    """List visible tables."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        tables = build_catalog_service(
            profile_name,
            root_context.config_path,
        ).list_tables(
            schema=schema,
            include_system=include_system,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, tables, render_table_list(tables))


@table_app.command("describe")
def describe_table(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Table name, preferably schema.table.")],
) -> None:
    """Describe one table including columns and constraints."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        qualified_name = parse_qualified_name(name)
        description = build_catalog_service(
            profile_name,
            root_context.config_path,
        ).describe_table(qualified_name)
    except PyDBAdminError as error:
        fail_with_error(error)
    except ValueError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(2) from error

    emit_output(ctx, description, render_table_description(description))

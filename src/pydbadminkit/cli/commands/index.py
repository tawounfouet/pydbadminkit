"""Index catalog CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_index_description, render_index_list

index_app = typer.Typer(
    name="index",
    no_args_is_help=True,
    help="Inspect indexes in the selected database.",
)


@index_app.command("list")
def list_indexes(
    ctx: typer.Context,
    schema: Annotated[
        str | None,
        typer.Option("--schema", help="Restrict results to one schema."),
    ] = None,
    table: Annotated[
        str | None,
        typer.Option("--table", help="Restrict results to one table name."),
    ] = None,
    include_system: Annotated[
        bool,
        typer.Option("--include-system", help="Include PostgreSQL system schemas."),
    ] = False,
) -> None:
    """List visible indexes."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        indexes = build_catalog_service(
            profile_name,
            root_context.config_path,
        ).list_indexes(
            schema=schema,
            table=table,
            include_system=include_system,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, indexes, render_index_list(indexes))


@index_app.command("describe")
def describe_index(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Index name, preferably schema.index.")],
) -> None:
    """Describe one index."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        qualified_name = parse_qualified_name(name)
        description = build_catalog_service(
            profile_name,
            root_context.config_path,
        ).describe_index(qualified_name)
    except PyDBAdminError as error:
        fail_with_error(error)
    except ValueError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(2) from error

    emit_output(ctx, description, render_index_description(description))

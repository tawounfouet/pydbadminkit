"""View catalog CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_view_description, render_view_list

view_app = typer.Typer(
    name="view",
    no_args_is_help=True,
    help="Inspect views in the selected database.",
)


@view_app.command("list")
def list_views(
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
    """List visible views and materialized views."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        views = build_catalog_service(
            profile_name,
            root_context.config_path,
        ).list_views(
            schema=schema,
            include_system=include_system,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, views, render_view_list(views))


@view_app.command("describe")
def describe_view(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="View name, preferably schema.view.")],
) -> None:
    """Describe one view including columns and definition."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        qualified_name = parse_qualified_name(name)
        description = build_catalog_service(
            profile_name,
            root_context.config_path,
        ).describe_view(qualified_name)
    except PyDBAdminError as error:
        fail_with_error(error)
    except ValueError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(2) from error

    emit_output(ctx, description, render_view_description(description))

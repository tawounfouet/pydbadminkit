"""Schema catalog CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_catalog_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_schema_info, render_schema_list

schema_app = typer.Typer(
    name="schema",
    no_args_is_help=True,
    help="Inspect schemas in the selected database.",
)


@schema_app.command("list")
def list_schemas(
    ctx: typer.Context,
    include_system: Annotated[
        bool,
        typer.Option("--include-system", help="Include PostgreSQL system schemas."),
    ] = False,
) -> None:
    """List visible schemas."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        schemas = build_catalog_service(
            profile_name,
            root_context.config_path,
        ).list_schemas(include_system=include_system)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, schemas, render_schema_list(schemas))


@schema_app.command("describe")
def describe_schema(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Exact schema name.")],
) -> None:
    """Describe one visible schema."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        schema = build_catalog_service(profile_name, root_context.config_path).get_schema(name)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, schema, render_schema_info(schema))

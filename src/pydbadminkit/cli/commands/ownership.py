"""Ownership security CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_security_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.domain.common import DatabaseObjectType
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_ownership_list

ownership_app = typer.Typer(
    name="ownership",
    no_args_is_help=True,
    help="Inspect database objects owned by a role.",
)


@ownership_app.command("list")
def list_ownership(
    ctx: typer.Context,
    owner: Annotated[
        str,
        typer.Option("--owner", help="Owner role to inspect."),
    ],
    object_type: Annotated[
        DatabaseObjectType | None,
        typer.Option("--type", help="Restrict to one object type."),
    ] = None,
    schema: Annotated[
        str | None,
        typer.Option("--schema", help="Restrict relation ownership to one schema."),
    ] = None,
    include_system: Annotated[
        bool,
        typer.Option("--include-system", help="Include PostgreSQL system schemas."),
    ] = False,
) -> None:
    """List objects owned by one role."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        entries = build_security_service(
            profile_name,
            root_context.config_path,
        ).list_ownership(
            owner,
            object_type=object_type,
            schema=schema,
            include_system=include_system,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, entries, render_ownership_list(entries))

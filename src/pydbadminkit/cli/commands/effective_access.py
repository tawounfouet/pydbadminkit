"""Effective access security CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_security_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_effective_access_list

effective_access_app = typer.Typer(
    name="effective-access",
    no_args_is_help=True,
    help="Inspect effective relation access and its sources.",
)


@effective_access_app.command("list")
def list_effective_access(
    ctx: typer.Context,
    role: Annotated[
        str,
        typer.Option("--role", help="Role whose effective access is inspected."),
    ],
    schema: Annotated[
        str | None,
        typer.Option("--schema", help="Restrict results to one schema."),
    ] = None,
    object_name: Annotated[
        str | None,
        typer.Option("--object", help="Restrict results to one relation name."),
    ] = None,
    include_system: Annotated[
        bool,
        typer.Option("--include-system", help="Include PostgreSQL system schemas."),
    ] = False,
) -> None:
    """List effective access with direct/inherited/public/owner/superuser sources."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        entries = build_security_service(
            profile_name,
            root_context.config_path,
        ).list_effective_access(
            role,
            schema=schema,
            object_name=object_name,
            include_system=include_system,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, entries, render_effective_access_list(entries))

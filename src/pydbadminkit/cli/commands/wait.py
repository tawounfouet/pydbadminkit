"""Runtime wait CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_runtime_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_wait_list

wait_app = typer.Typer(
    name="wait",
    no_args_is_help=True,
    help="Inspect database backends currently reporting wait events.",
)


@wait_app.command("list")
def list_waits(
    ctx: typer.Context,
    database: Annotated[
        str | None,
        typer.Option("--database", help="Restrict results to one database."),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--user", help="Restrict results to one database user."),
    ] = None,
    wait_event_type: Annotated[
        str | None,
        typer.Option("--type", help="Restrict results to one PostgreSQL wait-event type."),
    ] = None,
    include_self: Annotated[
        bool,
        typer.Option("--include-self", help="Include PyDBAdminKit's inspection backend."),
    ] = False,
) -> None:
    """List backends currently reporting wait events."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        waits = build_runtime_service(
            profile_name,
            root_context.config_path,
        ).list_waits(
            database=database,
            username=username,
            wait_event_type=wait_event_type,
            include_self=include_self,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, waits, render_wait_list(waits))

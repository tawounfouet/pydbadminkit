"""Runtime lock CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_runtime_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_lock_list

lock_app = typer.Typer(
    name="lock",
    no_args_is_help=True,
    help="Inspect database backend locks.",
)


@lock_app.command("list")
def list_locks(
    ctx: typer.Context,
    database: Annotated[
        str | None,
        typer.Option("--database", help="Restrict results to one database."),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--user", help="Restrict results to one database user."),
    ] = None,
    waiting_only: Annotated[
        bool,
        typer.Option("--waiting-only", help="Show only locks that have not been granted."),
    ] = False,
    include_self: Annotated[
        bool,
        typer.Option("--include-self", help="Include PyDBAdminKit's inspection backend."),
    ] = False,
) -> None:
    """List backend locks."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        locks = build_runtime_service(
            profile_name,
            root_context.config_path,
        ).list_locks(
            database=database,
            username=username,
            granted=False if waiting_only else None,
            include_self=include_self,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, locks, render_lock_list(locks))

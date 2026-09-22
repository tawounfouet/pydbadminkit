"""Runtime blocking-chain CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_runtime_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_blocking_list

blocking_app = typer.Typer(
    name="blocking",
    no_args_is_help=True,
    help="Inspect recursive database blocking chains.",
)


@blocking_app.command("list")
def list_blocking(
    ctx: typer.Context,
    database: Annotated[
        str | None,
        typer.Option("--database", help="Restrict root waiters to one database."),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--user", help="Restrict root waiters to one database user."),
    ] = None,
    include_self: Annotated[
        bool,
        typer.Option("--include-self", help="Include PyDBAdminKit's inspection backend."),
    ] = False,
) -> None:
    """List recursive blocking-chain edges."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        relations = build_runtime_service(
            profile_name,
            root_context.config_path,
        ).list_blocking(
            database=database,
            username=username,
            include_self=include_self,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, relations, render_blocking_list(relations))

"""Runtime transaction CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_runtime_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_transaction_list

transaction_app = typer.Typer(
    name="transaction",
    no_args_is_help=True,
    help="Inspect open database transactions.",
)


@transaction_app.command("list")
def list_transactions(
    ctx: typer.Context,
    database: Annotated[
        str | None,
        typer.Option("--database", help="Restrict results to one database."),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--user", help="Restrict results to one database user."),
    ] = None,
    include_self: Annotated[
        bool,
        typer.Option("--include-self", help="Include PyDBAdminKit's inspection transaction."),
    ] = False,
) -> None:
    """List open transactions."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        transactions = build_runtime_service(
            profile_name,
            root_context.config_path,
        ).list_transactions(
            database=database,
            username=username,
            include_self=include_self,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, transactions, render_transaction_list(transactions))

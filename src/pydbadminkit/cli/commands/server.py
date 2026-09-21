"""Server CLI commands."""

import typer

from pydbadminkit.bootstrap import build_server_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_server_info

server_app = typer.Typer(
    name="server",
    no_args_is_help=True,
    help="Inspect the selected database server.",
)


@server_app.command("info")
def server_info(ctx: typer.Context) -> None:
    """Show information about the connected server."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        info = build_server_service(profile_name, root_context.config_path).get_info()
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, info, render_server_info(info))

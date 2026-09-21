"""Connection CLI commands."""

import typer

from pydbadminkit.bootstrap import build_connection_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_connection_test

connection_app = typer.Typer(
    name="connection",
    no_args_is_help=True,
    help="Inspect and validate database connections.",
)


@connection_app.command("test")
def test_connection(ctx: typer.Context) -> None:
    """Test the selected connection profile."""

    root_context, profile_name = require_connection_profile(ctx)
    service = build_connection_service(root_context.config_path)
    try:
        result = service.test(profile_name)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, result, render_connection_test(result))

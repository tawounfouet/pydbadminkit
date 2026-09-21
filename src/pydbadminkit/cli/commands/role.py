"""Role security CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_security_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_role_description, render_role_list

role_app = typer.Typer(
    name="role",
    no_args_is_help=True,
    help="Inspect database roles and memberships.",
)


@role_app.command("list")
def list_roles(
    ctx: typer.Context,
    include_system: Annotated[
        bool,
        typer.Option("--include-system", help="Include PostgreSQL built-in roles."),
    ] = False,
    login_only: Annotated[
        bool,
        typer.Option("--login-only", help="Show roles that can log in."),
    ] = False,
) -> None:
    """List visible roles."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        roles = build_security_service(
            profile_name,
            root_context.config_path,
        ).list_roles(
            include_system=include_system,
            login_only=login_only,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, roles, render_role_list(roles))


@role_app.command("describe")
def describe_role(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Exact role name.")],
) -> None:
    """Describe one role including membership relationships."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        description = build_security_service(
            profile_name,
            root_context.config_path,
        ).describe_role(name)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, description, render_role_description(description))

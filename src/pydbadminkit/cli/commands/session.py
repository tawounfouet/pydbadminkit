"""Runtime session CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_runtime_mutation_service, build_runtime_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.mutations import emit_mutation_outcome
from pydbadminkit.cli.output import emit_output
from pydbadminkit.cli.safety import mutation_options
from pydbadminkit.domain.runtime import SessionState, TerminateSessionCommand
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_session_list

session_app = typer.Typer(
    name="session",
    no_args_is_help=True,
    help="Inspect live database sessions.",
)


@session_app.command("list")
def list_sessions(
    ctx: typer.Context,
    database: Annotated[
        str | None,
        typer.Option("--database", help="Restrict results to one database."),
    ] = None,
    username: Annotated[
        str | None,
        typer.Option("--user", help="Restrict results to one database user."),
    ] = None,
    state: Annotated[
        SessionState | None,
        typer.Option("--state", help="Restrict results to one normalized session state."),
    ] = None,
    include_self: Annotated[
        bool,
        typer.Option("--include-self", help="Include PyDBAdminKit's inspection session."),
    ] = False,
) -> None:
    """List visible database sessions."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        sessions = build_runtime_service(
            profile_name,
            root_context.config_path,
        ).list_sessions(
            database=database,
            username=username,
            state=state,
            include_self=include_self,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, sessions, render_session_list(sessions))


@session_app.command("terminate")
def terminate_session(
    ctx: typer.Context,
    pid: Annotated[int, typer.Argument(help="Client backend PID to terminate.")],
    confirm_target: Annotated[
        str | None,
        typer.Option("--confirm-target", help="Exact target proof for critical operations."),
    ] = None,
) -> None:
    """Terminate one client backend session."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = TerminateSessionCommand(pid=pid)
        service = build_runtime_mutation_service(
            profile_name,
            root_context.config_path,
        )
        plan = service.plan_terminate_session(command)
        options = mutation_options(
            ctx,
            plan,
            confirmed_target=confirm_target,
        )
        outcome = service.terminate_session(
            command,
            options,
            plan=plan,
        )
    except PyDBAdminError as error:
        fail_with_error(error)
    except ValueError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(2) from error

    emit_mutation_outcome(ctx, outcome)

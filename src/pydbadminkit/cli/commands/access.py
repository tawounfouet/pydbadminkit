"""Direct access security CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_security_mutation_service, build_security_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.mutations import emit_mutation_outcome
from pydbadminkit.cli.output import emit_output
from pydbadminkit.cli.safety import mutation_options
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.domain.security import AccessType, RelationAccessCommand
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_access_list

access_app = typer.Typer(
    name="access",
    no_args_is_help=True,
    help="Inspect and administer explicit relation access.",
)


def _usage_error(error: ValueError) -> None:
    typer.echo(f"Error: {error}", err=True)
    raise typer.Exit(2) from error


@access_app.command("list")
def list_access(
    ctx: typer.Context,
    role: Annotated[
        str,
        typer.Option("--role", help="Role whose explicit relation access is inspected."),
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
    """List explicit relation access entries for one role."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        entries = build_security_service(
            profile_name,
            root_context.config_path,
        ).list_direct_access(
            role,
            schema=schema,
            object_name=object_name,
            include_system=include_system,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, entries, render_access_list(entries))


@access_app.command("grant")
def grant_access(
    ctx: typer.Context,
    role: Annotated[str, typer.Option("--role", help="Role receiving access.")],
    object_name: Annotated[
        str,
        typer.Option("--object", help="Relation name, preferably schema.object."),
    ],
    access_type: Annotated[
        AccessType,
        typer.Option("--access", help="Access type to grant."),
    ],
    grant_option: Annotated[
        bool,
        typer.Option("--grant-option", help="Grant WITH GRANT OPTION."),
    ] = False,
    confirm_target: Annotated[
        str | None,
        typer.Option("--confirm-target", help="Exact target proof for critical operations."),
    ] = None,
) -> None:
    """Grant one relation access type through the guarded mutation pipeline."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = RelationAccessCommand(
            principal=role,
            access_type=access_type,
            object=parse_qualified_name(object_name),
            grant_option=grant_option,
        )
        service = build_security_mutation_service(profile_name, root_context.config_path)
        plan = service.plan_grant_access(command)
        options = mutation_options(ctx, plan, confirmed_target=confirm_target)
        outcome = service.grant_access(command, options, plan=plan)
    except ValueError as error:
        _usage_error(error)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_mutation_outcome(ctx, outcome)


@access_app.command("revoke")
def revoke_access(
    ctx: typer.Context,
    role: Annotated[str, typer.Option("--role", help="Role losing access.")],
    object_name: Annotated[
        str,
        typer.Option("--object", help="Relation name, preferably schema.object."),
    ],
    access_type: Annotated[
        AccessType,
        typer.Option("--access", help="Access type to revoke."),
    ],
    confirm_target: Annotated[
        str | None,
        typer.Option("--confirm-target", help="Exact target proof for critical operations."),
    ] = None,
) -> None:
    """Revoke one relation access type through the guarded mutation pipeline."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = RelationAccessCommand(
            principal=role,
            access_type=access_type,
            object=parse_qualified_name(object_name),
        )
        service = build_security_mutation_service(profile_name, root_context.config_path)
        plan = service.plan_revoke_access(command)
        options = mutation_options(ctx, plan, confirmed_target=confirm_target)
        outcome = service.revoke_access(command, options, plan=plan)
    except ValueError as error:
        _usage_error(error)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_mutation_outcome(ctx, outcome)

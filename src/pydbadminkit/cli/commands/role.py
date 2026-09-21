"""Role security CLI commands."""

from enum import StrEnum
from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_security_mutation_service, build_security_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.mutations import emit_mutation_outcome
from pydbadminkit.cli.output import emit_output
from pydbadminkit.cli.safety import mutation_options
from pydbadminkit.domain.security import (
    AlterRoleCommand,
    CreateRoleCommand,
    MembershipCommand,
)
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_role_description, render_role_list

role_app = typer.Typer(
    name="role",
    no_args_is_help=True,
    help="Inspect and administer database roles and memberships.",
)


class Toggle(StrEnum):
    """Explicit tri-state CLI toggle value."""

    ENABLE = "enable"
    DISABLE = "disable"


def _toggle_value(value: Toggle | None) -> bool | None:
    if value is None:
        return None
    return value is Toggle.ENABLE


def _usage_error(error: ValueError) -> None:
    typer.echo(f"Error: {error}", err=True)
    raise typer.Exit(2) from error


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


@role_app.command("create")
def create_role(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Role name to create.")],
    login: Annotated[bool, typer.Option("--login", help="Allow LOGIN.")] = False,
    superuser: Annotated[
        bool,
        typer.Option("--superuser", help="Grant SUPERUSER."),
    ] = False,
    createdb: Annotated[bool, typer.Option("--createdb", help="Grant CREATEDB.")] = False,
    createrole: Annotated[
        bool,
        typer.Option("--createrole", help="Grant CREATEROLE."),
    ] = False,
    replication: Annotated[
        bool,
        typer.Option("--replication", help="Grant REPLICATION."),
    ] = False,
    inherit: Annotated[
        bool,
        typer.Option("--inherit/--no-inherit", help="Control role inheritance."),
    ] = True,
    bypass_rls: Annotated[
        bool,
        typer.Option("--bypass-rls", help="Grant BYPASSRLS."),
    ] = False,
    connection_limit: Annotated[
        int,
        typer.Option("--connection-limit", help="-1 means no connection limit."),
    ] = -1,
    confirm_target: Annotated[
        str | None,
        typer.Option("--confirm-target", help="Exact target proof for critical operations."),
    ] = None,
) -> None:
    """Create a role through the guarded mutation pipeline."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = CreateRoleCommand(
            name=name,
            can_login=login,
            is_superuser=superuser,
            can_create_db=createdb,
            can_create_role=createrole,
            can_replicate=replication,
            inherit=inherit,
            bypass_rls=bypass_rls,
            connection_limit=connection_limit,
        )
        service = build_security_mutation_service(profile_name, root_context.config_path)
        plan = service.plan_create_role(command)
        options = mutation_options(ctx, plan, confirmed_target=confirm_target)
        outcome = service.create_role(command, options, plan=plan)
    except ValueError as error:
        _usage_error(error)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_mutation_outcome(ctx, outcome)


@role_app.command("alter")
def alter_role(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Role name to alter.")],
    login: Annotated[
        Toggle | None,
        typer.Option("--login", help="enable or disable LOGIN."),
    ] = None,
    superuser: Annotated[
        Toggle | None,
        typer.Option("--superuser", help="enable or disable SUPERUSER."),
    ] = None,
    createdb: Annotated[
        Toggle | None,
        typer.Option("--createdb", help="enable or disable CREATEDB."),
    ] = None,
    createrole: Annotated[
        Toggle | None,
        typer.Option("--createrole", help="enable or disable CREATEROLE."),
    ] = None,
    replication: Annotated[
        Toggle | None,
        typer.Option("--replication", help="enable or disable REPLICATION."),
    ] = None,
    inherit: Annotated[
        Toggle | None,
        typer.Option("--inherit", help="enable or disable INHERIT."),
    ] = None,
    bypass_rls: Annotated[
        Toggle | None,
        typer.Option("--bypass-rls", help="enable or disable BYPASSRLS."),
    ] = None,
    connection_limit: Annotated[
        int | None,
        typer.Option("--connection-limit", help="Set connection limit; -1 means unlimited."),
    ] = None,
    confirm_target: Annotated[
        str | None,
        typer.Option("--confirm-target", help="Exact target proof for critical operations."),
    ] = None,
) -> None:
    """Alter selected role attributes through the guarded mutation pipeline."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = AlterRoleCommand(
            name=name,
            can_login=_toggle_value(login),
            is_superuser=_toggle_value(superuser),
            can_create_db=_toggle_value(createdb),
            can_create_role=_toggle_value(createrole),
            can_replicate=_toggle_value(replication),
            inherit=_toggle_value(inherit),
            bypass_rls=_toggle_value(bypass_rls),
            connection_limit=connection_limit,
        )
        service = build_security_mutation_service(profile_name, root_context.config_path)
        plan = service.plan_alter_role(command)
        options = mutation_options(ctx, plan, confirmed_target=confirm_target)
        outcome = service.alter_role(command, options, plan=plan)
    except ValueError as error:
        _usage_error(error)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_mutation_outcome(ctx, outcome)


@role_app.command("drop")
def drop_role(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Role name to drop.")],
    confirm_target: Annotated[
        str | None,
        typer.Option("--confirm-target", help="Exact target proof for critical operations."),
    ] = None,
) -> None:
    """Drop a role through the guarded mutation pipeline."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        service = build_security_mutation_service(profile_name, root_context.config_path)
        plan = service.plan_drop_role(name)
        options = mutation_options(ctx, plan, confirmed_target=confirm_target)
        outcome = service.drop_role(name, options, plan=plan)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_mutation_outcome(ctx, outcome)


@role_app.command("membership-add")
def add_membership(
    ctx: typer.Context,
    role: Annotated[str, typer.Argument(help="Role being granted.")],
    member: Annotated[str, typer.Argument(help="Member receiving the role.")],
    admin_option: Annotated[
        bool,
        typer.Option("--admin-option", help="Grant membership WITH ADMIN OPTION."),
    ] = False,
    confirm_target: Annotated[
        str | None,
        typer.Option("--confirm-target", help="Exact target proof for critical operations."),
    ] = None,
) -> None:
    """Add one role membership."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = MembershipCommand(role=role, member=member, admin_option=admin_option)
        service = build_security_mutation_service(profile_name, root_context.config_path)
        plan = service.plan_add_membership(command)
        options = mutation_options(ctx, plan, confirmed_target=confirm_target)
        outcome = service.add_membership(command, options, plan=plan)
    except ValueError as error:
        _usage_error(error)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_mutation_outcome(ctx, outcome)


@role_app.command("membership-remove")
def remove_membership(
    ctx: typer.Context,
    role: Annotated[str, typer.Argument(help="Role being removed.")],
    member: Annotated[str, typer.Argument(help="Member losing the role.")],
    confirm_target: Annotated[
        str | None,
        typer.Option("--confirm-target", help="Exact target proof for critical operations."),
    ] = None,
) -> None:
    """Remove one role membership."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = MembershipCommand(role=role, member=member)
        service = build_security_mutation_service(profile_name, root_context.config_path)
        plan = service.plan_remove_membership(command)
        options = mutation_options(ctx, plan, confirmed_target=confirm_target)
        outcome = service.remove_membership(command, options, plan=plan)
    except ValueError as error:
        _usage_error(error)
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_mutation_outcome(ctx, outcome)

"""PostgreSQL-specific maintenance CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.bootstrap import build_maintenance_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.mutations import emit_mutation_outcome
from pydbadminkit.cli.output import emit_output
from pydbadminkit.cli.safety import mutation_options
from pydbadminkit.domain.common import parse_qualified_name
from pydbadminkit.domain.operations import (
    AnalyzeCommand,
    ReindexCommand,
    ReindexTargetType,
    VacuumCommand,
)
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_maintenance_progress

postgres_app = typer.Typer(
    name="postgres",
    no_args_is_help=True,
    help="PostgreSQL-specific administration commands.",
)

progress_app = typer.Typer(
    name="progress",
    no_args_is_help=True,
    help="Inspect PostgreSQL maintenance progress.",
)
postgres_app.add_typer(progress_app, name="progress")


@postgres_app.command("vacuum")
def vacuum(
    ctx: typer.Context,
    table: Annotated[
        str | None,
        typer.Option("--table", help="Optional schema.table target; omit for the database."),
    ] = None,
    full: Annotated[
        bool,
        typer.Option("--full", help="Run VACUUM FULL."),
    ] = False,
    freeze: Annotated[
        bool,
        typer.Option("--freeze", help="Enable PostgreSQL FREEZE processing."),
    ] = False,
    analyze_after: Annotated[
        bool,
        typer.Option("--analyze", help="Run ANALYZE as part of VACUUM."),
    ] = False,
    statement_timeout: Annotated[
        float | None,
        typer.Option("--statement-timeout", help="Statement timeout in seconds."),
    ] = None,
    lock_timeout: Annotated[
        float | None,
        typer.Option("--lock-timeout", help="Lock acquisition timeout in seconds."),
    ] = None,
    confirm_target: Annotated[
        str | None,
        typer.Option(
            "--confirm-target",
            help="Exact target confirmation for critical non-interactive maintenance.",
        ),
    ] = None,
) -> None:
    """Run guarded PostgreSQL VACUUM maintenance."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = VacuumCommand(
            table=parse_qualified_name(table) if table is not None else None,
            full=full,
            freeze=freeze,
            analyze=analyze_after,
            statement_timeout_seconds=statement_timeout,
            lock_timeout_seconds=lock_timeout,
        )
        service = build_maintenance_service(
            profile_name,
            root_context.config_path,
        )
        plan = service.plan_vacuum(command)
        options = mutation_options(
            ctx,
            plan,
            confirmed_target=confirm_target,
        )
        outcome = service.vacuum(
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


@postgres_app.command("analyze")
def analyze(
    ctx: typer.Context,
    table: Annotated[
        str | None,
        typer.Option("--table", help="Optional schema.table target; omit for the database."),
    ] = None,
    column: Annotated[
        list[str] | None,
        typer.Option("--column", help="Column to analyze; repeat for multiple columns."),
    ] = None,
    statement_timeout: Annotated[
        float | None,
        typer.Option("--statement-timeout", help="Statement timeout in seconds."),
    ] = None,
    lock_timeout: Annotated[
        float | None,
        typer.Option("--lock-timeout", help="Lock acquisition timeout in seconds."),
    ] = None,
    confirm_target: Annotated[
        str | None,
        typer.Option(
            "--confirm-target",
            help="Exact target confirmation for critical non-interactive maintenance.",
        ),
    ] = None,
) -> None:
    """Run guarded PostgreSQL ANALYZE maintenance."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        command = AnalyzeCommand(
            table=parse_qualified_name(table) if table is not None else None,
            columns=tuple(column or ()),
            statement_timeout_seconds=statement_timeout,
            lock_timeout_seconds=lock_timeout,
        )
        service = build_maintenance_service(
            profile_name,
            root_context.config_path,
        )
        plan = service.plan_analyze(command)
        options = mutation_options(
            ctx,
            plan,
            confirmed_target=confirm_target,
        )
        outcome = service.analyze(
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


@postgres_app.command("reindex")
def reindex(
    ctx: typer.Context,
    index: Annotated[
        str | None,
        typer.Option("--index", help="Schema.index target."),
    ] = None,
    table: Annotated[
        str | None,
        typer.Option("--table", help="Schema.table target."),
    ] = None,
    concurrently: Annotated[
        bool,
        typer.Option("--concurrently", help="Use PostgreSQL REINDEX CONCURRENTLY."),
    ] = False,
    statement_timeout: Annotated[
        float | None,
        typer.Option("--statement-timeout", help="Statement timeout in seconds."),
    ] = None,
    lock_timeout: Annotated[
        float | None,
        typer.Option("--lock-timeout", help="Lock acquisition timeout in seconds."),
    ] = None,
    confirm_target: Annotated[
        str | None,
        typer.Option(
            "--confirm-target",
            help="Exact target confirmation for critical non-interactive maintenance.",
        ),
    ] = None,
) -> None:
    """Run guarded PostgreSQL REINDEX maintenance."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        if (index is None) == (table is None):
            raise ValueError("Choose exactly one of --index or --table.")

        raw_target = index if index is not None else table
        if raw_target is None:
            raise ValueError("REINDEX target is required.")

        command = ReindexCommand(
            target_type=(ReindexTargetType.INDEX if index is not None else ReindexTargetType.TABLE),
            target=parse_qualified_name(raw_target),
            concurrently=concurrently,
            statement_timeout_seconds=statement_timeout,
            lock_timeout_seconds=lock_timeout,
        )
        service = build_maintenance_service(
            profile_name,
            root_context.config_path,
        )
        plan = service.plan_reindex(command)
        options = mutation_options(
            ctx,
            plan,
            confirmed_target=confirm_target,
        )
        outcome = service.reindex(
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


@progress_app.command("vacuum")
def vacuum_progress(ctx: typer.Context) -> None:
    """List currently visible PostgreSQL VACUUM progress."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        entries = build_maintenance_service(
            profile_name,
            root_context.config_path,
        ).list_vacuum_progress()
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, entries, render_maintenance_progress(entries))


@progress_app.command("reindex")
def reindex_progress(ctx: typer.Context) -> None:
    """List currently visible PostgreSQL REINDEX progress."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        entries = build_maintenance_service(
            profile_name,
            root_context.config_path,
        ).list_reindex_progress()
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, entries, render_maintenance_progress(entries))

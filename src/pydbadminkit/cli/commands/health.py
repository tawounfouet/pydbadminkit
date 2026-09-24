"""Database health CLI commands."""

from typing import Annotated

import typer

from pydbadminkit.application.monitoring import HealthCheckConfig
from pydbadminkit.bootstrap import build_health_service
from pydbadminkit.cli.common import require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.output import emit_output
from pydbadminkit.domain.monitoring import HealthStatus, Threshold
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_health_report

health_app = typer.Typer(
    name="health",
    no_args_is_help=True,
    help="Evaluate point-in-time database health.",
)


@health_app.command("check")
def check_health(
    ctx: typer.Context,
    fail_on_warning: Annotated[
        bool,
        typer.Option(
            "--fail-on-warning",
            help="Exit non-zero when the report contains a warning.",
        ),
    ] = False,
    connection_warning_ratio: Annotated[
        float,
        typer.Option("--connection-warning-ratio"),
    ] = 0.80,
    connection_critical_ratio: Annotated[
        float,
        typer.Option("--connection-critical-ratio"),
    ] = 0.95,
    query_warning_seconds: Annotated[
        float,
        typer.Option("--query-warning-seconds"),
    ] = 30.0,
    query_critical_seconds: Annotated[
        float,
        typer.Option("--query-critical-seconds"),
    ] = 300.0,
    transaction_warning_seconds: Annotated[
        float,
        typer.Option("--transaction-warning-seconds"),
    ] = 60.0,
    transaction_critical_seconds: Annotated[
        float,
        typer.Option("--transaction-critical-seconds"),
    ] = 600.0,
    idle_transaction_warning_seconds: Annotated[
        float,
        typer.Option("--idle-transaction-warning-seconds"),
    ] = 60.0,
    idle_transaction_critical_seconds: Annotated[
        float,
        typer.Option("--idle-transaction-critical-seconds"),
    ] = 300.0,
    lock_warning_count: Annotated[
        int,
        typer.Option("--lock-warning-count"),
    ] = 1,
    lock_critical_count: Annotated[
        int,
        typer.Option("--lock-critical-count"),
    ] = 10,
) -> None:
    """Run the default point-in-time health suite."""

    root_context, profile_name = require_connection_profile(ctx)
    try:
        config = HealthCheckConfig(
            connection_usage=Threshold(connection_warning_ratio, connection_critical_ratio),
            long_queries_seconds=Threshold(query_warning_seconds, query_critical_seconds),
            long_transactions_seconds=Threshold(
                transaction_warning_seconds,
                transaction_critical_seconds,
            ),
            idle_transactions_seconds=Threshold(
                idle_transaction_warning_seconds,
                idle_transaction_critical_seconds,
            ),
            waiting_locks=Threshold(lock_warning_count, lock_critical_count),
        )
        report = build_health_service(
            profile_name,
            root_context.config_path,
            config=config,
        ).check()
    except PyDBAdminError as error:
        fail_with_error(error)
    except (TypeError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(2) from error

    emit_output(ctx, report, render_health_report(report))

    if report.overall_status is HealthStatus.CRITICAL:
        raise typer.Exit(1)
    if fail_on_warning and report.overall_status is HealthStatus.WARNING:
        raise typer.Exit(1)

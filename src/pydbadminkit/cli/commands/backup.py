"""Logical backup CLI commands."""

from pathlib import Path
from typing import Annotated

import typer

from pydbadminkit.bootstrap import (
    build_backup_service,
    build_backup_validation_service,
)
from pydbadminkit.cli.common import require_cli_context, require_connection_profile
from pydbadminkit.cli.errors import fail_with_error
from pydbadminkit.cli.mutations import emit_mutation_outcome
from pydbadminkit.cli.output import emit_output
from pydbadminkit.cli.safety import mutation_options
from pydbadminkit.domain.operations import BackupFormat, CreateBackupCommand
from pydbadminkit.domain.safety import OperationPlan
from pydbadminkit.errors import PyDBAdminError
from pydbadminkit.output.human import render_backup, render_backup_validation

backup_app = typer.Typer(
    name="backup",
    no_args_is_help=True,
    help="Create and validate logical database backups.",
)


@backup_app.command("create")
def create_backup(
    ctx: typer.Context,
    database: Annotated[str, typer.Argument(help="Database to back up.")],
    backup_format: Annotated[
        BackupFormat,
        typer.Option("--format", help="Backup format."),
    ] = BackupFormat.CUSTOM,
    output_path: Annotated[
        Path | None,
        typer.Option("--output-path", help="Destination backup artifact path."),
    ] = None,
    compress: Annotated[
        bool,
        typer.Option("--compress", help="Enable explicit custom-format compression."),
    ] = False,
    checksum: Annotated[
        bool,
        typer.Option("--checksum/--no-checksum", help="Compute SHA-256 metadata."),
    ] = True,
    jobs: Annotated[
        int | None,
        typer.Option("--jobs", help="Parallel backup jobs when supported."),
    ] = None,
    timeout: Annotated[
        float | None,
        typer.Option("--timeout", help="Native tool timeout in seconds."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Explicitly replace an existing backup artifact."),
    ] = False,
) -> None:
    """Create one logical backup using PostgreSQL native tooling."""

    root_context, profile_name = require_connection_profile(ctx)
    destination = output_path or _default_output_path(database, backup_format)

    try:
        command = CreateBackupCommand(
            database=database,
            format=backup_format,
            output_path=str(destination),
            compress=True if compress else None,
            checksum=checksum,
            jobs=jobs,
            timeout_seconds=timeout,
            force=force,
        )
        service = build_backup_service(
            profile_name,
            root_context.config_path,
        )
        plan = service.plan_create_backup(command)
        options = mutation_options(ctx, plan)
        outcome = service.create_backup(
            command,
            options,
            plan=plan,
        )
    except PyDBAdminError as error:
        fail_with_error(error)
    except ValueError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(2) from error

    if isinstance(outcome, OperationPlan):
        emit_mutation_outcome(ctx, outcome)
        return

    emit_output(ctx, outcome, render_backup(outcome))


@backup_app.command("validate")
def validate_backup(
    ctx: typer.Context,
    path: Annotated[Path, typer.Argument(help="Backup artifact to validate.")],
    timeout: Annotated[
        float | None,
        typer.Option("--timeout", help="Native validation timeout in seconds."),
    ] = None,
) -> None:
    """Validate a backup artifact and its sidecar metadata."""

    require_cli_context(ctx)
    try:
        validation = build_backup_validation_service().validate_backup(
            str(path),
            timeout_seconds=timeout,
        )
    except PyDBAdminError as error:
        fail_with_error(error)

    emit_output(ctx, validation, render_backup_validation(validation))


def _default_output_path(database: str, backup_format: BackupFormat) -> Path:
    suffix = ".dump" if backup_format is BackupFormat.CUSTOM else ".sql"
    if backup_format not in {BackupFormat.CUSTOM, BackupFormat.PLAIN_SQL}:
        suffix = ".backup"
    return Path(f"{database}{suffix}")

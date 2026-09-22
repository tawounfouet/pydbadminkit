"""PostgreSQL logical restore adapter using native tools."""

from datetime import UTC, datetime
from time import perf_counter

from pydbadminkit.adapters.postgresql.backup import (
    parse_postgresql_tool_version,
    postgres_child_env,
)
from pydbadminkit.domain.common import DatabaseEngine, DatabaseVersion, OperationStatus
from pydbadminkit.domain.connection import ResolvedConnectionConfig
from pydbadminkit.domain.operations import (
    Backup,
    BackupFormat,
    ExternalTool,
    RestoreBackupCommand,
    RestoreOperation,
    RestoreValidation,
)
from pydbadminkit.errors import (
    CapabilityNotAvailableError,
    RestoreError,
    RestoreValidationError,
    ToolNotFoundError,
    ToolVersionMismatchError,
)
from pydbadminkit.ports.process import ProcessRunnerPort
from pydbadminkit.ports.restore_database import RestoreDatabasePort
from pydbadminkit.ports.server import ServerPort
from pydbadminkit.ports.tools import ToolResolverPort


class PostgreSQLRestoreAdapter:
    """Validate, execute and verify PostgreSQL logical restores."""

    def __init__(
        self,
        *,
        runner: ProcessRunnerPort,
        tool_resolver: ToolResolverPort,
        target_port: RestoreDatabasePort,
        server_port: ServerPort,
        config: ResolvedConnectionConfig,
    ) -> None:
        self._runner = runner
        self._tool_resolver = tool_resolver
        self._target_port = target_port
        self._server_port = server_port
        self._config = config

    def validate_restore(
        self,
        command: RestoreBackupCommand,
        backup: Backup,
    ) -> RestoreValidation:
        warnings: list[str] = []
        errors: list[str] = []

        if backup.engine is not DatabaseEngine.POSTGRESQL:
            errors.append(
                "Backup engine "
                f"'{backup.engine.value}' is not supported by the PostgreSQL restore adapter."
            )

        if backup.format not in {BackupFormat.CUSTOM, BackupFormat.PLAIN_SQL}:
            errors.append(
                f"Backup format '{backup.format.value}' is not implemented for restore in 0.5.0a2."
            )

        target_exists = self._target_port.target_exists(command.target_database)
        if target_exists:
            if command.create:
                errors.append(
                    "Restore target already exists; --create requires an absent target database."
                )
            elif not command.clean:
                errors.append(
                    "Restore target already exists; implicit overwrite is blocked. "
                    "Use --clean for a custom archive or choose a new target."
                )
        else:
            if not command.create:
                errors.append(
                    "Restore target does not exist; use --create to create it explicitly."
                )
            if command.clean:
                errors.append("--clean requires an existing restore target.")

        if command.clean and backup.format is not BackupFormat.CUSTOM:
            errors.append("--clean is supported only for custom-format backups.")

        if command.jobs is not None and backup.format is not BackupFormat.CUSTOM:
            errors.append("Parallel restore jobs are supported only for custom-format backups.")

        server_version = self._server_port.get_info().version
        if backup.engine_version is not None and backup.engine_version.major > server_version.major:
            errors.append(
                "Backup was created from PostgreSQL major "
                f"{backup.engine_version.major}, newer than target server major "
                f"{server_version.major}."
            )

        if not errors:
            tool = self._required_tool(_tool_name_for(backup.format))
            tool_version = parse_postgresql_tool_version(tool)
            self._check_restore_tool_compatibility(
                tool=tool,
                tool_version=tool_version,
                server_version=server_version,
            )

        if command.clean:
            warnings.append("Restore --clean drops archive-owned objects before recreating them.")
        if command.create:
            warnings.append("A new target database will be created before restore execution.")

        return RestoreValidation(
            valid=not errors,
            backup_format=backup.format,
            target_exists=target_exists,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    def restore_backup(
        self,
        command: RestoreBackupCommand,
        backup: Backup,
    ) -> RestoreOperation:
        validation = self.validate_restore(command, backup)
        if not validation.valid:
            raise RestoreValidationError("; ".join(validation.errors))

        tool = self._required_tool(_tool_name_for(backup.format))
        tool_version = parse_postgresql_tool_version(tool)

        if command.create:
            self._target_port.create_target(command.target_database)

        args = self._build_restore_args(
            command,
            backup,
            tool=tool,
        )
        started_at = datetime.now(UTC)
        started = perf_counter()
        result = self._runner.run(
            args,
            env=postgres_child_env(self._config),
            timeout_seconds=command.timeout_seconds,
        )
        duration_ms = int((perf_counter() - started) * 1000)

        if result.return_code != 0:
            raise RestoreError(
                f"{tool.name} exited with code {result.return_code}: "
                f"{_safe_stderr_excerpt(result.stderr)}"
            )

        verification_passed = self._target_port.verify_target(command.target_database)
        if not verification_passed:
            raise RestoreValidationError(
                f"Restore completed but verification failed for target '{command.target_database}'."
            )

        return RestoreOperation(
            backup=backup,
            target_database=command.target_database,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=OperationStatus.SUCCEEDED,
            duration_ms=duration_ms,
            verification_passed=True,
            tool=tool.name,
            tool_version=str(tool_version),
        )

    def _required_tool(self, name: str) -> ExternalTool:
        tool = self._tool_resolver.resolve(name)
        if not tool.available or tool.path is None:
            raise ToolNotFoundError(f"Required tool '{name}' was not found.")
        if tool.version is None:
            raise ToolVersionMismatchError(
                f"Required tool '{name}' did not report a parseable version."
            )
        return tool

    @staticmethod
    def _check_restore_tool_compatibility(
        *,
        tool: ExternalTool,
        tool_version: DatabaseVersion,
        server_version: DatabaseVersion,
    ) -> None:
        if tool_version.major < server_version.major:
            raise ToolVersionMismatchError(
                f"{tool.name} major version {tool_version.major} cannot restore to "
                f"PostgreSQL server major {server_version.major}."
            )

    def _build_restore_args(
        self,
        command: RestoreBackupCommand,
        backup: Backup,
        *,
        tool: ExternalTool,
    ) -> list[str]:
        if tool.path is None:
            raise ToolNotFoundError(f"Required tool '{tool.name}' was not found.")

        common = [
            "--host",
            self._config.host,
            "--port",
            str(self._config.port),
            "--username",
            self._config.username,
            "--dbname",
            command.target_database,
            "--no-password",
        ]

        if backup.format is BackupFormat.CUSTOM:
            args = [
                tool.path,
                *common,
                "--exit-on-error",
            ]
            if command.clean:
                args.extend(("--clean", "--if-exists"))
            if command.jobs is not None:
                args.extend(("--jobs", str(command.jobs)))
            args.append(backup.path)
            return args

        if backup.format is BackupFormat.PLAIN_SQL:
            return [
                tool.path,
                *common,
                "--no-psqlrc",
                "--set",
                "ON_ERROR_STOP=1",
                "--file",
                backup.path,
            ]

        raise CapabilityNotAvailableError(
            f"Backup format '{backup.format.value}' is not implemented for restore."
        )


def _tool_name_for(backup_format: BackupFormat) -> str:
    if backup_format is BackupFormat.CUSTOM:
        return "pg_restore"
    if backup_format is BackupFormat.PLAIN_SQL:
        return "psql"
    raise CapabilityNotAvailableError(
        f"Backup format '{backup_format.value}' is not implemented for restore."
    )


def _safe_stderr_excerpt(value: str, limit: int = 500) -> str:
    single_line = " ".join(value.split())
    if not single_line:
        return "<no stderr>"
    if len(single_line) <= limit:
        return single_line
    return single_line[: limit - 1] + "…"

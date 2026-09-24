"""PostgreSQL logical backup adapter using native tools."""

import re
from datetime import UTC, datetime
from uuid import uuid4

from pydbadminkit.domain.common import DatabaseVersion, OperationStatus
from pydbadminkit.domain.connection import ResolvedConnectionConfig, SecretValue
from pydbadminkit.domain.operations import (
    Backup,
    BackupFormat,
    BackupMetadata,
    BackupToolResult,
    BackupValidation,
    CreateBackupCommand,
    ExternalTool,
)
from pydbadminkit.errors import (
    CapabilityNotAvailableError,
    InternalError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolVersionMismatchError,
)
from pydbadminkit.infrastructure.redaction import redact_secret
from pydbadminkit.ports.backup_files import BackupFileStorePort
from pydbadminkit.ports.process import ProcessRunnerPort
from pydbadminkit.ports.server import ServerPort
from pydbadminkit.ports.tools import ToolResolverPort

_TOOL_VERSION_PATTERN = re.compile(
    r"PostgreSQL\)\s+(?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<patch>\d+))?"
)


class PostgreSQLBackupAdapter:
    """Create and validate PostgreSQL logical backups with native utilities."""

    def __init__(
        self,
        *,
        runner: ProcessRunnerPort,
        tool_resolver: ToolResolverPort,
        file_store: BackupFileStorePort,
        config: ResolvedConnectionConfig | None = None,
        server_port: ServerPort | None = None,
    ) -> None:
        self._runner = runner
        self._tool_resolver = tool_resolver
        self._file_store = file_store
        self._config = config
        self._server_port = server_port

    def create_backup(self, command: CreateBackupCommand) -> Backup:
        config = self._require_config()
        server_port = self._require_server_port()
        self._validate_create_options(command)

        paths = self._file_store.prepare(
            command.output_path,
            force=command.force,
        )
        try:
            tool = self._required_tool("pg_dump")
            tool_version = parse_postgresql_tool_version(tool)
            server_version = server_port.get_info().version
            self._check_pg_dump_compatibility(
                tool_version=tool_version,
                server_version=server_version,
            )

            args = self._build_pg_dump_args(
                command,
                executable=tool.path,
                temporary_path=paths.temporary_path,
                config=config,
                tool_version=tool_version,
                server_version=server_version,
            )
            process = self._runner.run(
                args,
                env=postgres_child_env(config),
                timeout_seconds=command.timeout_seconds,
            )
            tool_result = BackupToolResult(tool=tool, process=process)
            _raise_for_process_failure(tool_result, config.password)

            self._file_store.secure_artifact(paths.temporary_path)
            artifact = self._file_store.inspect(paths.temporary_path)
            if (
                not artifact.exists
                or not artifact.readable
                or artifact.size_bytes is None
                or artifact.size_bytes <= 0
            ):
                raise ToolExecutionError(
                    "pg_dump completed without producing a readable non-empty artifact."
                )

            checksum = self._file_store.sha256(paths.temporary_path) if command.checksum else None
            created_at = datetime.now(UTC)
            backup_id = _backup_id(command.database, created_at)
            metadata = BackupMetadata(
                backup_id=backup_id,
                database=command.database,
                format=command.format,
                created_at=created_at,
                engine=config.engine,
                engine_version=server_version,
                tool_version=str(tool_version),
                size_bytes=artifact.size_bytes,
                checksum_algorithm="sha256" if checksum is not None else None,
                checksum=checksum,
            )

            self._file_store.finalize(
                paths,
                metadata,
                force=command.force,
            )
        except Exception:
            self._file_store.cleanup_temporary(paths)
            raise

        return Backup(
            id=metadata.backup_id,
            database=metadata.database,
            format=metadata.format,
            path=paths.final_path,
            created_at=metadata.created_at,
            size_bytes=metadata.size_bytes,
            checksum=metadata.checksum,
            engine=metadata.engine,
            engine_version=metadata.engine_version,
            tool_version=metadata.tool_version,
            status=OperationStatus.SUCCEEDED,
        )

    def validate_backup(
        self,
        backup: Backup,
        *,
        timeout_seconds: float | None = None,
    ) -> BackupValidation:
        warnings: list[str] = []
        errors: list[str] = []
        level = "artifact"

        artifact = self._file_store.inspect(backup.path)
        if not artifact.exists:
            errors.append("Backup artifact does not exist.")
        elif not artifact.readable:
            errors.append("Backup artifact is not readable.")
        elif artifact.size_bytes is None or artifact.size_bytes <= 0:
            errors.append("Backup artifact is empty.")

        if (
            not errors
            and backup.size_bytes is not None
            and artifact.size_bytes != backup.size_bytes
        ):
            errors.append("Backup artifact size does not match its metadata sidecar.")

        if not errors and backup.checksum is not None:
            current_checksum = self._file_store.sha256(backup.path)
            if current_checksum != backup.checksum:
                errors.append("Backup SHA-256 checksum does not match metadata.")

        if not errors and backup.format is BackupFormat.CUSTOM:
            level = "logical"
            tool = self._required_tool("pg_restore")
            result = self._runner.run(
                [tool.path or "pg_restore", "--list", "--", backup.path],
                timeout_seconds=timeout_seconds,
            )
            if result.return_code != 0:
                secret = self._config.password if self._config is not None else None
                errors.append(
                    "pg_restore could not list the custom backup archive: "
                    f"{_safe_stderr_excerpt(result.stderr, secret)}"
                )
        elif not errors and backup.format is BackupFormat.PLAIN_SQL:
            warnings.append(
                "Plain SQL validation is limited to artifact and checksum checks; "
                "full logical validity requires a restore test."
            )
        elif not errors:
            errors.append(
                f"Backup format '{backup.format.value}' is not supported by 0.5.0a1 validation."
            )

        return BackupValidation(
            valid=not errors,
            level=level,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    @staticmethod
    def _validate_create_options(command: CreateBackupCommand) -> None:
        if command.format not in {BackupFormat.CUSTOM, BackupFormat.PLAIN_SQL}:
            raise CapabilityNotAvailableError(
                f"Backup format '{command.format.value}' is not implemented in 0.5.0a1."
            )
        if command.jobs is not None:
            raise CapabilityNotAvailableError(
                "Parallel backup jobs require directory format and are not implemented in 0.5.0a1."
            )
        if command.format is BackupFormat.PLAIN_SQL and command.compress is not None:
            raise CapabilityNotAvailableError(
                "Explicit plain-SQL compression is deferred until restore compression handling."
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
    def _check_pg_dump_compatibility(
        *,
        tool_version: DatabaseVersion,
        server_version: DatabaseVersion,
    ) -> None:
        if tool_version.major < server_version.major:
            raise ToolVersionMismatchError(
                "pg_dump major version "
                f"{tool_version.major} cannot dump PostgreSQL server major "
                f"{server_version.major}."
            )

    @staticmethod
    def _build_pg_dump_args(
        command: CreateBackupCommand,
        *,
        executable: str | None,
        temporary_path: str,
        config: ResolvedConnectionConfig,
        tool_version: DatabaseVersion,
        server_version: DatabaseVersion,
    ) -> list[str]:
        if executable is None:
            raise ToolNotFoundError("Required tool 'pg_dump' was not found.")

        format_value = {
            BackupFormat.CUSTOM: "custom",
            BackupFormat.PLAIN_SQL: "plain",
        }[command.format]

        args = [
            executable,
            f"--format={format_value}",
            "--file",
            temporary_path,
            "--host",
            config.host,
            "--port",
            str(config.port),
            "--username",
            config.username,
            "--no-password",
            "--dbname",
            command.database,
        ]

        if tool_version.major != server_version.major:
            args.append("--quote-all-identifiers")

        if command.format is BackupFormat.CUSTOM and command.compress is not None:
            args.append("--compress=6" if command.compress else "--compress=0")

        return args

    def _require_config(self) -> ResolvedConnectionConfig:
        if self._config is None:
            raise InternalError("Backup creation requires a resolved connection config.")
        return self._config

    def _require_server_port(self) -> ServerPort:
        if self._server_port is None:
            raise InternalError("Backup creation requires a server inspection port.")
        return self._server_port


def parse_postgresql_tool_version(tool: ExternalTool) -> DatabaseVersion:
    """Parse PostgreSQL native-tool version output."""

    if tool.version is None:
        raise ToolVersionMismatchError(f"Required tool '{tool.name}' did not report a version.")
    match = _TOOL_VERSION_PATTERN.search(tool.version)
    if match is None:
        raise ToolVersionMismatchError(
            f"Could not parse {tool.name} version from '{tool.version}'."
        )

    return DatabaseVersion(
        major=int(match.group("major")),
        minor=int(match.group("minor") or 0),
        patch=int(match.group("patch") or 0),
    )


def postgres_child_env(config: ResolvedConnectionConfig) -> dict[str, str]:
    env = {
        "PGSSLMODE": config.ssl.mode.value,
        "PGCONNECT_TIMEOUT": str(config.timeouts.connect_seconds),
    }
    if config.password is not None:
        env["PGPASSWORD"] = config.password.reveal()
    if config.ssl.root_cert is not None:
        env["PGSSLROOTCERT"] = config.ssl.root_cert
    if config.ssl.cert is not None:
        env["PGSSLCERT"] = config.ssl.cert
    if config.ssl.key is not None:
        env["PGSSLKEY"] = config.ssl.key
    return env


def _raise_for_process_failure(
    result: BackupToolResult,
    secret: SecretValue | None,
) -> None:
    if result.process.return_code == 0:
        return
    raise ToolExecutionError(
        f"{result.tool.name} exited with code {result.process.return_code}: "
        f"{_safe_stderr_excerpt(result.process.stderr, secret)}"
    )


def _safe_stderr_excerpt(
    value: str,
    secret: SecretValue | None,
    limit: int = 500,
) -> str:
    single_line = " ".join(redact_secret(value, secret).split())
    if not single_line:
        return "<no stderr>"
    if len(single_line) <= limit:
        return single_line
    return single_line[: limit - 1] + "…"


def _backup_id(database: str, created_at: datetime) -> str:
    safe_database = re.sub(r"[^A-Za-z0-9_.-]+", "_", database).strip("_")
    timestamp = created_at.strftime("%Y%m%d_%H%M%S")
    return f"backup_{timestamp}_{safe_database}_{uuid4().hex[:8]}"

"""Unit tests for PostgreSQL logical backup adapter."""

from collections.abc import Mapping
from pathlib import Path

import pytest

from pydbadminkit.adapters.postgresql.backup import (
    PostgreSQLBackupAdapter,
    parse_postgresql_tool_version,
)
from pydbadminkit.domain.catalog import ServerInfo
from pydbadminkit.domain.common import (
    DatabaseEngine,
    DatabaseVersion,
)
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SecretValue,
    SSLConfig,
    TimeoutConfig,
)
from pydbadminkit.domain.operations import (
    BackupFormat,
    CreateBackupCommand,
    ExternalTool,
    ProcessResult,
)
from pydbadminkit.errors import (
    CapabilityNotAvailableError,
    ToolExecutionError,
    ToolVersionMismatchError,
)
from pydbadminkit.infrastructure.backup_files import LocalBackupFileStore

pytestmark = [pytest.mark.unit, pytest.mark.postgresql, pytest.mark.backup]


class FakeServerPort:
    def __init__(self, version: DatabaseVersion | None = None) -> None:
        self.version = version or DatabaseVersion(18)

    def get_info(self) -> ServerInfo:
        return ServerInfo(
            engine=DatabaseEngine.POSTGRESQL,
            version=self.version,
            current_database="postgres",
            current_user="postgres",
        )


class FakeToolResolver:
    def __init__(self, versions: dict[str, str]) -> None:
        self.versions = versions

    def resolve(self, name: str) -> ExternalTool:
        version = self.versions.get(name)
        if version is None:
            return ExternalTool(name=name, path=None, version=None, available=False)
        return ExternalTool(
            name=name,
            path=f"/usr/bin/{name}",
            version=version,
            available=True,
        )


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Mapping[str, str] | None, float | None]] = []
        self.return_code = 0
        self.stderr = ""

    def run(
        self,
        args: list[str],
        env: Mapping[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        self.calls.append((args, env, timeout_seconds))
        if Path(args[0]).name == "pg_dump":
            file_index = args.index("--file") + 1
            Path(args[file_index]).write_bytes(b"postgres-backup")
        return ProcessResult(
            return_code=self.return_code,
            stdout="",
            stderr=self.stderr,
            duration_ms=5,
        )


def _config(password: str = "super-secret") -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("local"),
        engine=DatabaseEngine.POSTGRESQL,
        host="127.0.0.1",
        port=5432,
        database="postgres",
        username="postgres",
        password=SecretValue(password),
        environment="testing",  # type: ignore[arg-type]
        read_only=False,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(connect_seconds=5),
    )


def _adapter(
    tmp_path: Path,
    *,
    runner: FakeRunner | None = None,
    dump_version: str = "pg_dump (PostgreSQL) 18.1",
    restore_version: str = "pg_restore (PostgreSQL) 18.1",
    server_version: DatabaseVersion | None = None,
) -> tuple[PostgreSQLBackupAdapter, FakeRunner]:
    effective_runner = runner or FakeRunner()
    effective_server_version = server_version or DatabaseVersion(18)
    return (
        PostgreSQLBackupAdapter(
            runner=effective_runner,
            tool_resolver=FakeToolResolver(
                {
                    "pg_dump": dump_version,
                    "pg_restore": restore_version,
                }
            ),
            file_store=LocalBackupFileStore(),
            config=_config(),
            server_port=FakeServerPort(effective_server_version),
        ),
        effective_runner,
    )


def test_parse_postgresql_tool_version() -> None:
    tool = ExternalTool(
        name="pg_dump",
        path="/usr/bin/pg_dump",
        version="pg_dump (PostgreSQL) 18.1 (Ubuntu 18.1-1)",
        available=True,
    )

    assert parse_postgresql_tool_version(tool) == DatabaseVersion(18, 1)


def test_create_custom_backup_keeps_password_out_of_argv(tmp_path: Path) -> None:
    adapter, runner = _adapter(tmp_path)
    target = tmp_path / "accounting.dump"
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path=str(target),
        checksum=True,
    )

    backup = adapter.create_backup(command)

    args, env, timeout = runner.calls[0]
    assert backup.path == str(target)
    assert backup.size_bytes == len(b"postgres-backup")
    assert backup.checksum is not None
    assert "--format=custom" in args
    assert "super-secret" not in args
    assert env is not None
    assert env["PGPASSWORD"] == "super-secret"
    assert timeout is None
    assert Path(f"{target}.metadata.json").exists()


def test_create_cross_version_backup_quotes_identifiers(tmp_path: Path) -> None:
    adapter, runner = _adapter(
        tmp_path,
        dump_version="pg_dump (PostgreSQL) 19devel",
        server_version=DatabaseVersion(18),
    )
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path=str(tmp_path / "accounting.dump"),
    )

    adapter.create_backup(command)

    assert "--quote-all-identifiers" in runner.calls[0][0]


def test_create_backup_rejects_older_pg_dump(tmp_path: Path) -> None:
    adapter, _runner = _adapter(
        tmp_path,
        dump_version="pg_dump (PostgreSQL) 17.9",
        server_version=DatabaseVersion(18),
    )

    with pytest.raises(ToolVersionMismatchError):
        adapter.create_backup(
            CreateBackupCommand(
                database="accounting",
                format=BackupFormat.CUSTOM,
                output_path=str(tmp_path / "accounting.dump"),
            )
        )


def test_create_backup_rejects_deferred_options(tmp_path: Path) -> None:
    adapter, _runner = _adapter(tmp_path)

    with pytest.raises(CapabilityNotAvailableError):
        adapter.create_backup(
            CreateBackupCommand(
                database="accounting",
                format=BackupFormat.DIRECTORY,
                output_path=str(tmp_path / "accounting"),
            )
        )

    with pytest.raises(CapabilityNotAvailableError):
        adapter.create_backup(
            CreateBackupCommand(
                database="accounting",
                format=BackupFormat.PLAIN_SQL,
                output_path=str(tmp_path / "accounting.sql"),
                compress=True,
            )
        )


def test_create_backup_cleans_partial_on_pg_dump_failure(tmp_path: Path) -> None:
    runner = FakeRunner()
    runner.return_code = 1
    runner.stderr = "pg_dump: connection failed"
    adapter, _runner = _adapter(tmp_path, runner=runner)
    target = tmp_path / "accounting.dump"

    with pytest.raises(ToolExecutionError):
        adapter.create_backup(
            CreateBackupCommand(
                database="accounting",
                format=BackupFormat.CUSTOM,
                output_path=str(target),
            )
        )

    assert not Path(f"{target}.partial").exists()
    assert not target.exists()


def test_validate_custom_and_plain_backups(tmp_path: Path) -> None:
    adapter, _runner = _adapter(tmp_path)

    custom = adapter.create_backup(
        CreateBackupCommand(
            database="accounting",
            format=BackupFormat.CUSTOM,
            output_path=str(tmp_path / "accounting.dump"),
        )
    )
    custom_validation = adapter.validate_backup(custom)

    plain = adapter.create_backup(
        CreateBackupCommand(
            database="accounting",
            format=BackupFormat.PLAIN_SQL,
            output_path=str(tmp_path / "accounting.sql"),
        )
    )
    plain_validation = adapter.validate_backup(plain)

    assert custom_validation.valid is True
    assert custom_validation.level == "logical"
    assert plain_validation.valid is True
    assert plain_validation.level == "artifact"
    assert plain_validation.warnings

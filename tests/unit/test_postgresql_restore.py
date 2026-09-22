"""Unit tests for PostgreSQL restore adapter."""

from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from pydbadminkit.adapters.postgresql.restore import PostgreSQLRestoreAdapter
from pydbadminkit.domain.catalog import ServerInfo
from pydbadminkit.domain.common import (
    DatabaseEngine,
    DatabaseVersion,
    EnvironmentName,
    OperationStatus,
)
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    ResolvedConnectionConfig,
    SecretValue,
    SSLConfig,
    TimeoutConfig,
)
from pydbadminkit.domain.operations import (
    Backup,
    BackupFormat,
    ExternalTool,
    ProcessResult,
    RestoreBackupCommand,
)
from pydbadminkit.errors import (
    RestoreError,
    RestoreValidationError,
    ToolVersionMismatchError,
)

pytestmark = [pytest.mark.unit, pytest.mark.postgresql, pytest.mark.restore]


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
        return ProcessResult(self.return_code, "", self.stderr, 5)


class FakeToolResolver:
    def __init__(self, major: int = 18) -> None:
        self.major = major

    def resolve(self, name: str) -> ExternalTool:
        return ExternalTool(
            name=name,
            path=f"/usr/bin/{name}",
            version=f"{name} (PostgreSQL) {self.major}.1",
            available=True,
        )


class FakeServerPort:
    def __init__(self, major: int = 18) -> None:
        self.major = major

    def get_info(self) -> ServerInfo:
        return ServerInfo(
            engine=DatabaseEngine.POSTGRESQL,
            version=DatabaseVersion(self.major),
            current_database="postgres",
            current_user="postgres",
        )


class FakeTargetPort:
    def __init__(self, *, exists: bool, verification: bool = True) -> None:
        self.exists = exists
        self.verification = verification
        self.created: list[str] = []

    def target_exists(self, name: str) -> bool:
        del name
        return self.exists

    def create_target(self, name: str) -> None:
        self.created.append(name)
        self.exists = True

    def verify_target(self, name: str) -> bool:
        del name
        return self.verification


def _config() -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("local"),
        engine=DatabaseEngine.POSTGRESQL,
        host="127.0.0.1",
        port=5432,
        database="postgres",
        username="postgres",
        password=SecretValue("super-secret"),
        environment=EnvironmentName.TESTING,
        read_only=False,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(connect_seconds=5),
    )


def _backup(
    backup_format: BackupFormat = BackupFormat.CUSTOM,
    *,
    major: int = 18,
) -> Backup:
    suffix = "dump" if backup_format is BackupFormat.CUSTOM else "sql"
    return Backup(
        id="backup_test",
        database="source",
        format=backup_format,
        path=f"/tmp/source.{suffix}",
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
        size_bytes=42,
        checksum="abc",
        engine=DatabaseEngine.POSTGRESQL,
        engine_version=DatabaseVersion(major),
        tool_version=str(major),
        status=OperationStatus.SUCCEEDED,
    )


def _adapter(
    *,
    exists: bool,
    runner: FakeRunner | None = None,
    tool_major: int = 18,
    server_major: int = 18,
    verification: bool = True,
) -> tuple[PostgreSQLRestoreAdapter, FakeRunner, FakeTargetPort]:
    effective_runner = runner or FakeRunner()
    target = FakeTargetPort(exists=exists, verification=verification)
    return (
        PostgreSQLRestoreAdapter(
            runner=effective_runner,
            tool_resolver=FakeToolResolver(tool_major),
            target_port=target,
            server_port=FakeServerPort(server_major),
            config=_config(),
        ),
        effective_runner,
        target,
    )


def test_new_custom_target_requires_create() -> None:
    adapter, _runner, _target = _adapter(exists=False)

    blocked = adapter.validate_restore(
        RestoreBackupCommand("/tmp/source.dump", "target"),
        _backup(),
    )
    allowed = adapter.validate_restore(
        RestoreBackupCommand("/tmp/source.dump", "target", create=True),
        _backup(),
    )

    assert blocked.valid is False
    assert allowed.valid is True
    assert allowed.target_exists is False


def test_existing_target_requires_explicit_clean() -> None:
    adapter, _runner, _target = _adapter(exists=True)

    blocked = adapter.validate_restore(
        RestoreBackupCommand("/tmp/source.dump", "target"),
        _backup(),
    )
    allowed = adapter.validate_restore(
        RestoreBackupCommand("/tmp/source.dump", "target", clean=True),
        _backup(),
    )

    assert blocked.valid is False
    assert allowed.valid is True
    assert any("drops" in warning for warning in allowed.warnings)


def test_plain_restore_rejects_clean_and_parallel_jobs() -> None:
    adapter, _runner, _target = _adapter(exists=True)

    validation = adapter.validate_restore(
        RestoreBackupCommand(
            "/tmp/source.sql",
            "target",
            clean=True,
            jobs=2,
        ),
        _backup(BackupFormat.PLAIN_SQL),
    )

    assert validation.valid is False
    assert len(validation.errors) >= 2


def test_restore_rejects_newer_backup_and_older_tool() -> None:
    adapter, _runner, _target = _adapter(exists=False, server_major=18)

    validation = adapter.validate_restore(
        RestoreBackupCommand("/tmp/source.dump", "target", create=True),
        _backup(major=19),
    )
    assert validation.valid is False

    older_tool, _runner, _target = _adapter(
        exists=False,
        tool_major=17,
        server_major=18,
    )
    with pytest.raises(ToolVersionMismatchError):
        older_tool.validate_restore(
            RestoreBackupCommand("/tmp/source.dump", "target", create=True),
            _backup(),
        )


def test_custom_restore_creates_target_and_keeps_secret_out_of_argv() -> None:
    adapter, runner, target = _adapter(exists=False)

    operation = adapter.restore_backup(
        RestoreBackupCommand(
            "/tmp/source.dump",
            "target",
            create=True,
            jobs=2,
        ),
        _backup(),
    )

    args, env, _timeout = runner.calls[-1]
    assert target.created == ["target"]
    assert operation.status is OperationStatus.SUCCEEDED
    assert "--jobs" in args
    assert "super-secret" not in args
    assert env is not None
    assert env["PGPASSWORD"] == "super-secret"


def test_plain_restore_uses_psql_on_new_target() -> None:
    adapter, runner, target = _adapter(exists=False)

    operation = adapter.restore_backup(
        RestoreBackupCommand("/tmp/source.sql", "plain_target", create=True),
        _backup(BackupFormat.PLAIN_SQL),
    )

    args = runner.calls[-1][0]
    assert target.created == ["plain_target"]
    assert operation.tool == "psql"
    assert "--no-psqlrc" in args
    assert "ON_ERROR_STOP=1" in args


def test_restore_maps_process_and_verification_failures() -> None:
    runner = FakeRunner()
    runner.return_code = 1
    runner.stderr = "restore failed"
    adapter, _runner, _target = _adapter(exists=False, runner=runner)

    with pytest.raises(RestoreError):
        adapter.restore_backup(
            RestoreBackupCommand("/tmp/source.dump", "target", create=True),
            _backup(),
        )

    failed_verify, _runner, _target = _adapter(
        exists=False,
        verification=False,
    )
    with pytest.raises(RestoreValidationError):
        failed_verify.restore_backup(
            RestoreBackupCommand("/tmp/source.dump", "target", create=True),
            _backup(),
        )

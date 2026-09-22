"""Edge-case coverage for Backup Foundation safety paths."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from pydbadminkit.adapters.postgresql.backup import (
    PostgreSQLBackupAdapter,
    parse_postgresql_tool_version,
)
from pydbadminkit.application.operations import BackupService
from pydbadminkit.domain.audit import AuditEvent, AuditEventType
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
    SSLConfig,
    TimeoutConfig,
)
from pydbadminkit.domain.operations import (
    Backup,
    BackupArtifactInfo,
    BackupFormat,
    BackupMetadata,
    BackupValidation,
    CreateBackupCommand,
    ExternalTool,
)
from pydbadminkit.domain.safety import MutationOptions
from pydbadminkit.errors import (
    BackupValidationError,
    FileCollisionError,
    InternalError,
    ResourceNotFoundError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolVersionMismatchError,
    UnsafePathError,
)
from pydbadminkit.infrastructure.backup_files import LocalBackupFileStore

pytestmark = [pytest.mark.unit, pytest.mark.backup]


def _metadata() -> BackupMetadata:
    return BackupMetadata(
        backup_id="backup_edge",
        database="accounting",
        format=BackupFormat.CUSTOM,
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
        engine=DatabaseEngine.POSTGRESQL,
        engine_version=DatabaseVersion(18),
        tool_version="18",
        size_bytes=4,
        checksum_algorithm="sha256",
        checksum="expected",
    )


def _backup(path: Path, *, checksum: str | None = None, size_bytes: int | None = 4) -> Backup:
    return Backup(
        id="backup_edge",
        database="accounting",
        format=BackupFormat.CUSTOM,
        path=str(path),
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
        size_bytes=size_bytes,
        checksum=checksum,
        engine=DatabaseEngine.POSTGRESQL,
        engine_version=DatabaseVersion(18),
        tool_version="18",
        status=OperationStatus.SUCCEEDED,
    )


def _config() -> ResolvedConnectionConfig:
    return ResolvedConnectionConfig(
        name=ConnectionProfileName("local"),
        engine=DatabaseEngine.POSTGRESQL,
        host="127.0.0.1",
        port=5432,
        database="postgres",
        username="postgres",
        password=None,
        environment=EnvironmentName.TESTING,
        read_only=False,
        ssl=SSLConfig(),
        timeouts=TimeoutConfig(),
    )


class MissingToolResolver:
    def resolve(self, name: str) -> ExternalTool:
        return ExternalTool(name=name, path=None, version=None, available=False)


class FixedToolResolver:
    def __init__(self, version: str | None) -> None:
        self.version = version

    def resolve(self, name: str) -> ExternalTool:
        return ExternalTool(
            name=name,
            path=f"/usr/bin/{name}",
            version=self.version,
            available=True,
        )


class NoopRunner:
    def run(
        self,
        args: list[str],
        env: object = None,
        timeout_seconds: float | None = None,
    ) -> object:
        del args, env, timeout_seconds
        raise AssertionError("runner should not be called")


class FakeServer:
    def get_info(self) -> ServerInfo:
        return ServerInfo(
            engine=DatabaseEngine.POSTGRESQL,
            version=DatabaseVersion(18),
        )


class ValidationStore:
    def __init__(
        self,
        info: BackupArtifactInfo,
        checksum: str = "actual",
    ) -> None:
        self.info = info
        self.checksum = checksum

    def inspect(self, path: str) -> BackupArtifactInfo:
        del path
        return self.info

    def sha256(self, path: str) -> str:
        del path
        return self.checksum


class FailingBackupPort:
    def create_backup(self, command: CreateBackupCommand) -> Backup:
        del command
        raise ToolExecutionError("pg_dump failed safely")

    def validate_backup(
        self,
        backup: Backup,
        *,
        timeout_seconds: float | None = None,
    ) -> BackupValidation:
        del backup, timeout_seconds
        return BackupValidation(True, "artifact", (), ())


class AuditCollector:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)


def test_file_store_rejects_missing_parent_and_directory_target(tmp_path: Path) -> None:
    store = LocalBackupFileStore()

    with pytest.raises(UnsafePathError):
        store.prepare(str(tmp_path / "missing" / "db.dump"), force=False)

    directory_target = tmp_path / "backup-dir"
    directory_target.mkdir()
    with pytest.raises(UnsafePathError):
        store.prepare(str(directory_target), force=False)


def test_file_store_rejects_sidecar_and_partial_collisions(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    target = tmp_path / "db.dump"
    sidecar = Path(f"{target}.metadata.json")
    sidecar.write_text("{}", encoding="utf-8")

    with pytest.raises(FileCollisionError):
        store.prepare(str(target), force=False)

    sidecar.unlink()
    partial = Path(f"{target}.partial")
    partial.write_bytes(b"partial")
    with pytest.raises(FileCollisionError):
        store.prepare(str(target), force=True)

    partial.unlink()
    metadata_partial = Path(f"{sidecar}.partial")
    metadata_partial.write_text("{}", encoding="utf-8")
    with pytest.raises(FileCollisionError):
        store.prepare(str(target), force=True)


def test_file_store_inspect_checksum_and_load_missing_paths(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    missing = tmp_path / "missing.dump"

    info = store.inspect(str(missing))
    assert info.exists is False
    assert info.readable is False
    assert info.size_bytes is None

    with pytest.raises(BackupValidationError):
        store.sha256(str(missing))

    with pytest.raises(ResourceNotFoundError):
        store.load_backup(str(missing))


def test_file_store_rejects_missing_and_invalid_sidecar(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    target = tmp_path / "db.dump"
    target.write_bytes(b"data")

    with pytest.raises(BackupValidationError):
        store.load_backup(str(target))

    sidecar = Path(f"{target}.metadata.json")
    sidecar.write_text("not-json", encoding="utf-8")
    with pytest.raises(BackupValidationError):
        store.load_backup(str(target))


def test_adapter_requires_context_and_resolved_tools(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path=str(tmp_path / "db.dump"),
    )

    without_context = PostgreSQLBackupAdapter(
        runner=NoopRunner(),  # type: ignore[arg-type]
        tool_resolver=MissingToolResolver(),
        file_store=store,
    )
    with pytest.raises(InternalError):
        without_context.create_backup(command)

    missing_tool = PostgreSQLBackupAdapter(
        runner=NoopRunner(),  # type: ignore[arg-type]
        tool_resolver=MissingToolResolver(),
        file_store=store,
        config=_config(),
        server_port=FakeServer(),
    )
    with pytest.raises(ToolNotFoundError):
        missing_tool.create_backup(command)


def test_adapter_rejects_missing_and_unparseable_tool_versions(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path=str(tmp_path / "db.dump"),
    )

    missing_version = PostgreSQLBackupAdapter(
        runner=NoopRunner(),  # type: ignore[arg-type]
        tool_resolver=FixedToolResolver(None),
        file_store=store,
        config=_config(),
        server_port=FakeServer(),
    )
    with pytest.raises(ToolVersionMismatchError):
        missing_version.create_backup(command)

    tool = ExternalTool(
        name="pg_dump",
        path="/usr/bin/pg_dump",
        version="unexpected version text",
        available=True,
    )
    with pytest.raises(ToolVersionMismatchError):
        parse_postgresql_tool_version(tool)


def test_validate_backup_detects_artifact_and_checksum_errors(tmp_path: Path) -> None:
    missing_adapter = PostgreSQLBackupAdapter(
        runner=NoopRunner(),  # type: ignore[arg-type]
        tool_resolver=MissingToolResolver(),
        file_store=ValidationStore(
            BackupArtifactInfo(False, False, None)
        ),  # type: ignore[arg-type]
    )
    missing = missing_adapter.validate_backup(_backup(tmp_path / "db.dump"))
    assert missing.valid is False
    assert missing.errors == ("Backup artifact does not exist.",)

    size_adapter = PostgreSQLBackupAdapter(
        runner=NoopRunner(),  # type: ignore[arg-type]
        tool_resolver=MissingToolResolver(),
        file_store=ValidationStore(
            BackupArtifactInfo(True, True, 8)
        ),  # type: ignore[arg-type]
    )
    size = size_adapter.validate_backup(_backup(tmp_path / "db.dump", size_bytes=4))
    assert size.valid is False
    assert "size does not match" in size.errors[0]

    checksum_adapter = PostgreSQLBackupAdapter(
        runner=NoopRunner(),  # type: ignore[arg-type]
        tool_resolver=MissingToolResolver(),
        file_store=ValidationStore(
            BackupArtifactInfo(True, True, 4),
            checksum="actual",
        ),  # type: ignore[arg-type]
    )
    checksum = checksum_adapter.validate_backup(
        _backup(tmp_path / "db.dump", checksum="expected")
    )
    assert checksum.valid is False
    assert "checksum does not match" in checksum.errors[0]


def test_backup_service_audits_native_tool_failure(tmp_path: Path) -> None:
    audit = AuditCollector()
    service = BackupService(
        backup_port=FailingBackupPort(),
        audit_port=audit,
        config=_config(),
    )
    command = CreateBackupCommand(
        database="accounting",
        format=BackupFormat.CUSTOM,
        output_path=str(tmp_path / "db.dump"),
    )
    plan = service.plan_create_backup(command)

    with pytest.raises(ToolExecutionError):
        service.create_backup(
            command,
            MutationOptions(approved=True),
            plan=plan,
        )

    assert [event.event_type for event in audit.events] == [
        AuditEventType.STARTED,
        AuditEventType.FAILED,
    ]

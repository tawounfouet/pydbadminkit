"""Unit tests for local backup artifact finalization."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from pydbadminkit.domain.common import DatabaseEngine, DatabaseVersion
from pydbadminkit.domain.operations import BackupFormat, BackupMetadata
from pydbadminkit.errors import FileCollisionError
from pydbadminkit.infrastructure.backup_files import LocalBackupFileStore

pytestmark = [pytest.mark.unit, pytest.mark.backup]


def _metadata(checksum: str | None, size_bytes: int) -> BackupMetadata:
    return BackupMetadata(
        backup_id="backup_test",
        database="accounting",
        format=BackupFormat.CUSTOM,
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
        engine=DatabaseEngine.POSTGRESQL,
        engine_version=DatabaseVersion(18),
        tool_version="18",
        size_bytes=size_bytes,
        checksum_algorithm="sha256" if checksum else None,
        checksum=checksum,
    )


def test_file_store_finalizes_and_loads_sidecar(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    target = tmp_path / "accounting.dump"
    paths = store.prepare(str(target), force=False)
    Path(paths.temporary_path).write_bytes(b"backup-data")
    store.secure_artifact(paths.temporary_path)
    checksum = store.sha256(paths.temporary_path)

    store.finalize(
        paths,
        _metadata(checksum, len(b"backup-data")),
        force=False,
    )

    assert target.read_bytes() == b"backup-data"
    assert Path(paths.metadata_path).exists()
    assert not Path(paths.temporary_path).exists()

    backup = store.load_backup(str(target))
    assert backup.id == "backup_test"
    assert backup.checksum == checksum
    assert backup.engine_version == DatabaseVersion(18)


def test_file_store_rejects_collision_without_force(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    target = tmp_path / "accounting.dump"
    target.write_bytes(b"old")

    with pytest.raises(FileCollisionError):
        store.prepare(str(target), force=False)


def test_file_store_force_replaces_existing_artifact(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    target = tmp_path / "accounting.dump"
    target.write_bytes(b"old")
    metadata_path = Path(f"{target}.metadata.json")
    metadata_path.write_text("{}", encoding="utf-8")

    paths = store.prepare(str(target), force=True)
    Path(paths.temporary_path).write_bytes(b"new")
    checksum = store.sha256(paths.temporary_path)

    store.finalize(
        paths,
        _metadata(checksum, 3),
        force=True,
    )

    assert target.read_bytes() == b"new"
    loaded = store.load_backup(str(target))
    assert loaded.checksum == checksum


def test_file_store_cleanup_removes_partial_artifacts(tmp_path: Path) -> None:
    store = LocalBackupFileStore()
    paths = store.prepare(str(tmp_path / "x.dump"), force=False)
    Path(paths.temporary_path).write_bytes(b"x")
    Path(paths.metadata_temporary_path).write_text("{}", encoding="utf-8")

    store.cleanup_temporary(paths)

    assert not Path(paths.temporary_path).exists()
    assert not Path(paths.metadata_temporary_path).exists()

"""Local filesystem backup artifact store."""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydbadminkit.domain.common import (
    DatabaseEngine,
    DatabaseVersion,
    OperationStatus,
)
from pydbadminkit.domain.operations import (
    Backup,
    BackupArtifactInfo,
    BackupFormat,
    BackupMetadata,
    BackupPaths,
)
from pydbadminkit.errors import (
    BackupValidationError,
    FileCollisionError,
    ResourceNotFoundError,
    UnsafePathError,
)


class LocalBackupFileStore:
    """Store one backup artifact beside a secret-safe JSON metadata sidecar."""

    def prepare(self, output_path: str, *, force: bool) -> BackupPaths:
        final_path = Path(output_path).expanduser()
        parent = final_path.parent

        if not parent.exists() or not parent.is_dir():
            raise UnsafePathError(f"Backup parent directory does not exist: '{parent}'.")
        if not os.access(parent, os.W_OK):
            raise UnsafePathError(f"Backup parent directory is not writable: '{parent}'.")
        if final_path.exists() and final_path.is_dir():
            raise UnsafePathError(f"Backup output path is a directory: '{final_path}'.")

        metadata_path = _metadata_path(final_path)
        temporary_path = Path(f"{final_path}.partial")
        metadata_temporary_path = Path(f"{metadata_path}.partial")

        if not force and final_path.exists():
            raise FileCollisionError(f"Backup output already exists: '{final_path}'.")
        if not force and metadata_path.exists():
            raise FileCollisionError(f"Backup metadata already exists: '{metadata_path}'.")
        if temporary_path.exists():
            raise FileCollisionError(
                f"Backup temporary artifact already exists: '{temporary_path}'."
            )
        if metadata_temporary_path.exists():
            raise FileCollisionError(
                f"Backup temporary metadata already exists: '{metadata_temporary_path}'."
            )

        return BackupPaths(
            final_path=str(final_path),
            temporary_path=str(temporary_path),
            metadata_path=str(metadata_path),
            metadata_temporary_path=str(metadata_temporary_path),
        )

    def secure_artifact(self, path: str) -> None:
        try:
            Path(path).chmod(0o600)
        except OSError as error:
            raise UnsafePathError(
                f"Backup artifact permissions could not be restricted: '{path}'."
            ) from error

    def inspect(self, path: str) -> BackupArtifactInfo:
        artifact = Path(path).expanduser()
        if not artifact.exists() or not artifact.is_file():
            return BackupArtifactInfo(
                exists=False,
                readable=False,
                size_bytes=None,
            )
        return BackupArtifactInfo(
            exists=True,
            readable=os.access(artifact, os.R_OK),
            size_bytes=artifact.stat().st_size,
        )

    def sha256(self, path: str) -> str:
        digest = hashlib.sha256()
        try:
            with Path(path).open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
        except OSError as error:
            raise BackupValidationError(
                f"Backup checksum could not be computed for '{path}'."
            ) from error
        return digest.hexdigest()

    def finalize(
        self,
        paths: BackupPaths,
        metadata: BackupMetadata,
        *,
        force: bool,
    ) -> None:
        final_path = Path(paths.final_path)
        temporary_path = Path(paths.temporary_path)
        metadata_path = Path(paths.metadata_path)
        metadata_temporary_path = Path(paths.metadata_temporary_path)

        self._write_metadata(metadata_temporary_path, metadata)

        if force:
            self._replace_with_rollback(
                temporary_path,
                final_path,
                metadata_temporary_path,
                metadata_path,
            )
            return

        artifact_link_created = False
        metadata_link_created = False
        try:
            os.link(temporary_path, final_path)
            artifact_link_created = True
            os.link(metadata_temporary_path, metadata_path)
            metadata_link_created = True
        except FileExistsError as error:
            if artifact_link_created:
                final_path.unlink(missing_ok=True)
            if metadata_link_created:
                metadata_path.unlink(missing_ok=True)
            raise FileCollisionError(
                "Backup destination changed while the operation was running."
            ) from error
        except OSError as error:
            if artifact_link_created:
                final_path.unlink(missing_ok=True)
            if metadata_link_created:
                metadata_path.unlink(missing_ok=True)
            raise UnsafePathError("Backup artifact could not be atomically finalized.") from error

        temporary_path.unlink()
        metadata_temporary_path.unlink()

    def cleanup_temporary(self, paths: BackupPaths) -> None:
        Path(paths.temporary_path).unlink(missing_ok=True)
        Path(paths.metadata_temporary_path).unlink(missing_ok=True)

    def load_backup(self, path: str) -> Backup:
        artifact = Path(path).expanduser()
        if not artifact.exists() or not artifact.is_file():
            raise ResourceNotFoundError(f"Backup artifact not found: '{artifact}'.")

        metadata_path = _metadata_path(artifact)
        if not metadata_path.exists() or not metadata_path.is_file():
            raise BackupValidationError(f"Backup metadata sidecar not found: '{metadata_path}'.")

        try:
            raw = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata = _metadata_from_dict(raw)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise BackupValidationError(
                f"Backup metadata sidecar is invalid: '{metadata_path}'."
            ) from error

        return Backup(
            id=metadata.backup_id,
            database=metadata.database,
            format=metadata.format,
            path=str(artifact),
            created_at=metadata.created_at,
            size_bytes=metadata.size_bytes,
            checksum=metadata.checksum,
            engine=metadata.engine,
            engine_version=metadata.engine_version,
            tool_version=metadata.tool_version,
            status=OperationStatus.SUCCEEDED,
        )

    def _write_metadata(
        self,
        path: Path,
        metadata: BackupMetadata,
    ) -> None:
        payload = {
            "backup_id": metadata.backup_id,
            "database": metadata.database,
            "format": metadata.format.value,
            "created_at": metadata.created_at.isoformat(),
            "engine": metadata.engine.value,
            "engine_version": (
                str(metadata.engine_version) if metadata.engine_version is not None else None
            ),
            "tool_version": metadata.tool_version,
            "size_bytes": metadata.size_bytes,
            "checksum_algorithm": metadata.checksum_algorithm,
            "checksum": metadata.checksum,
        }

        try:
            descriptor = os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        except OSError as error:
            raise UnsafePathError(f"Backup metadata could not be written: '{path}'.") from error

    @staticmethod
    def _replace_with_rollback(
        temporary_path: Path,
        final_path: Path,
        metadata_temporary_path: Path,
        metadata_path: Path,
    ) -> None:
        token = uuid4().hex
        artifact_rollback = Path(f"{final_path}.rollback.{token}")
        metadata_rollback = Path(f"{metadata_path}.rollback.{token}")
        moved_artifact = False
        moved_metadata = False

        try:
            if final_path.exists():
                os.replace(final_path, artifact_rollback)
                moved_artifact = True
            if metadata_path.exists():
                os.replace(metadata_path, metadata_rollback)
                moved_metadata = True

            os.replace(temporary_path, final_path)
            os.replace(metadata_temporary_path, metadata_path)
        except OSError as error:
            final_path.unlink(missing_ok=True)
            metadata_path.unlink(missing_ok=True)
            if moved_artifact and artifact_rollback.exists():
                os.replace(artifact_rollback, final_path)
            if moved_metadata and metadata_rollback.exists():
                os.replace(metadata_rollback, metadata_path)
            raise UnsafePathError("Backup overwrite could not be atomically finalized.") from error
        else:
            artifact_rollback.unlink(missing_ok=True)
            metadata_rollback.unlink(missing_ok=True)


def _metadata_path(artifact: Path) -> Path:
    return Path(f"{artifact}.metadata.json")


def _metadata_from_dict(raw: object) -> BackupMetadata:
    if not isinstance(raw, dict):
        raise TypeError("backup metadata must be a JSON object")

    engine_version_raw = raw.get("engine_version")
    engine_version = (
        _parse_database_version(engine_version_raw) if engine_version_raw is not None else None
    )

    return BackupMetadata(
        backup_id=str(raw["backup_id"]),
        database=str(raw["database"]),
        format=BackupFormat(str(raw["format"])),
        created_at=datetime.fromisoformat(str(raw["created_at"])),
        engine=DatabaseEngine(str(raw["engine"])),
        engine_version=engine_version,
        tool_version=_optional_string(raw.get("tool_version")),
        size_bytes=_optional_int(raw.get("size_bytes")),
        checksum_algorithm=_optional_string(raw.get("checksum_algorithm")),
        checksum=_optional_string(raw.get("checksum")),
    )


def _parse_database_version(value: object) -> DatabaseVersion:
    parts = str(value).split(".")
    numbers = [int(part) for part in parts]
    while len(numbers) < 3:
        numbers.append(0)
    return DatabaseVersion(*numbers[:3])


def _optional_string(value: object) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("boolean is not a valid size")
    return int(value)

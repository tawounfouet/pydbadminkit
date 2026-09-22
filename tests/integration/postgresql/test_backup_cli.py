"""PostgreSQL logical backup integration tests."""

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pydbadminkit.cli.app import app

pytestmark = [pytest.mark.integration, pytest.mark.postgresql, pytest.mark.backup]

runner = CliRunner()


def _host() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_HOST", "127.0.0.1")


def _port() -> int:
    return int(os.getenv("PYDBADMIN_TEST_POSTGRES_PORT", "5432"))


def _database() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_DATABASE", "pydbadmin_test")


def _user() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_USER", "postgres")


def _password() -> str:
    return os.getenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", "postgres")


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(
        f"""
[connections.local]
engine = "postgresql"
host = "{_host()}"
port = {_port()}
database = "{_database()}"
username = "{_user()}"
environment = "testing"
read_only = false
ssl_mode = "disable"
connect_timeout_seconds = 5

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_TEST_POSTGRES_PASSWORD"
""".strip(),
        encoding="utf-8",
    )
    return path


def _base_args(config: Path) -> list[str]:
    return ["--connection", "local", "--config", str(config)]


@pytest.fixture
def backup_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    monkeypatch.setenv("PYDBADMIN_TEST_POSTGRES_PASSWORD", _password())
    audit_path = tmp_path / "backup-audit.jsonl"
    monkeypatch.setenv("PYDBADMIN_AUDIT_PATH", str(audit_path))
    return _config(tmp_path), audit_path


def test_custom_backup_create_and_validate_with_native_tools(
    tmp_path: Path,
    backup_environment: tuple[Path, Path],
) -> None:
    config, audit_path = backup_environment
    target = tmp_path / "database.dump"

    create = runner.invoke(
        app,
        [
            *_base_args(config),
            "backup",
            "create",
            _database(),
            "--format",
            "custom",
            "--output-path",
            str(target),
        ],
    )

    assert create.exit_code == 0, create.output
    assert target.exists()
    assert target.stat().st_size > 0
    assert not Path(f"{target}.partial").exists()
    sidecar = Path(f"{target}.metadata.json")
    assert sidecar.exists()

    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    assert metadata["database"] == _database()
    assert metadata["format"] == "custom"
    assert metadata["checksum_algorithm"] == "sha256"
    assert metadata["checksum"]
    assert _password() not in sidecar.read_text(encoding="utf-8")
    assert _password() not in create.output

    validate = runner.invoke(
        app,
        ["--output", "json", "backup", "validate", str(target)],
    )

    assert validate.exit_code == 0, validate.output
    parsed = json.loads(validate.stdout)
    assert parsed["valid"] is True
    assert parsed["level"] == "logical"

    events = [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [event["event_type"] for event in events[-2:]] == [
        "started",
        "succeeded",
    ]
    assert events[-1]["operation"] == "backup.create"


def test_plain_backup_and_collision_guard(
    tmp_path: Path,
    backup_environment: tuple[Path, Path],
) -> None:
    config, _audit_path = backup_environment
    target = tmp_path / "database.sql"

    first = runner.invoke(
        app,
        [
            *_base_args(config),
            "backup",
            "create",
            _database(),
            "--format",
            "plain_sql",
            "--output-path",
            str(target),
        ],
    )
    second = runner.invoke(
        app,
        [
            *_base_args(config),
            "backup",
            "create",
            _database(),
            "--format",
            "plain_sql",
            "--output-path",
            str(target),
        ],
    )

    assert first.exit_code == 0, first.output
    assert target.exists()
    assert second.exit_code == 8
    assert "already exists" in second.output

    validate = runner.invoke(
        app,
        ["--output", "json", "backup", "validate", str(target)],
    )
    assert validate.exit_code == 0, validate.output
    parsed = json.loads(validate.stdout)
    assert parsed["valid"] is True
    assert parsed["level"] == "artifact"
    assert parsed["warnings"]


def test_force_backup_replaces_existing_artifact(
    tmp_path: Path,
    backup_environment: tuple[Path, Path],
) -> None:
    config, _audit_path = backup_environment
    target = tmp_path / "database.dump"
    target.write_bytes(b"stale")
    Path(f"{target}.metadata.json").write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            *_base_args(config),
            "--yes",
            "backup",
            "create",
            _database(),
            "--output-path",
            str(target),
            "--force",
        ],
    )

    assert result.exit_code == 0, result.output
    assert target.read_bytes() != b"stale"
    metadata = json.loads(
        Path(f"{target}.metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["database"] == _database()

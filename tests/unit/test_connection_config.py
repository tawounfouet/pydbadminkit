"""Unit tests for connection configuration and secret resolution."""

from pathlib import Path

import pytest

from pydbadminkit.application.connection import ConnectionConfigResolver
from pydbadminkit.domain.common import DatabaseEngine, EnvironmentName
from pydbadminkit.domain.connection import (
    ConnectionProfileName,
    SSLMode,
    SecretReference,
)
from pydbadminkit.errors import ConfigurationError, ProfileNotFoundError
from pydbadminkit.infrastructure.config import TomlConnectionProfileRepository
from pydbadminkit.infrastructure.secrets import EnvironmentSecretProvider

pytestmark = pytest.mark.unit


def _write_config(path: Path) -> None:
    path.write_text(
        """
[connections.local]
engine = "postgresql"
host = "localhost"
port = 5432
database = "pydbadmin_dev"
username = "postgres"
environment = "development"
read_only = false
ssl_mode = "disable"
connect_timeout_seconds = 5

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"
""".strip(),
        encoding="utf-8",
    )


def test_toml_repository_loads_connection_profile(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    _write_config(path)
    repository = TomlConnectionProfileRepository(path)

    profile = repository.get_connection_profile(ConnectionProfileName("local"))

    assert profile.engine is DatabaseEngine.POSTGRESQL
    assert profile.environment is EnvironmentName.DEVELOPMENT
    assert profile.ssl.mode is SSLMode.DISABLE
    assert profile.timeouts.connect_seconds == 5
    assert profile.secret == SecretReference(
        provider="env",
        reference="PYDBADMIN_LOCAL_PASSWORD",
    )


def test_toml_repository_reports_missing_profile(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    _write_config(path)
    repository = TomlConnectionProfileRepository(path)

    with pytest.raises(ProfileNotFoundError):
        repository.get_connection_profile(ConnectionProfileName("missing"))


def test_toml_repository_reports_invalid_file(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[connections.local", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        TomlConnectionProfileRepository(path).list_connection_profiles()


def test_environment_secret_provider_redacts_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_secret = "SUPER_SECRET_SENTINEL"
    monkeypatch.setenv("PYDBADMIN_LOCAL_PASSWORD", raw_secret)

    secret = EnvironmentSecretProvider().resolve(
        SecretReference(provider="env", reference="PYDBADMIN_LOCAL_PASSWORD")
    )

    assert secret.reveal() == raw_secret
    assert raw_secret not in str(secret)
    assert raw_secret not in repr(secret)


def test_connection_config_resolver_resolves_environment_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "config.toml"
    _write_config(path)
    monkeypatch.setenv("PYDBADMIN_LOCAL_PASSWORD", "postgres")

    resolver = ConnectionConfigResolver(
        repository=TomlConnectionProfileRepository(path),
        secret_providers=(EnvironmentSecretProvider(),),
    )
    resolved = resolver.resolve("local")

    assert resolved.name == ConnectionProfileName("local")
    assert resolved.password is not None
    assert resolved.password.reveal() == "postgres"

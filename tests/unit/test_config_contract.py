"""Stable implemented configuration contract for LOT-20."""

from pathlib import Path

import pytest

from pydbadminkit.domain.common import DatabaseEngine, EnvironmentName
from pydbadminkit.domain.connection import ConnectionProfileName, SSLMode, SecretReference
from pydbadminkit.infrastructure.config import (
    TomlConnectionProfileRepository,
    default_config_path,
)

pytestmark = pytest.mark.unit


def _repository(tmp_path: Path, content: str) -> TomlConnectionProfileRepository:
    path = tmp_path / "config.toml"
    path.write_text(content.strip(), encoding="utf-8")
    return TomlConnectionProfileRepository(path)


def test_minimal_profile_defaults_are_frozen(tmp_path: Path) -> None:
    repository = _repository(
        tmp_path,
        """
[connections.minimal]
host = "localhost"
database = "postgres"
username = "postgres"
""",
    )

    profile = repository.get_connection_profile(ConnectionProfileName("minimal"))

    assert profile.engine is DatabaseEngine.POSTGRESQL
    assert profile.port == 5432
    assert profile.environment is EnvironmentName.UNKNOWN
    assert profile.read_only is False
    assert profile.ssl.mode is SSLMode.PREFER
    assert profile.ssl.root_cert is None
    assert profile.ssl.cert is None
    assert profile.ssl.key is None
    assert profile.timeouts.connect_seconds == 10
    assert profile.timeouts.statement_ms is None
    assert profile.timeouts.lock_ms is None
    assert profile.secret is None


def test_complete_profile_field_mapping_is_frozen(tmp_path: Path) -> None:
    repository = _repository(
        tmp_path,
        """
[connections.prod]
engine = "postgresql"
host = "db.internal"
port = 5433
database = "analytics"
username = "pydbadmin"
environment = "production"
read_only = true
ssl_mode = "verify-full"
ssl_root_cert = "/certs/root.pem"
ssl_cert = "/certs/client.pem"
ssl_key = "/certs/client.key"
connect_timeout_seconds = 3
statement_timeout_ms = 5000
lock_timeout_ms = 2000

[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
""",
    )

    profile = repository.get_connection_profile(ConnectionProfileName("prod"))

    assert profile.engine is DatabaseEngine.POSTGRESQL
    assert profile.host == "db.internal"
    assert profile.port == 5433
    assert profile.database == "analytics"
    assert profile.username == "pydbadmin"
    assert profile.environment is EnvironmentName.PRODUCTION
    assert profile.read_only is True
    assert profile.ssl.mode is SSLMode.VERIFY_FULL
    assert profile.ssl.root_cert == "/certs/root.pem"
    assert profile.ssl.cert == "/certs/client.pem"
    assert profile.ssl.key == "/certs/client.key"
    assert profile.timeouts.connect_seconds == 3
    assert profile.timeouts.statement_ms == 5000
    assert profile.timeouts.lock_ms == 2000
    assert profile.secret == SecretReference(
        provider="env",
        reference="PYDBADMIN_PROD_PASSWORD",
    )


def test_environment_and_ssl_wire_values_are_frozen() -> None:
    assert tuple(item.value for item in EnvironmentName) == (
        "development",
        "testing",
        "staging",
        "production",
        "unknown",
    )
    assert tuple(item.value for item in SSLMode) == (
        "disable",
        "allow",
        "prefer",
        "require",
        "verify-ca",
        "verify-full",
    )


def test_profile_listing_order_is_deterministic(tmp_path: Path) -> None:
    repository = _repository(
        tmp_path,
        """
[connections.zeta]
host = "zeta"
database = "postgres"
username = "postgres"

[connections.alpha]
host = "alpha"
database = "postgres"
username = "postgres"
""",
    )

    assert tuple(str(profile.name) for profile in repository.list_connection_profiles()) == (
        "alpha",
        "zeta",
    )


def test_default_config_path_contract() -> None:
    path = default_config_path()

    assert path.name == "config.toml"
    assert path.parent.name == "pydbadminkit"

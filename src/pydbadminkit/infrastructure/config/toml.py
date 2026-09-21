"""TOML-backed connection profile repository."""

from collections.abc import Mapping
from pathlib import Path
from typing import cast
import tomllib

from pydbadminkit.domain.common.engine import DatabaseEngine
from pydbadminkit.domain.common.environment import EnvironmentName
from pydbadminkit.domain.connection.profile import ConnectionProfile, ConnectionProfileName
from pydbadminkit.domain.connection.secrets import SecretReference
from pydbadminkit.domain.connection.ssl import SSLConfig, SSLMode
from pydbadminkit.domain.connection.timeouts import TimeoutConfig
from pydbadminkit.errors import ConfigurationError, ProfileNotFoundError


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{label} must be a TOML table.")
    return cast(Mapping[str, object], value)


def _required_str(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value or value.isspace():
        raise ConfigurationError(f"Configuration field '{key}' must be a non-blank string.")
    return value


def _optional_str(data: Mapping[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value or value.isspace():
        raise ConfigurationError(f"Configuration field '{key}' must be a non-blank string.")
    return value


def _optional_int(data: Mapping[str, object], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigurationError(f"Configuration field '{key}' must be an integer.")
    return value


def _bool(data: Mapping[str, object], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ConfigurationError(f"Configuration field '{key}' must be a boolean.")
    return value


class TomlConnectionProfileRepository:
    """Read connection profiles from one TOML configuration file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def get_connection_profile(self, name: ConnectionProfileName) -> ConnectionProfile:
        profiles = self._load_profiles()
        profile = profiles.get(name.value)
        if profile is None:
            raise ProfileNotFoundError(
                f"Connection profile '{name}' was not found in '{self._path}'."
            )
        return profile

    def list_connection_profiles(self) -> tuple[ConnectionProfile, ...]:
        profiles = self._load_profiles()
        return tuple(profiles[name] for name in sorted(profiles))

    def _load_profiles(self) -> dict[str, ConnectionProfile]:
        try:
            document = cast(dict[str, object], tomllib.loads(self._path.read_text(encoding="utf-8")))
        except FileNotFoundError as error:
            raise ConfigurationError(
                f"Configuration file '{self._path}' was not found."
            ) from error
        except tomllib.TOMLDecodeError as error:
            raise ConfigurationError(
                f"Configuration file '{self._path}' contains invalid TOML."
            ) from error

        connections_value = document.get("connections", {})
        connections = _mapping(connections_value, "connections")
        profiles: dict[str, ConnectionProfile] = {}

        for raw_name, raw_profile in connections.items():
            profile_data = _mapping(raw_profile, f"connections.{raw_name}")
            profiles[raw_name] = self._parse_profile(raw_name, profile_data)

        return profiles

    def _parse_profile(
        self,
        raw_name: str,
        data: Mapping[str, object],
    ) -> ConnectionProfile:
        try:
            engine = DatabaseEngine(str(data.get("engine", DatabaseEngine.POSTGRESQL.value)))
            environment = EnvironmentName(
                str(data.get("environment", EnvironmentName.UNKNOWN.value))
            )
            ssl_mode = SSLMode(str(data.get("ssl_mode", SSLMode.PREFER.value)))

            port_value = data.get("port", 5432)
            if not isinstance(port_value, int) or isinstance(port_value, bool):
                raise ConfigurationError("Configuration field 'port' must be an integer.")

            secret: SecretReference | None = None
            secret_value = data.get("secret")
            if secret_value is not None:
                secret_data = _mapping(secret_value, f"connections.{raw_name}.secret")
                secret = SecretReference(
                    provider=_required_str(secret_data, "provider"),
                    reference=_required_str(secret_data, "reference"),
                )

            return ConnectionProfile(
                name=ConnectionProfileName(raw_name),
                engine=engine,
                host=_required_str(data, "host"),
                port=port_value,
                database=_required_str(data, "database"),
                username=_required_str(data, "username"),
                secret=secret,
                environment=environment,
                read_only=_bool(data, "read_only", False),
                ssl=SSLConfig(
                    mode=ssl_mode,
                    root_cert=_optional_str(data, "ssl_root_cert"),
                    cert=_optional_str(data, "ssl_cert"),
                    key=_optional_str(data, "ssl_key"),
                ),
                timeouts=TimeoutConfig(
                    connect_seconds=_optional_int(data, "connect_timeout_seconds") or 10,
                    statement_ms=_optional_int(data, "statement_timeout_ms"),
                    lock_ms=_optional_int(data, "lock_timeout_ms"),
                ),
            )
        except (ValueError, TypeError) as error:
            if isinstance(error, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Connection profile '{raw_name}' is invalid: {error}"
            ) from error

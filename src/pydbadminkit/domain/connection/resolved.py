"""Resolved runtime connection configuration."""

from dataclasses import dataclass

from pydbadminkit.domain.common.engine import DatabaseEngine
from pydbadminkit.domain.common.environment import EnvironmentName
from pydbadminkit.domain.connection.profile import ConnectionProfileName
from pydbadminkit.domain.connection.secrets import SecretValue
from pydbadminkit.domain.connection.ssl import SSLConfig
from pydbadminkit.domain.connection.timeouts import TimeoutConfig


@dataclass(frozen=True, slots=True)
class ResolvedConnectionConfig:
    """Connection configuration ready for an engine adapter."""

    name: ConnectionProfileName
    engine: DatabaseEngine
    host: str
    port: int
    database: str
    username: str
    password: SecretValue | None
    environment: EnvironmentName
    read_only: bool
    ssl: SSLConfig
    timeouts: TimeoutConfig

    def __post_init__(self) -> None:
        if not self.host or self.host.isspace():
            raise ValueError("host must not be blank")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if not self.database or self.database.isspace():
            raise ValueError("database must not be blank")
        if not self.username or self.username.isspace():
            raise ValueError("username must not be blank")

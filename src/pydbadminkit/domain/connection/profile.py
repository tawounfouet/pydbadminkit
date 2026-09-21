"""Connection profile domain models."""

from dataclasses import dataclass, field

from pydbadminkit.domain.common.engine import DatabaseEngine
from pydbadminkit.domain.common.environment import EnvironmentName
from pydbadminkit.domain.connection.secrets import SecretReference
from pydbadminkit.domain.connection.ssl import SSLConfig
from pydbadminkit.domain.connection.timeouts import TimeoutConfig


@dataclass(frozen=True, slots=True)
class ConnectionProfileName:
    """Validated connection profile name."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or self.value.isspace():
            raise ValueError("connection profile name must not be blank")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ConnectionProfile:
    """Persisted connection profile without resolved secret material."""

    name: ConnectionProfileName
    engine: DatabaseEngine
    host: str
    port: int
    database: str
    username: str
    secret: SecretReference | None = None
    environment: EnvironmentName = EnvironmentName.UNKNOWN
    read_only: bool = False
    ssl: SSLConfig = field(default_factory=SSLConfig)
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)

    def __post_init__(self) -> None:
        if not self.host or self.host.isspace():
            raise ValueError("host must not be blank")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if not self.database or self.database.isspace():
            raise ValueError("database must not be blank")
        if not self.username or self.username.isspace():
            raise ValueError("username must not be blank")

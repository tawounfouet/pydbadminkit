"""Connection-related domain primitives."""

from pydbadminkit.domain.connection.profile import ConnectionProfile, ConnectionProfileName
from pydbadminkit.domain.connection.resolved import ResolvedConnectionConfig
from pydbadminkit.domain.connection.result import ConnectionTestResult
from pydbadminkit.domain.connection.secrets import SecretReference, SecretValue
from pydbadminkit.domain.connection.ssl import SSLConfig, SSLMode
from pydbadminkit.domain.connection.timeouts import TimeoutConfig

__all__ = [
    "ConnectionProfile",
    "ConnectionProfileName",
    "ConnectionTestResult",
    "ResolvedConnectionConfig",
    "SSLConfig",
    "SSLMode",
    "SecretReference",
    "SecretValue",
    "TimeoutConfig",
]

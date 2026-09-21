"""Connection operation results."""

from dataclasses import dataclass

from pydbadminkit.domain.common.database_version import DatabaseVersion
from pydbadminkit.domain.common.engine import DatabaseEngine


@dataclass(frozen=True, slots=True)
class ConnectionTestResult:
    """Successful database connection test result."""

    engine: DatabaseEngine
    version: DatabaseVersion
    current_database: str
    current_user: str
    latency_ms: float

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be >= 0")

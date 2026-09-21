"""Safe technical context attached to public errors."""

from dataclasses import dataclass

from pydbadminkit.domain.common.engine import DatabaseEngine
from pydbadminkit.domain.common.environment import EnvironmentName


@dataclass(frozen=True, slots=True)
class ErrorContext:
    """Non-secret structured context for diagnostics."""

    operation: str | None = None
    resource_type: str | None = None
    resource_name: str | None = None
    engine: DatabaseEngine | None = None
    profile: str | None = None
    environment: EnvironmentName | None = None
    sqlstate: str | None = None
    capability: str | None = None
    correlation_id: str | None = None

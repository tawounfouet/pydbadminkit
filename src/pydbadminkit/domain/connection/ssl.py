"""SSL configuration primitives."""

from dataclasses import dataclass
from enum import StrEnum


class SSLMode(StrEnum):
    """libpq-compatible SSL modes."""

    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


@dataclass(frozen=True, slots=True)
class SSLConfig:
    """Engine-independent connection SSL configuration."""

    mode: SSLMode = SSLMode.PREFER
    root_cert: str | None = None
    cert: str | None = None
    key: str | None = None

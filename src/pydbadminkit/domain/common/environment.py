"""Deployment environment identifiers."""

from enum import StrEnum


class EnvironmentName(StrEnum):
    """Environment classification used by safety policies."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    UNKNOWN = "unknown"

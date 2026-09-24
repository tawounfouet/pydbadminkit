"""Monitoring enumerations."""

from enum import StrEnum


class HealthStatus(StrEnum):
    """Normalized health status for point-in-time checks."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthCheckCategory(StrEnum):
    """Stable health-check categories."""

    CONNECTIVITY = "connectivity"
    CONNECTIONS = "connections"
    QUERIES = "queries"
    TRANSACTIONS = "transactions"
    LOCKS = "locks"
    STORAGE = "storage"
    TABLES = "tables"
    INDEXES = "indexes"
    BACKUP = "backup"
    REPLICATION = "replication"

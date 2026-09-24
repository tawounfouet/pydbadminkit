"""PostgreSQL adapter implementation."""

from pydbadminkit.adapters.postgresql.backup import PostgreSQLBackupAdapter
from pydbadminkit.adapters.postgresql.capabilities import PostgreSQLCapabilityAdapter
from pydbadminkit.adapters.postgresql.catalog import PostgreSQLCatalogAdapter
from pydbadminkit.adapters.postgresql.connection import (
    PostgreSQLConnectionFactory,
    PostgreSQLConnectionTester,
)
from pydbadminkit.adapters.postgresql.executor import PostgreSQLExecutor
from pydbadminkit.adapters.postgresql.maintenance import PostgreSQLMaintenanceAdapter
from pydbadminkit.adapters.postgresql.monitoring import PostgreSQLMonitoringAdapter
from pydbadminkit.adapters.postgresql.restore import PostgreSQLRestoreAdapter
from pydbadminkit.adapters.postgresql.restore_database import PostgreSQLRestoreDatabaseAdapter
from pydbadminkit.adapters.postgresql.runtime import PostgreSQLRuntimeAdapter
from pydbadminkit.adapters.postgresql.security import PostgreSQLSecurityAdapter
from pydbadminkit.adapters.postgresql.server import PostgreSQLServerAdapter

__all__ = [
    "PostgreSQLBackupAdapter",
    "PostgreSQLCapabilityAdapter",
    "PostgreSQLCatalogAdapter",
    "PostgreSQLConnectionFactory",
    "PostgreSQLConnectionTester",
    "PostgreSQLExecutor",
    "PostgreSQLMaintenanceAdapter",
    "PostgreSQLMonitoringAdapter",
    "PostgreSQLRestoreAdapter",
    "PostgreSQLRestoreDatabaseAdapter",
    "PostgreSQLRuntimeAdapter",
    "PostgreSQLSecurityAdapter",
    "PostgreSQLServerAdapter",
]

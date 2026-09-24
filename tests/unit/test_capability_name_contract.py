"""Stable capability-name contract for LOT-20."""

import pytest

from pydbadminkit.adapters.postgresql.capabilities import PostgreSQLCapabilityAdapter

pytestmark = pytest.mark.unit

EXPECTED_CAPABILITY_NAMES = (
    "backup.create",
    "backup.restore",
    "backup.validate",
    "catalog.database.describe",
    "catalog.database.list",
    "catalog.index.describe",
    "catalog.index.list",
    "catalog.schema.describe",
    "catalog.schema.list",
    "catalog.table.describe",
    "catalog.table.list",
    "catalog.view.describe",
    "catalog.view.list",
    "connection.test",
    "maintenance.analyze",
    "maintenance.reindex",
    "maintenance.vacuum",
    "monitoring.connection.statistics",
    "monitoring.database.sizes",
    "monitoring.health",
    "monitoring.index.statistics",
    "monitoring.table.statistics",
    "postgres.reindex.concurrently",
    "postgres.reindex.progress",
    "postgres.vacuum.progress",
    "runtime.blocking.list",
    "runtime.lock.list",
    "runtime.query.cancel",
    "runtime.query.list",
    "runtime.session.list",
    "runtime.session.terminate",
    "runtime.transaction.list",
    "runtime.wait.list",
    "security.access.direct.list",
    "security.access.effective.list",
    "security.access.grant",
    "security.access.revoke",
    "security.membership.add",
    "security.membership.list",
    "security.membership.remove",
    "security.ownership.list",
    "security.role.alter",
    "security.role.create",
    "security.role.describe",
    "security.role.drop",
    "security.role.list",
    "server.info",
)


def test_postgresql_capability_names_match_frozen_contract() -> None:
    capabilities = PostgreSQLCapabilityAdapter().list_capabilities()

    assert tuple(capability.name for capability in capabilities) == EXPECTED_CAPABILITY_NAMES

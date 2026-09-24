# LOT-20 / T20-007 — Capability-Name Freeze

## Status

```text
Ticket: T20-007
Lot: LOT-20 — Hardening
Baseline: 0.6.0
Contract: frozen for the route to 1.0
```

Capability names are machine-readable identifiers returned by the capability discovery API
and CLI. Their spelling is therefore part of the compatibility surface.

## Frozen capability names

```text
backup.create
backup.restore
backup.validate
catalog.database.describe
catalog.database.list
catalog.index.describe
catalog.index.list
catalog.schema.describe
catalog.schema.list
catalog.table.describe
catalog.table.list
catalog.view.describe
catalog.view.list
connection.test
maintenance.analyze
maintenance.reindex
maintenance.vacuum
monitoring.connection.statistics
monitoring.database.sizes
monitoring.health
monitoring.index.statistics
monitoring.table.statistics
postgres.reindex.concurrently
postgres.reindex.progress
postgres.vacuum.progress
runtime.blocking.list
runtime.lock.list
runtime.query.cancel
runtime.query.list
runtime.session.list
runtime.session.terminate
runtime.transaction.list
runtime.wait.list
security.access.direct.list
security.access.effective.list
security.access.grant
security.access.revoke
security.membership.add
security.membership.list
security.membership.remove
security.ownership.list
security.role.alter
security.role.create
security.role.describe
security.role.drop
security.role.list
server.info
```

The list is returned in deterministic lexical order.

## Naming convention

Current names follow a dot-separated hierarchy:

```text
<domain>.<resource>.<action>
```

Some PostgreSQL-specific capabilities use the `postgres.` namespace and monitoring
statistics may use a four-segment form.

Names describe capability identity, not current availability. Availability remains a
separate `CapabilityAvailability` value.

## Compatibility rules

Before a future major-version compatibility break:

- a frozen capability name must not be removed or renamed silently;
- a name must not be reused for different semantics;
- new capabilities are additive;
- engine-specific additions should use an explicit namespace when they are not portable;
- availability changes do not rename the capability;
- aliases, if introduced, must not replace the canonical frozen name without deprecation.

## Automated drift guard

`tests/unit/test_capability_name_contract.py` compares the complete capability list
returned by the PostgreSQL capability adapter with this frozen set.

## Next ticket

```text
T20-008 — operation-name freeze
```

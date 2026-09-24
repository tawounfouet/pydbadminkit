# LOT-20 / T20-008 — Operation-Name Freeze

## Status

```text
Ticket: T20-008
Lot: LOT-20 — Hardening
Baseline: 0.6.0
Contract: frozen for the route to 1.0
```

Guarded administrative mutations expose stable operation names in plans, audit events and
operation results. T20-008 centralizes those identifiers in the public `OperationName`
enum so application services no longer own independent string literals.

## Public API

```python
from pydbadminkit.domain.common import OperationName
```

## Frozen mutation operation names

```text
backup.create
backup.restore
maintenance.analyze
maintenance.reindex
maintenance.vacuum
runtime.query.cancel
runtime.session.terminate
security.access.grant
security.access.revoke
security.membership.add
security.membership.remove
security.role.alter
security.role.create
security.role.drop
```

These names are used by `OperationPlan.operation`, successful `OperationResult.operation`
and mutation audit events.

## Scope boundary

This contract covers **guarded mutation operation identities**. It does not redefine:

- capability names, frozen separately by T20-007;
- SQL/query identifiers used internally by adapters;
- error-context operation strings such as connection-open diagnostics;
- maintenance operation types (`vacuum`, `analyze`, `reindex`) used by maintenance
  read models.

## Compatibility rules

Before a future major-version compatibility break:

- existing `OperationName` wire values must not be removed, renamed or repurposed;
- plans, audit events and results for the same mutation must use the same canonical name;
- new guarded mutations require an additive `OperationName`;
- application services must use the enum instead of introducing new free-form mutation
  literals.

## Automated drift guard

`tests/unit/test_operation_name_contract.py` freezes the complete wire-value set.
T20-001 additionally freezes `OperationName` as a public export.

## Next ticket

```text
T20-009 — security review
```

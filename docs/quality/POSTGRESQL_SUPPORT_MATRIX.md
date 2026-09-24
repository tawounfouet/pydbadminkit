# LOT-20 / T20-014 — PostgreSQL Support Matrix

## Status

```text
Ticket: T20-014
Lot: LOT-20 — Hardening
Release line: 1.0 qualification
Matrix: PostgreSQL 14–18
```

## Frozen support levels

| PostgreSQL | 1.0 qualification level | CI |
| --- | --- | --- |
| 18 | Tier A | full integration |
| 17 | Tier A | full integration |
| 16 | Tier A | full integration |
| 15 | Tier A | full integration |
| 14 | Transitional | full integration during 2026 qualification |
| 19 beta/devel | Unsupported | none |

This follows the PostgreSQL implementation specification: 15–18 are Tier A, PostgreSQL 14
is transitional during the 2026 implementation phase, and development/beta PostgreSQL 19
does not carry a support promise.

## CI enforcement

The PostgreSQL integration workflow now runs the same integration suite against:

```text
14
15
16
17
18
```

Each matrix job uses:

- a server container matching the matrix version;
- matching PostgreSQL client tools;
- Python 3.13 for the PostgreSQL compatibility axis;
- the same integration marker selection.

This isolates the database-version axis from the Python-version axis.

## Native-tool rule

For matrix qualification, `pg_dump`, `pg_restore` and `psql` match the server major
version.

Runtime code remains version-aware:

- `pg_dump` older than the server is rejected;
- restore tools older than the target server are rejected;
- newer `pg_dump` may be accepted with identifier-quoting compatibility handling.

## Version-specific behavior

The current supported matrix is entirely PostgreSQL 14+, so the implemented
`REINDEX CONCURRENTLY` minimum of PostgreSQL 12 is available throughout the supported
matrix. The adapter nevertheless retains the explicit version guard so the capability
boundary remains correct if a lower server is encountered outside the support matrix.

Version-specific divergence must continue to be represented by:

```text
capability
query variant where required
test
documentation
```

## PostgreSQL 14 transition

PostgreSQL 14 remains transitional for the current 2026 qualification window. Its support
status must be re-evaluated at the actual 1.0 release boundary according to upstream
community support status.

Removing PostgreSQL 14 from a future support matrix must be an explicit release-policy
decision; a passing implementation does not by itself extend upstream lifecycle support.

## Managed PostgreSQL

RDS PostgreSQL, Azure Database for PostgreSQL and Cloud SQL PostgreSQL remain best-effort
compatibility targets. This matrix qualifies PostgreSQL engine versions, not provider-
specific privilege restrictions or managed-service control planes.

## Release gate

```text
A PostgreSQL version is not claimed as supported unless its matrix job is green.
Tier A 1.0 release requires 15, 16, 17 and 18 green.
PostgreSQL 14 remains qualified as Transitional while it is retained in the matrix.
```

## Next ticket

```text
T20-015 — package metadata review
```

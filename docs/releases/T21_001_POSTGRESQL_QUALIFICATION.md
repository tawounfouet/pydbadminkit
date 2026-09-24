# LOT-21 / T21-001 — Full PostgreSQL Qualification

## Decision

```text
Ticket: T21-001
Result: PASS
Qualified matrix: PostgreSQL 14, 15, 16, 17, 18
Tier A: 15, 16, 17, 18
Transitional: 14
```

## Qualification basis

LOT-20 converted PostgreSQL integration from a single-version PostgreSQL 18 job into a
real server/client matrix. T21-001 treats that matrix as the release qualification
boundary and records its result for the 1.0 gate.

Each matrix member executes the same PostgreSQL integration suite with:

- a PostgreSQL server matching the matrix major;
- matching `pg_dump`, `pg_restore` and `psql` client tools;
- Python 3.13 as the fixed Python axis;
- the same `integration and postgresql` pytest selection;
- version-aware assertions against the actual server major.

## Qualified result

```text
PostgreSQL 14  44 passed
PostgreSQL 15  44 passed
PostgreSQL 16  44 passed
PostgreSQL 17  44 passed
PostgreSQL 18  44 passed

Total matrix executions: 220 passed
```

No PostgreSQL integration failure remains on the qualified matrix.

## Release interpretation

For the 1.0 release gate:

```text
PostgreSQL 15  Tier A  GREEN
PostgreSQL 16  Tier A  GREEN
PostgreSQL 17  Tier A  GREEN
PostgreSQL 18  Tier A  GREEN
PostgreSQL 14  Transitional  GREEN
```

The release condition "all Tier A PostgreSQL versions green" is therefore satisfied by
the current implementation.

PostgreSQL 14 remains explicitly Transitional. A later support-policy decision may remove
it according to upstream lifecycle status; this qualification does not silently convert
it into a permanent Tier A promise.

## Covered PostgreSQL surfaces

The integration suite exercises the live PostgreSQL adapter/CLI path for the implemented
feature lines, including connection/server information, catalog, security/runtime
surfaces and the integration contracts already carried by the repository.

Native backup/restore compatibility receives its dedicated end-to-end qualification in
T21-003.

## Reproducibility

The authoritative executable contract is:

```text
.github/workflows/postgresql-integration.yml
pytest -m "integration and postgresql"
```

A PostgreSQL major must not be advertised as supported if its matrix job is red.

## Next ticket

```text
T21-002 — Python matrix qualification
```

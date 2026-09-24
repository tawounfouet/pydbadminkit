# LOT-21 / T21-003 — Backup → Restore Qualification

## Decision

```text
Ticket: T21-003
Result: PASS
Formats qualified: custom, plain_sql
Execution path: real pg_dump → artifact → real pg_restore/psql → verification
```

## Qualification scenario

The PostgreSQL integration suite performs an actual round trip rather than mocking native
tools.

For custom format:

```text
source PostgreSQL database
        ↓ seed restore_probe(id=42, payload="restored")
pydbadmin backup create --format custom
        ↓
pg_dump
        ↓
custom archive + metadata + checksum
        ↓
pydbadmin backup restore --create
        ↓
pg_restore
        ↓
new target database
        ↓
SELECT restore_probe
        ↓
(42, "restored")
```

For plain SQL:

```text
source database
        ↓
pg_dump --format plain
        ↓
SQL artifact
        ↓
pydbadmin backup restore --create
        ↓
psql
        ↓
new target database
        ↓
data verification
```

## Safety qualification

The integration suite also verifies:

- backup artifacts are non-empty;
- temporary `.partial` files do not remain after success;
- metadata sidecars contain the expected stable fields;
- SHA-256 checksum metadata is produced;
- custom archive validation succeeds through native tooling;
- existing backup collisions fail unless force is explicit;
- restore to an existing target is blocked by default;
- custom `--clean` must be explicit before replacing objects in an existing target;
- backup and restore mutation audit events are emitted.

## Cross-version execution

These tests are part of the PostgreSQL integration marker and therefore execute on every
qualified server/client pair:

```text
PostgreSQL 14
PostgreSQL 15
PostgreSQL 16
PostgreSQL 17
PostgreSQL 18
```

The workflow installs matching native client tools for each server major.

## Release gate

The 1.0 condition:

```text
backup/restore green
```

is satisfied when the PostgreSQL matrix is green with the backup and restore integration
tests enabled.

## Next ticket

```text
T21-004 — runtime concurrency qualification
```

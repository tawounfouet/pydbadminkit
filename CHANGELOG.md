# Changelog

All notable PyDBAdminKit milestones are documented here.

## [0.4.0a1] — Runtime Inspection Foundations

### Runtime domain

- Immutable `SessionInfo`, `QueryInfo` and `TransactionInfo` read models.
- Normalized `SessionState` values for public API consumers.
- Engine-neutral `RuntimePort` and `RuntimeService`.

### PostgreSQL runtime inspection

- `pg_stat_activity` session inspection.
- Currently active query inspection with elapsed time and wait metadata.
- Open transaction inspection with transaction age and XID/XMIN metadata.
- Database and user filtering.
- Optional session-state filtering.
- PyDBAdminKit's own inspection backend excluded by default.

### CLI and machine interface

- `session list`.
- `query list`.
- `transaction list`.
- `--include-self` for explicit self-inspection.
- Runtime objects supported by table, JSON and YAML output.

### Quality

- Runtime domain, service, mapper and PostgreSQL adapter unit tests.
- Human-output tests.
- PostgreSQL CLI integration tests for sessions, active queries and transactions.
- Runtime capabilities promoted from roadmap placeholders to available capabilities.

### Safety boundary

This alpha is intentionally read-only. It does not implement query cancellation or session
termination.

### Next

`0.4.0a2` extends Runtime Administration with waits, locks and blocking chains.

## [0.3.0] — Security Administration

### Foundation

- PostgreSQL-first ports/adapters architecture.
- TOML connection profiles and environment-backed secret resolution.
- Stable public errors, exit codes and capability discovery.
- Ruff, Mypy strict, unit coverage, package smoke tests and PostgreSQL 18 integration gates.

### Object Explorer

- Server and database inspection.
- Schema inspection with system-schema filtering.
- Tables, columns and constraints.
- Views and materialized views.
- Index metadata, definitions and partial predicates.

### Machine interface

- Global `--output table|json|yaml`.
- Domain-independent serialization.
- Clean machine-readable stdout for JSON/YAML automation.

### Security inspection

- PostgreSQL roles and LOGIN roles.
- Role membership graph.
- Direct relation ACL inspection.
- Effective relation access source attribution:
  - direct;
  - inherited;
  - PUBLIC;
  - owner;
  - superuser.
- Ownership inspection for databases, schemas and relations.

### Guarded Security mutations

- Role create / alter / drop.
- Membership add / remove.
- Relation access grant / revoke.
- Risk-aware `OperationPlan`.
- `--dry-run` planning.
- Explicit and typed-target confirmations.
- `--yes` never bypasses typed-target confirmation.
- Fail-closed behavior for read-only profiles and unknown environments.
- PostgreSQL built-in role and active-role protections.
- Secret-safe JSONL audit events with correlation IDs.

### Next

`0.4.x` introduces Runtime Administration: sessions, queries, transactions, waits, locks, blocking chains, cancel and terminate operations.

## [0.1.0a1] — Initial foundation

- Repository bootstrap.
- Initial CLI entrypoint.
- Initial Domain, error, port and application foundations.

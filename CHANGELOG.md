# Changelog

All notable PyDBAdminKit milestones are documented here.

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

# Changelog

All notable PyDBAdminKit milestones are documented here.

## [0.4.0] — Runtime Administration

### Stable Runtime surface

- Stabilized the complete Runtime Administration Python and CLI contracts introduced
  through `0.4.0a1`, `0.4.0a2` and `0.4.0b1`.
- Public read models cover sessions, active queries, transactions, waits, locks and
  recursive blocking relations.
- Public mutation commands cover guarded query cancellation and client-session
  termination.
- Runtime capabilities are reported as available through capability discovery.

### PostgreSQL Runtime inspection

- Session, query and transaction inspection through `pg_stat_activity`.
- Wait inspection through PostgreSQL wait-event metadata.
- Lock inspection through `pg_locks`.
- Recursive blocking-chain inspection through `pg_blocking_pids()`.
- Optional Runtime filters use explicit PostgreSQL parameter casts for stable NULL
  handling on PostgreSQL 18.

### Runtime safety

- Query cancellation requires a visible client backend with an active query.
- Session termination is restricted to visible client backends.
- The PyDBAdminKit execution backend cannot signal itself.
- Read-only profiles and unknown environments fail closed.
- Production risk escalation is preserved.
- Critical termination requires exact typed-target confirmation.
- Dry-run planning, operation correlation IDs and JSONL audit semantics are stable.

### Qualification

- Stable Runtime public exports are covered by explicit contract tests.
- Runtime capability names are covered as part of the stable 0.4.0 contract.
- Unit tests retain the project-wide coverage gate.
- PostgreSQL 18 integration covers sessions, active queries, transactions, waits,
  locks, blocking chains, real query cancellation and real session termination.
- Package build and installed-wheel smoke tests cover the stable version and CLI.

### Next

`0.5.x` begins the Operations line.

## [0.4.0b1] — Guarded Runtime Mutations

### Runtime mutation domain

- Immutable `CancelQueryCommand` and `TerminateSessionCommand`.
- Atomic `BackendSignalResult` returned by engine adapters.
- Dedicated `RuntimeMutationPort` and `RuntimeMutationService`.

### Guarded PostgreSQL signaling

- Query cancellation through `pg_cancel_backend(pid)`.
- Client-session termination through `pg_terminate_backend(pid)`.
- Atomic guards ensure the target exists, is not the PyDBAdminKit execution backend,
  and is a PostgreSQL `client backend` before a signal can be sent.
- PostgreSQL background and auxiliary workers remain protected in this milestone.
- A false PostgreSQL signal result is surfaced as an operation failure rather than success.

### Safety model

- Query cancellation is medium risk outside production and high risk in production.
- Session termination is high risk outside production and critical risk in production.
- Critical termination requires exact typed-target confirmation such as `pid:12345`.
- `--yes` never bypasses typed-target confirmation.
- Read-only profiles and unknown environments fail closed.
- Dry-run returns an `OperationPlan` without signaling or writing audit events.

### Audit and result semantics

- Started, blocked, failed and succeeded lifecycle events reuse the existing JSONL audit sink.
- Runtime operations carry correlation IDs and stable operation identifiers.
- Successful results include target PID, backend type and risk metadata.

### CLI

- `query cancel <pid>`.
- `session terminate <pid>`.
- `--confirm-target` support for critical runtime mutations.
- Human, JSON and YAML mutation plan/result output through the shared output pipeline.

### Quality

- Runtime mutation domain and service unit tests.
- PostgreSQL signal mapper and adapter unit tests.
- CLI mutation tests.
- PostgreSQL integration tests use real sleeping client backends to verify query
  cancellation and session termination end to end.

### Next

Qualify the complete `0.4.x` Runtime Administration line and promote it to stable `0.4.0`.


## [0.4.0a2] — Runtime Waits, Locks and Blocking Chains

### Runtime domain

- Immutable `WaitInfo`, `LockInfo` and `BlockingRelation` read models.
- `RuntimePort` and `RuntimeService` extended without changing the 0.4.0a1 API.
- Recursive blocking relations expose `root_pid`, `blocked_pid`, `blocking_pid`
  and chain `depth`.

### PostgreSQL runtime inspection

- Wait-event inspection from `pg_stat_activity`.
- Backend lock inspection from `pg_locks`.
- Relation, transaction and virtual transaction lock metadata.
- Waiting-only lock filtering.
- Recursive blocking-chain discovery through `pg_blocking_pids()`.
- PostgreSQL PID `0` preserved for prepared-transaction blockers.
- Duplicate blocker PIDs collapsed by recursive `UNION` traversal.
- Cycle-safe recursive traversal using a visited PID path.

### CLI and machine interface

- `wait list`, including optional `--type` filtering.
- `lock list`, including `--waiting-only`.
- `blocking list` for recursive blocker relationships.
- Table, JSON and YAML output for all new runtime models.

### Quality

- Domain, service, mapper, adapter and human-output tests extended for 0.4.0a2.
- PostgreSQL integration tests create a real advisory-lock contention.
- The same contention is verified through waits, waiting locks and blocking relations.
- Runtime wait, lock and blocking capabilities are now reported as available.

### Safety boundary

`0.4.0a2` remains read-only. No backend cancellation or termination operation is exposed.

### Next

The next Runtime Administration milestone introduces guarded query cancellation and session
termination using the existing `OperationPlan`, risk, confirmation and audit model.


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

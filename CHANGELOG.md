# Changelog

## [Unreleased] — 1.0 Hardening

### LOT-20 complete

- Froze public API, CLI, JSON, error-code, exit-code, configuration, capability-name and
  guarded operation-name contracts.
- Completed security, SQL-injection, command-injection and secret-redaction reviews.
- Hardened JSONL audit file permissions to `0600`, including pre-existing files.
- Replaced enum-derived dynamic SQL fragments with explicit PostgreSQL keyword whitelists.
- Hardened native-tool argv construction against option injection and retained
  `shell=False` execution.
- Redacted resolved secrets from native-tool diagnostic errors and machine serialization.
- Reviewed query budgets and added a constant-call monitoring regression contract.
- Expanded PostgreSQL integration CI from PostgreSQL 18 only to PostgreSQL 14–18.
- Hardened package metadata with Python 3.11–3.14 classifiers and canonical project URLs.

### LOT-20 qualification

- Unit: 419 passed, 44 deselected.
- Unit coverage: 86.15% with the required 85% gate.
- PostgreSQL integration: 44 tests passed independently on PostgreSQL 14, 15, 16, 17 and 18.
- Quality: Ruff format/check and Mypy strict green.
- Package: build, Twine validation, clean-wheel install and CLI smoke tests green.

### Open 1.0 policy decision

- The repository has no declared license. LOT-20 deliberately does not invent a legal
  license choice; the owner must choose the license policy before the 1.0 publication gate.

### Next

LOT-21 — Qualification / Documentation.

All notable PyDBAdminKit milestones are documented here.

## [0.6.0] — Monitoring / Observability

### Stable promotion

- Promotes the complete Monitoring / Observability feature line to stable `0.6.0`.
- LOT-17 Monitoring Core, LOT-18 Health Checks and LOT-19 Observability Foundations are
  complete.
- Health aggregation, UNKNOWN semantics, threshold defaults and the machine health-report
  shape are frozen by dedicated release-contract tests.
- The public observability boundary is frozen around `MetricExporterPort`,
  `MetricDescriptor`, `MetricType` and `MonitoringSnapshot`.
- Prometheus and OpenTelemetry runtime adapters remain optional future adapter work.

### Qualification

- Stable contract qualification: 352 unit tests passed.
- PostgreSQL 18 integration qualification: 44 tests passed.
- Unit coverage: 85.66%, above the required 85% gate.
- Ruff format/check, Mypy strict, package build, wheel installation and CLI smoke tests are
  green.
- Qualification evidence is documented in `docs/releases/0.6.0_QUALIFICATION.md`.

### Next

LOT-20 — Hardening prepares the full framework for the `1.0.0` stability contract.

## [0.6.0b1] — Observability Foundations

### Exporter boundary

- Public engine-neutral `MetricExporterPort` exports already-collected metric batches.
- `MetricExportService` validates cardinality policy before crossing the exporter boundary.
- No Prometheus or OpenTelemetry runtime dependency is introduced.
- No permanent HTTP metrics daemon is introduced.

### Metric metadata and naming

- `MetricType` distinguishes `gauge`, `counter` and `state` semantics.
- `MetricDescriptor` captures name, unit, semantic type, description and label names.
- Core descriptors cover the LOT-17 connection and database-size metric families.
- Metric names now enforce lowercase dotted segments.
- Future Prometheus names map deterministically to the `pydbadmin_` namespace.
- PyDBAdminKit self-observability reserves the dotted `pydbadmin.` namespace.

### Cardinality policy

- Default exporter labels are limited to `profile`, `environment`, `database` and
  `status`.
- High-cardinality or sensitive labels such as PID, query text and client address are
  rejected before export.
- Exporter-specific policies may explicitly relax the default boundary later.

### Snapshot composition

- `MonitoringSnapshot` combines one metric batch, one `HealthReport` and an
  execution-window timestamp.
- `MonitoringSnapshotService` composes Monitoring Core and Health Checks without claiming
  atomic database consistency.
- Bootstrap wiring exposes `build_monitoring_snapshot_service()`.

### Design spikes

- Prometheus design spike documents naming, types, cardinality and future adapter ownership.
- OpenTelemetry design spike documents Meter mapping, resource attributes, tracing boundary
  and self-observability naming.
- Both integrations remain optional adapters and are intentionally deferred beyond the
  `0.6.x` Core.

### Qualification

- LOT-19 unit tests cover naming, descriptors, registry metadata, cardinality rejection,
  exporter delegation and snapshot composition.
- Qualification reached 348 unit tests and 44 PostgreSQL integration tests with the
  project coverage gate above 85%.
- Ruff format/check, Mypy strict, package build and PostgreSQL integration are green.

### Next

Qualify the complete Monitoring / Observability line and promote `0.6.0b1` to stable
`0.6.0`. LOT-20 hardening follows the stable `0.6.x` feature line.

## [0.6.0a2] — Health Checks

### Default health suite

- `ConnectivityCheck` verifies that the configured PostgreSQL server responds and exposes
  safe latency/version evidence.
- `ConnectionUsageCheck` evaluates current connection utilization.
- `LongQueryCheck` evaluates active-query duration without exposing SQL text.
- `LongTransactionCheck` evaluates open-transaction duration.
- `IdleTransactionCheck` isolates idle and aborted-idle transactions.
- `WaitingLockCheck` evaluates waiting sessions, blocked sessions and root blockers.
- `HealthCheckRunner` isolates check-specific operational failures and aggregates the
  resulting `HealthReport`.
- Connectivity failure is CRITICAL; non-connectivity operational failures become UNKNOWN.

### Thresholds and evidence

- Connection defaults: warning 80%, critical 95%.
- Long-query defaults: warning 30s, critical 300s.
- Long-transaction defaults: warning 60s, critical 600s.
- Idle-transaction defaults: warning 60s, critical 300s.
- Waiting-lock defaults: warning 1 session, critical 10 sessions.
- Every default threshold is overridable from `pydbadmin health check`.
- Health results expose raw observed values and warning/critical evidence.

### CLI and machine contract

- New vertical slice: `pydbadmin health check`.
- Human, JSON and YAML output use the shared output interface.
- Stable JSON report contains `overall_status`, `checks` and `captured_at`.
- CRITICAL exits non-zero by default.
- `--fail-on-warning` makes WARNING exit non-zero for CI/CD use.
- UNKNOWN remains non-failing by default; a future `--fail-on-unknown` policy is reserved.

### Qualification

- Threshold-boundary tests cover below/equal/between/equal-critical semantics.
- Unit tests cover connectivity, connection usage, queries, transactions, idle transactions,
  locks, aggregation, UNKNOWN isolation and CLI exit policy.
- PostgreSQL 18 integration executes the complete JSON health vertical slice against a real
  database.
- Qualification reached 336 unit tests and 44 PostgreSQL integration tests with 85.67%
  total unit coverage.
- Ruff format/check, Mypy strict, package build and installed-wheel smoke tests are green.

### Next

LOT-19 adds Observability Foundations: exporter port, metric descriptors, cardinality rules,
internal metric naming, monitoring snapshot DTO and Prometheus/OpenTelemetry design spikes.

## [0.6.0a1] — Monitoring Core

### Monitoring domain

- `Metric` for point-in-time observable facts with explicit units, labels and timestamps.
- `HealthStatus`, `HealthCheckResult`, `HealthCheckEvidence` and `HealthReport`.
- Stable health aggregation semantics: CRITICAL > WARNING > OK, with explicit UNKNOWN.
- `Threshold` model for configurable warning/critical boundaries.
- `ConnectionStatistics`, `DatabaseSizeMetric`, `TableSizeMetric`, `TableStatistics`
  and `IndexStatistics`.
- Table and index statistics retain their `QualifiedName` identity.

### Monitoring architecture

- Engine-neutral `MonitoringPort`.
- Read-only `MonitoringService`.
- Initial low-cardinality metric snapshot through `collect_metrics()`.
- PostgreSQL-first `PostgreSQLMonitoringAdapter`.
- Bootstrap wiring through `build_monitoring_service()`.
- Capability discovery for connection statistics, database sizes, table statistics and
  index statistics.

### PostgreSQL sources

- Connection usage from `pg_stat_activity` and `max_connections`.
- Logical database sizes from `pg_database_size()`.
- Table observations from `pg_stat_user_tables` plus `pg_class.reltuples`.
- Index observations from `pg_stat_user_indexes` plus `pg_relation_size()`.
- Cross-database relation filters fail explicitly instead of attempting unsafe inspection.

### Qualification

- Domain validation and aggregation tests cover metrics, thresholds and health semantics.
- Adapter tests cover PostgreSQL row mapping, filters and error handling.
- Application tests cover raw monitoring reads and low-cardinality metric collection.
- PostgreSQL 18 integration creates a real table and index and validates connection, size,
  table-statistics and index-statistics reads.
- Qualification reached 316 unit tests and 43 PostgreSQL integration tests with the
  project coverage gate above 85%.
- Ruff format/check, Mypy strict, package build and installed-wheel smoke tests are green.

### Next

LOT-18 introduces the default health-check engine and the `pydbadmin health check`
vertical slice: connectivity, connection usage, long queries, long transactions,
idle transactions and waiting locks.

## [0.5.0] — Operations

### Stable scope

- Logical PostgreSQL backup in custom and plain-SQL formats.
- Backup validation with SHA-256 checksum and artifact metadata.
- Restore through `pg_restore` and `psql`, with target inspection and post-restore verification.
- VACUUM, ANALYZE and REINDEX maintenance operations.
- Progress inspection for VACUUM and REINDEX.
- Tool compatibility checks, secret-safe process environments, filesystem safety and shared guardrails/audit.

### Qualification

- Local notebook smoke validation on PostgreSQL 17.10 confirmed connection, capability discovery,
  catalog/security surfaces, maintenance progress queries and dry-run planning.
- The local Windows lab correctly reports backup/restore as unavailable when `pg_dump`,
  `pg_restore` and `psql` are absent from PATH; it no longer prints or embeds a demo password.
- PostgreSQL integration CI installs PostgreSQL 18 client tools and qualifies the real Operations
  line, including backup, restore and maintenance suites.
- The qualification run completed with 42 PostgreSQL integration tests passing.
- Quality, unit tests, package build and PostgreSQL integration are green before promotion.

### Roadmap

- LOT-14 — Backup Foundation: complete.
- LOT-15 — Restore: complete.
- LOT-16 — Maintenance: complete.
- Next: LOT-17 — Monitoring Core, then LOT-18 — Health Checks and LOT-19 — Observability Foundations.

## [0.5.0b1] — Maintenance Foundation

### Maintenance domain

- `VacuumCommand`, `AnalyzeCommand`, `ReindexCommand`.
- `MaintenanceOperation`, `MaintenanceOperationType`, `MaintenanceProgress`.
- MVP `ReindexTargetType` scopes: index and table.
- Engine-neutral `MaintenancePort`.
- Dedicated public `MaintenanceError`.

### PostgreSQL maintenance

- Routine `VACUUM`.
- `VACUUM ANALYZE`, `VACUUM FREEZE` and explicit `VACUUM FULL`.
- Database-wide or relation-targeted `ANALYZE`.
- Column-specific `ANALYZE`.
- `REINDEX INDEX` and `REINDEX TABLE`.
- `REINDEX CONCURRENTLY` with an explicit PostgreSQL version guard.
- Relation targets are checked against PostgreSQL catalog relation kinds before mutation.
- Identifiers are composed exclusively through Psycopg SQL identifier objects.
- Cross-database relation targets are rejected.

### Execution semantics and timeouts

- Maintenance uses the PostgreSQL connection factory's autocommit sessions.
- `statement_timeout` and `lock_timeout` are set in the same session as the
  maintenance command through parameterized `set_config()`.
- PostgreSQL timeout cancellations map to the public `OperationTimeoutError`.
- Database errors continue through the shared PostgreSQL error translator.

### Guardrails and audit

- Dry-run performs target preflight and returns the shared `OperationPlan`.
- Routine VACUUM and ANALYZE are medium risk outside production.
- VACUUM FULL and REINDEX are high risk outside production.
- Production escalates medium to high and high to critical.
- Critical maintenance requires exact typed-target confirmation.
- Read-only profiles and unknown environments fail closed.
- Started, blocked, failed and succeeded lifecycle events use the shared JSONL audit sink.

### Progress

- `postgres progress vacuum` reads `pg_stat_progress_vacuum`.
- VACUUM FULL progress is included from `pg_stat_progress_cluster`.
- `postgres progress reindex` reads REINDEX rows from
  `pg_stat_progress_create_index`.
- Percent is emitted only when completed/total counters are meaningful.

### CLI

- `postgres vacuum`.
- `postgres analyze`.
- `postgres reindex`.
- `postgres progress vacuum`.
- `postgres progress reindex`.
- Human, JSON and YAML output continue through the shared machine interface.

### Qualification

- Unit coverage for domain invariants, guardrails, adapter preflight, timeout session
  setup, progress mapping and CLI contracts.
- PostgreSQL 18 integration creates a real table and index, then executes VACUUM,
  ANALYZE, REINDEX INDEX CONCURRENTLY and REINDEX TABLE.
- Successful VACUUM integration also proves the required non-transaction-block
  execution semantics.
- Integration verifies data and index validity after maintenance.

### Next

Qualify the complete `0.5.x` Operations line and promote it to stable `0.5.0`.

## [0.5.0a2] — Restore Foundation

### Restore domain

- `RestoreBackupCommand`, `RestoreValidation` and `RestoreOperation`.
- Engine-neutral `RestorePort` and restore-target database port.
- Dedicated `RestoreError` and `RestoreValidationError` public errors.

### PostgreSQL restore

- Custom archive restore through `pg_restore`.
- Plain SQL restore through `psql` with `ON_ERROR_STOP=1`.
- Explicit target inspection before execution.
- New target creation uses a safely quoted PostgreSQL identifier.
- Existing targets are blocked by default.
- `--clean` is limited to custom archives and maps to
  `pg_restore --clean --if-exists`.
- Parallel `--jobs` is limited to custom archives.
- Restore tools older than the target PostgreSQL major are rejected.
- Backups from a newer PostgreSQL major than the target server are rejected.

### Restore guardrails

- Dry-run produces the shared immutable `OperationPlan`; no simulated restore is
  claimed.
- Non-production restore is high risk and requires explicit approval.
- Production restore is critical and requires exact typed-target confirmation.
- Read-only connection profiles block restore.
- Unknown environments fail closed.
- Restore execution revalidates target/tool state immediately before mutation.
- A partially restored database created by `--create` is retained on failure rather
  than silently deleted.

### Verification and audit

- Successful restore requires connectivity to the target database.
- Basic catalog presence is verified after native-tool completion.
- Started, blocked, failed and succeeded restore events use the shared JSONL audit sink.
- Passwords remain in the child environment only and are never placed in process
  arguments.

### Qualification

- Unit coverage for restore models, adapter, application guardrails and CLI.
- PostgreSQL 18 integration performs real custom and plain backups, restores each into
  a new database, then reads restored table data.
- Integration also proves that an existing target is rejected until custom `--clean`
  is explicitly requested.
- Capability discovery reports `backup.restore` and validates `pg_restore` / `psql`
  availability.

### Next

`0.5.0b1` introduces Maintenance.

## [0.5.0a1] — Backup Foundation

### Backup domain

- `Backup`, `BackupMetadata`, `BackupFormat`, `CreateBackupCommand` and
  `BackupValidation`.
- External-tool and process result models.
- Engine-neutral backup, process, tool-resolution and backup-filesystem ports.

### PostgreSQL logical backup

- Custom-format backup through `pg_dump --format=custom`.
- Plain-SQL backup through `pg_dump --format=plain`.
- PostgreSQL tool-version parsing isolated in the adapter.
- Backup creation rejects a `pg_dump` major version older than the server major.
- Cross-major supported dumps add `--quote-all-identifiers`.
- Directory/tar and parallel jobs remain deferred.

### Backup artifact safety

- Destination validation before process launch.
- No overwrite without explicit `--force`.
- Temporary `.partial` artifacts.
- Atomic finalization of artifact and metadata sidecar.
- Restrictive local file permissions where supported.
- SHA-256 checksums enabled by default.
- Secret-safe `.metadata.json` sidecar generation.
- Failed native-tool runs clean temporary artifacts.

### Native tool execution

- `PathToolResolver` resolves `pg_dump` and `pg_restore` from PATH.
- `SubprocessRunner` always uses argument arrays with `shell=False`.
- Passwords are supplied only through the child `PGPASSWORD` environment.
- Explicit process timeouts map to `OperationTimeoutError`.
- Tool failures use dedicated public tool errors and CLI exit code 8.

### Validation

- Artifact existence/readability/size checks.
- SHA-256 verification against metadata.
- Custom archives are validated with `pg_restore --list`.
- Plain SQL validation explicitly warns that a real restore test is required for
  full logical validation.

### CLI and safety

- `backup create <database>`.
- `backup validate <path>`.
- `--format`, `--output-path`, `--checksum/--no-checksum`, `--timeout`
  and guarded `--force`.
- Backup creation supports the shared global `--dry-run` plan.
- Forced overwrite requires approval and escalates to high risk in production.
- Backup creation lifecycle is written to the shared JSONL audit sink.

### Quality

- Unit coverage for models, tool resolution, process timeout, filesystem finalization,
  PostgreSQL adapter, application service and CLI.
- PostgreSQL integration installs PostgreSQL 18 client utilities and exercises real
  `pg_dump` / `pg_restore` against the PostgreSQL 18 service.

### Next

`0.5.0a2` introduces Restore.

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

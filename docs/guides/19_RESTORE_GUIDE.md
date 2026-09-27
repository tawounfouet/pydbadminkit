# PyDBAdminKit 1.0 — Restore Guide

## Objective

Restore validated PostgreSQL logical backups safely with PyDBAdminKit 1.0.

This guide covers:

```text
backup restore <path> --database <target>
```

and the public Python `RestoreService`.

The restore workflow is deliberately stricter than backup creation because it changes database state and can replace objects in an existing target.

## Prerequisites

Before restoring:

1. ensure the backup artifact and its metadata sidecar are available;
2. validate the backup;
3. select an explicit target database;
4. confirm whether the target already exists;
5. understand whether `--create` or `--clean` is appropriate;
6. ensure the required PostgreSQL native tool is available;
7. use `--dry-run` before execution.

Recommended preflight:

```bash
pydbadmin backup validate /backups/accounting.dump

pydbadmin \
  -c staging \
  --dry-run \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

# Restore mental model

The application workflow is:

```text
backup path
    ↓
load artifact + metadata sidecar
    ↓
backup validation
    ↓
restore-specific preflight
    ↓
OperationPlan
    ↓
policy + confirmation
    ↓
backup validation again
    ↓
audit STARTED
    ↓
optional CREATE DATABASE
    ↓
pg_restore or psql
    ↓
target verification
    ↓
RestoreOperation
```

This means restore planning is not based only on a filename.

PyDBAdminKit first reconstructs and validates the `Backup` object from its artifact and metadata.

# CLI surface

```bash
pydbadmin \
  -c staging \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

Options:

```text
--database <target>    required
--clean
--create
--jobs <n>
--timeout <seconds>
--confirm-target <target>
```

Global mutation controls also apply:

```text
--dry-run
--yes
--non-interactive
```

# RestoreBackupCommand

The public Python model is:

```python
from pydbadminkit.domain.operations import RestoreBackupCommand

command = RestoreBackupCommand(
    backup_path="/backups/accounting.dump",
    target_database="accounting_restore",
    create=True,
)
```

Fields:

```text
backup_path
target_database
clean
create
jobs
timeout_seconds
```

Validation rules:

```text
backup_path       non-blank
target_database   non-blank
clean + create    forbidden together
jobs              > 0 when provided
timeout_seconds   > 0 when provided
```

# --create and --clean are mutually exclusive

This is invalid:

```bash
pydbadmin \
  -c staging \
  backup restore source.dump \
  --database target \
  --create \
  --clean
```

The command model rejects it before restore planning.

The two modes represent different target states:

```text
--create
    → target must not exist

--clean
    → target must already exist
```

# Target-existence policy

PyDBAdminKit checks:

```text
pg_catalog.pg_database
```

to determine whether the target database already exists.

The preflight then fails closed.

## Target exists

If the target exists:

```text
--create
    → invalid

no --clean
    → invalid implicit overwrite
```

For a custom archive, the permitted explicit path is:

```text
existing target + --clean
```

## Target does not exist

If the target does not exist:

```text
without --create
    → invalid

--clean
    → invalid
```

The permitted path is:

```text
absent target + --create
```

# No implicit overwrite

This command is intentionally rejected when `target` already exists:

```bash
pydbadmin \
  -c staging \
  backup restore source.dump \
  --database target
```

The restore validation reports that implicit overwrite is blocked.

You must explicitly choose:

```text
--clean
```

for a supported custom-archive restore into an existing target, or choose another target.

# Supported backup formats

The PostgreSQL restore adapter currently supports:

```text
custom
plain_sql
```

Other `BackupFormat` values are rejected during restore preflight.

# Custom restore

Custom backups use:

```text
pg_restore
```

## New target

```bash
pydbadmin \
  -c staging \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

PyDBAdminKit first creates:

```sql
CREATE DATABASE "accounting_restore"
```

using safe PostgreSQL identifier composition.

Then `pg_restore` connects directly to that target.

## Existing target

For a custom archive, an existing target requires:

```bash
pydbadmin \
  -c staging \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --clean
```

The native restore arguments include:

```text
--clean
--if-exists
```

The plan warns that archive-owned objects will be dropped before recreation.

# Plain SQL restore

Plain SQL backups use:

```text
psql
```

A typical supported workflow is:

```bash
pydbadmin \
  -c staging \
  backup restore /backups/accounting.sql \
  --database accounting_restore \
  --create
```

The native invocation includes:

```text
--no-psqlrc
--set ON_ERROR_STOP=1
--file <backup-path>
```

This prevents user `psqlrc` configuration from silently changing restore behavior and makes SQL errors stop the restore process.

# Plain SQL into an existing target

The current preflight requires an existing target to use `--clean`.

But:

```text
--clean
```

is supported only for custom-format backups.

Therefore, under the current 1.0 implementation, a plain-SQL restore cannot use the existing-target overwrite path.

The supported plain-SQL pattern is:

```text
target absent
    +
--create
```

If you need a different lifecycle, manage the target outside this restore command according to your operational process.

# --clean limitations

`--clean` requires:

```text
target exists
backup format = custom
```

It is rejected for plain SQL.

The effect recorded in the plan is:

```text
Drop archive-owned objects in '<target>' before restore.
```

This is destructive and should be reviewed carefully.

# --create semantics

`--create` requires the target to be absent.

PyDBAdminKit creates the database itself before launching the restore tool.

The plan records:

```text
Create database '<target>'.
```

and warns:

```text
If restore fails after target creation, the partial target database is retained.
```

PyDBAdminKit does not automatically drop a newly created target if the subsequent restore fails.

# Parallel restore jobs

`--jobs` is supported only for custom-format restore.

Example:

```bash
pydbadmin \
  -c staging \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create \
  --jobs 4
```

This maps to:

```text
pg_restore --jobs 4
```

For plain SQL:

```text
--jobs
    → restore validation error
```

# Backup validation before restore

The restore service first loads the backup through the file store.

That requires:

```text
artifact
metadata sidecar
```

It then invokes backup validation.

If the backup is invalid:

```text
BackupValidationError
```

is raised before restore-specific execution.

This protects restore from proceeding with:

- missing/unreadable artifacts;
- size mismatch;
- checksum mismatch;
- invalid custom archive;
- other backup-validation failures.

# Backup validation occurs twice in the service lifecycle

`plan_restore(...)` calls backup validation.

Then `restore(...)` loads and validates the backup again before starting execution.

Conceptually:

```text
plan
    → validate backup

time passes

execute
    → validate backup again
```

This reduces the chance that an artifact modified after planning is blindly restored.

# Restore-specific preflight

After backup validation, PyDBAdminKit evaluates:

```text
backup engine
backup format
target existence
--create / --clean combination
parallel-job compatibility
backup/server major compatibility
native-tool availability
native-tool/server compatibility
```

If restore validation is not valid:

```text
RestoreValidationError
```

is raised by the application service.

# Backup engine compatibility

The PostgreSQL restore adapter accepts only:

```text
DatabaseEngine.POSTGRESQL
```

A backup identified as another engine is rejected.

# Backup/server version rule

If backup metadata contains an engine version, PyDBAdminKit rejects:

```text
backup PostgreSQL major > target server major
```

Example:

```text
backup from PostgreSQL 19
target server PostgreSQL 18
    → invalid restore preflight
```

This check uses the recorded backup engine version.

# Restore-tool/server version rule

The required native tool must not be older than the target PostgreSQL server major.

Implemented rule:

```text
tool major < server major
    → ToolVersionMismatchError
```

Custom restore checks:

```text
pg_restore
```

Plain SQL restore checks:

```text
psql
```

# Native tool selection

Mapping:

```text
custom
    → pg_restore

plain_sql
    → psql
```

If the required executable is unavailable:

```text
ToolNotFoundError
```

If its version is missing/unparseable:

```text
ToolVersionMismatchError
```

# Custom pg_restore arguments

The current custom restore invocation contains:

```text
--host
--port
--username
--dbname
--no-password
--exit-on-error
```

Optional additions:

```text
--clean --if-exists
--jobs <n>
```

Before the backup path, the adapter inserts:

```text
--
```

so a backup filename beginning with option-like characters cannot be interpreted as a `pg_restore` option.

# Plain SQL psql arguments

The current plain-SQL invocation contains:

```text
--host
--port
--username
--dbname
--no-password
--no-psqlrc
--set ON_ERROR_STOP=1
--file <backup-path>
```

The backup path is passed as the value of `--file`, not concatenated into a shell command.

# Secret handling

The restore adapter reuses the PostgreSQL child-process environment model.

Password:

```text
PGPASSWORD
```

SSL/connect settings can use:

```text
PGSSLMODE
PGCONNECT_TIMEOUT
PGSSLROOTCERT
PGSSLCERT
PGSSLKEY
```

The password is not included in argv.

Native-tool stderr is redacted before being surfaced in a public `RestoreError`.

# Risk model

Restore is always a high-risk mutation outside production.

```text
non-production
    → high
    → explicit confirmation
```

Production restore is:

```text
critical
    → type_target
```

There is no low- or medium-risk restore path in the current service.

# Restore target for confirmation

The operation-plan target is:

```text
target_database
```

Example:

```text
accounting_restore
```

In production, typed-target confirmation must match exactly.

# Non-production execution

Dry-run:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

After review, explicit approval can be supplied with:

```bash
pydbadmin \
  -c staging \
  --yes \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

# Production execution

Dry-run:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

Execution:

```bash
pydbadmin \
  -c prod \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create \
  --confirm-target accounting_restore
```

`--yes` does not bypass critical typed-target confirmation.

# Production warning

Every production restore plan includes:

```text
Production restore requires exact typed-target confirmation.
```

# Read-only profile policy

Restore execution is blocked when:

```text
profile.read_only = true
```

with:

```text
PolicyDeniedError
```

Unlike backup creation, restore changes database state and therefore cannot execute through a read-only profile.

# Unknown environment policy

Restore execution is also blocked when:

```text
environment = unknown
```

This fails closed.

Note that planning performs validation and can produce a plan before execution policy is enforced; the actual restore remains blocked until the environment is classified.

# Dry-run semantics

Dry-run returns:

```text
OperationPlan
```

and does not execute restore.

The plan contains:

```text
operation
target
environment
risk
confirmation
effects
warnings
correlation_id
```

Operation:

```text
backup.restore
```

# Plan effects

Depending on mode, the effects may include:

```text
Drop archive-owned objects in '<target>' before restore.
Create database '<target>'.
Restore '<backup-path>' into database '<target>'.
```

This makes destructive/create behavior visible before execution.

# Plan warnings

Warnings can include:

```text
restore-validation warnings
target database already exists
partial created target retained after failure
production typed-target requirement
```

# Python API

Build the public restore service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_restore_service

service = build_restore_service(
    "staging",
    Path("config.toml"),
)
```

Create command:

```python
from pydbadminkit.domain.operations import RestoreBackupCommand

command = RestoreBackupCommand(
    backup_path="/backups/accounting.dump",
    target_database="accounting_restore",
    create=True,
)
```

Plan:

```python
plan = service.plan_restore(command)

print(plan.target)
print(plan.risk)
print(plan.confirmation)
print(plan.effects)
print(plan.warnings)
```

# Python dry-run

```python
from pydbadminkit.domain.safety import MutationOptions

outcome = service.restore(
    command,
    MutationOptions(dry_run=True),
    plan=plan,
)
```

# Python execution outside production

For a high-risk explicit-confirmation plan:

```python
result = service.restore(
    command,
    MutationOptions(approved=True),
    plan=plan,
)
```

# Python production execution

For a critical plan:

```python
result = service.restore(
    command,
    MutationOptions(
        confirmed_target=plan.target,
    ),
    plan=plan,
)
```

Application services do not prompt.

The caller supplies confirmation evidence.

# Restore execution failure

After validation and approval, the adapter:

1. optionally creates the target;
2. launches `pg_restore` or `psql`;
3. checks process return code;
4. verifies the resulting target.

A non-zero tool return code raises:

```text
RestoreError
```

with redacted stderr context.

# New target retained after failure

When `--create` is used, PyDBAdminKit creates the target before running the native restore tool.

If the native restore subsequently fails, the database is not automatically removed.

That behavior is deliberately warned in the operation plan.

Operational cleanup remains explicit rather than automatic.

# Post-restore verification

A zero native-tool exit code is not enough.

PyDBAdminKit performs a target verification step.

It opens a connection to the target database and checks:

```text
current_database() == target
public schema exists
```

If verification fails:

```text
RestoreValidationError
```

is raised.

# RestoreOperation

Successful execution returns:

```text
RestoreOperation
```

Fields:

```text
backup
target_database
started_at
finished_at
status
duration_ms
verification_passed
tool
tool_version
```

Constraints include:

```text
target_database non-blank
duration_ms >= 0
tool non-blank
```

# Human output

Successful restore human output contains:

```text
Backup
Target
Status
Duration
Verification
Tool
Tool version
```

# JSON/YAML output

Use:

```bash
pydbadmin \
  -c staging \
  --output json \
  --yes \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

Dry-run emits an `OperationPlan`.

Execution emits a `RestoreOperation`.

Automation must not assume those payloads have the same fields.

# Audit lifecycle

Restore execution uses the standard audited mutation lifecycle.

Policy/confirmation failure:

```text
BLOCKED
```

Before native restore execution:

```text
STARTED
RUNNING
```

Restore failure:

```text
FAILED
```

Successful verified restore:

```text
SUCCEEDED
```

Audit records preserve the operation-plan correlation ID.

# Error model

Important public restore-related errors include:

```text
BackupValidationError
RestoreValidationError
RestoreError
ToolNotFoundError
ToolVersionMismatchError
CapabilityNotAvailableError
PolicyDeniedError
ConfirmationRequiredError
ResourceNotFoundError
OperationTimeoutError
```

Related filesystem/backup errors may also occur while loading the artifact and metadata.

# CLI exit categories

Important frozen mappings include:

```text
0  success
2  CLI/argument/configuration failure
5  resource not found
6  capability unavailable
7  safety/policy failure
8  external tool / backup / restore failure
9  timeout
```

Authentication/authorization failures map to:

```text
4
```

Use exit codes or public error codes, not human-message parsing.

# Worked scenario: restore custom backup to a new staging database

Validate artifact:

```bash
pydbadmin backup validate /backups/accounting.dump
```

Plan:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

Execute:

```bash
pydbadmin \
  -c staging \
  --yes \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --create
```

The resulting `RestoreOperation` reports whether verification passed.

# Worked scenario: refresh an existing custom target

Plan:

```bash
pydbadmin \
  -c staging \
  --dry-run \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --clean
```

Review the destructive effect:

```text
Drop archive-owned objects in 'accounting_restore' before restore.
```

Execute only after explicit approval:

```bash
pydbadmin \
  -c staging \
  --yes \
  backup restore /backups/accounting.dump \
  --database accounting_restore \
  --clean
```

# Worked scenario: production restore

Plan:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  backup restore /backups/accounting.dump \
  --database accounting_recovery \
  --create
```

Then execute with exact target proof:

```bash
pydbadmin \
  -c prod \
  backup restore /backups/accounting.dump \
  --database accounting_recovery \
  --create \
  --confirm-target accounting_recovery
```

# Worked scenario: plain SQL

Validate:

```bash
pydbadmin backup validate /backups/accounting.sql
```

Restore to an absent target:

```bash
pydbadmin \
  -c staging \
  --yes \
  backup restore /backups/accounting.sql \
  --database accounting_sql_restore \
  --create
```

The adapter uses:

```text
psql
```

rather than `pg_restore`.

# Troubleshooting

## target does not exist

Use:

```text
--create
```

if creating a new restore target is intended.

## target already exists

For a custom archive, explicitly use:

```text
--clean
```

if destructive archive-owned object replacement is intended.

Otherwise choose a different target.

## --create says target already exists

Expected.

`--create` requires an absent target.

## --clean says target does not exist

Expected.

`--clean` requires an existing target.

## --clean rejected for plain_sql

Expected.

Current clean restore support is custom-only.

## plain_sql cannot restore into existing target

Under the current preflight, existing targets require `--clean`, and `--clean` is custom-only.

Use an absent target with `--create`.

## --jobs rejected

Parallel jobs require custom format.

## backup validation fails before restore planning

Investigate the backup artifact, metadata, checksum or custom archive before attempting restore.

## backup is from a newer PostgreSQL major than target

The restore is rejected by preflight.

Use a compatible target environment.

## pg_restore / psql older than target server

PyDBAdminKit rejects the native tool.

Use a client-tool major at least as new as the target server major.

## restore tool succeeds but PyDBAdminKit reports verification failure

The post-restore connection/database verification failed.

Treat the restore as unverified and investigate before relying on it.

## created target remains after failure

Expected.

PyDBAdminKit does not automatically drop a partially restored database created via `--create`.

## read-only profile blocks restore

Expected.

Use a deliberately mutation-capable profile if operational policy permits.

## unknown environment blocks restore

Expected.

Classify the connection environment before execution.

# Production considerations

For production restores:

1. validate the backup separately first;
2. confirm source backup engine/version metadata;
3. use a dedicated mutation-capable profile;
4. never rely on implicit overwrite;
5. inspect the target before `--clean`;
6. dry-run and archive the plan;
7. use exact typed-target confirmation;
8. understand that `--create` can leave a partial database after failure;
9. preserve audit correlation IDs;
10. verify application/schema/data semantics beyond PyDBAdminKit's minimal connectivity/public-schema verification;
11. perform restore rehearsals before incidents;
12. treat restore as high-impact even when the target is non-production.

# Best practices

Prefer:

```text
validate → plan → approve → restore → verify
new isolated target for rehearsals
custom format for clean/parallel restore workflows
explicit --create or --clean
compatible native tools
typed confirmation in production
post-restore application/data verification
```

Avoid:

```text
implicit overwrite
restore without prior backup validation
--clean without understanding object impact
assuming tool exit 0 proves full recovery
assuming PyDBAdminKit verification proves application correctness
plain-SQL overwrite of an existing target
bypassing RestoreService
ignoring a partial target after failed --create
```

## Key takeaways

- Restore always performs backup validation before restore preflight.
- The backup is validated again before execution.
- Restore supports custom and plain-SQL backups.
- Custom uses `pg_restore`; plain SQL uses `psql`.
- There is no implicit overwrite path.
- An absent target requires `--create`.
- An existing supported target requires `--clean`.
- `--clean` is custom-only.
- Therefore plain-SQL restore currently targets an absent database with `--create`.
- `--jobs` is custom-only.
- A backup from a newer PostgreSQL major than the target server is rejected.
- A restore tool older than the target server major is rejected.
- Non-production restore is always high-risk.
- Production restore is critical and requires exact target confirmation.
- Read-only and unknown-environment profiles block execution.
- A newly created target is retained if restore later fails.
- Native-tool success is followed by target verification.
- Guide 20 continues with maintenance operations.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Backup](18_BACKUP_GUIDE.md)
- [Maintenance](20_MAINTENANCE_GUIDE.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Audit and Operation Traceability](25_AUDIT_AND_OPERATION_TRACEABILITY.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [PostgreSQL Version Compatibility](30_POSTGRESQL_VERSION_COMPATIBILITY.md)
- [Production Usage and Safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Maintenance](20_MAINTENANCE_GUIDE.md).

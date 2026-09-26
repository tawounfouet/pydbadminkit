# PyDBAdminKit 1.0 — Backup Guide

## Objective

Create and validate PostgreSQL logical backups safely with PyDBAdminKit 1.0.

This guide covers:

```text
backup create
backup validate
```

and their public Python API equivalents.

Restore is covered separately in guide 19.

## Prerequisites

Backup creation requires:

- a valid connection profile;
- PostgreSQL connectivity;
- the native `pg_dump` utility available on PATH or otherwise resolvable;
- a writable destination directory;
- sufficient PostgreSQL privileges to dump the target database.

Custom-archive validation additionally requires:

```text
pg_restore
```

Validation itself does not require a database connection profile.

## Mental model

PyDBAdminKit backup creation is a logical-backup workflow:

```text
connection profile
    ↓
server/tool compatibility check
    ↓
pg_dump
    ↓
temporary artifact
    ↓
artifact validation
    ↓
optional SHA-256
    ↓
metadata sidecar
    ↓
atomic finalization
    ↓
Backup
```

This is not a filesystem-level PostgreSQL physical backup mechanism.

# CLI surface

## Create

```bash
pydbadmin \
  -c prod \
  backup create accounting
```

Options:

```text
--format <format>
--output-path <path>
--compress
--checksum / --no-checksum
--jobs <n>
--timeout <seconds>
--force
```

Default format:

```text
custom
```

## Validate

```bash
pydbadmin backup validate accounting.dump
```

Optional timeout:

```bash
pydbadmin \
  backup validate accounting.dump \
  --timeout 60
```

No connection profile is required for validation.

# Backup formats

The public `BackupFormat` enum contains:

```text
custom
plain_sql
directory
tar
```

However, the current PostgreSQL 1.0 creation implementation supports only:

```text
custom
plain_sql
```

Requests for:

```text
directory
tar
```

are rejected with `CapabilityNotAvailableError`.

This distinction is important:

```text
public enum
    ≠
all formats implemented by current PostgreSQL adapter
```

# Default output paths

When `--output-path` is omitted, the CLI derives the filename from the database and format.

For custom:

```text
<database>.dump
```

Example:

```text
accounting.dump
```

For plain SQL:

```text
<database>.sql
```

For other enum values, the CLI would derive:

```text
<database>.backup
```

but those formats are currently rejected by the PostgreSQL creation adapter.

# CreateBackupCommand

The public Python command model is:

```python
from pydbadminkit.domain.operations import (
    BackupFormat,
    CreateBackupCommand,
)

command = CreateBackupCommand(
    database="accounting",
    format=BackupFormat.CUSTOM,
    output_path="/backups/accounting.dump",
)
```

Fields:

```text
database
format
output_path
compress
checksum
jobs
timeout_seconds
force
```

Validation rules:

```text
database        non-blank
output_path     non-blank
jobs            > 0 when provided
timeout_seconds > 0 when provided
```

# Custom backup

Example:

```bash
pydbadmin \
  -c prod \
  backup create accounting \
  --format custom \
  --output-path /backups/accounting.dump
```

This maps to PostgreSQL `pg_dump` custom format.

Conceptually:

```text
pg_dump --format=custom ...
```

## Explicit compression

For custom backups:

```bash
pydbadmin \
  -c prod \
  backup create accounting \
  --format custom \
  --compress
```

The current adapter maps explicit compression to:

```text
--compress=6
```

If compression is explicitly represented as false at the Python command level, the adapter maps it to:

```text
--compress=0
```

At the CLI level, absence of `--compress` leaves explicit compression unset.

# Plain SQL backup

Example:

```bash
pydbadmin \
  -c prod \
  backup create accounting \
  --format plain_sql \
  --output-path /backups/accounting.sql
```

This maps to:

```text
pg_dump --format=plain
```

Explicit plain-SQL compression is not implemented by the current adapter.

Therefore:

```text
plain_sql + explicit compression
    → CapabilityNotAvailableError
```

# Parallel jobs

The command model and CLI expose:

```text
--jobs
```

but parallel backup jobs are currently not implemented.

The adapter rejects any non-null `jobs` value with:

```text
CapabilityNotAvailableError
```

because PostgreSQL parallel dump requires directory-format handling, which is deferred.

# Native PostgreSQL tool

Backup creation requires:

```text
pg_dump
```

PyDBAdminKit resolves the executable and its version before execution.

If unavailable:

```text
ToolNotFoundError
```

If version output cannot be parsed:

```text
ToolVersionMismatchError
```

# Tool/server version compatibility

PyDBAdminKit retrieves both:

```text
pg_dump version
PostgreSQL server version
```

The implemented compatibility rule is:

```text
pg_dump major < server major
    → reject
```

Therefore an older `pg_dump` major is not allowed to dump a newer server major.

A same-major tool is accepted.

A newer-major tool is also accepted by this implementation.

When the tool major differs from the server major, PyDBAdminKit adds:

```text
--quote-all-identifiers
```

to the `pg_dump` command.

# Connection parameters passed to pg_dump

The native command includes:

```text
--host
--port
--username
--no-password
--dbname
```

The output is first written to a temporary path.

PyDBAdminKit does not place the password in command-line arguments.

# Secret handling

If a password exists, PyDBAdminKit passes it to the child process through:

```text
PGPASSWORD
```

Other PostgreSQL child-process environment values include:

```text
PGSSLMODE
PGCONNECT_TIMEOUT
PGSSLROOTCERT
PGSSLCERT
PGSSLKEY
```

when configured.

Sensitive stderr is redacted before inclusion in public tool-execution errors.

# Destination safety

Before starting `pg_dump`, PyDBAdminKit validates the destination.

The parent directory must:

```text
exist
be a directory
be writable
```

The final output path must not itself be a directory.

Unsafe destinations raise:

```text
UnsafePathError
```

# Collision protection

Without:

```text
--force
```

PyDBAdminKit refuses to overwrite an existing artifact.

It also refuses collisions with:

```text
metadata sidecar
temporary artifact
temporary metadata
```

These conditions raise:

```text
FileCollisionError
```

# Temporary files

The backup is first produced as:

```text
<final-path>.partial
```

Metadata is staged as:

```text
<final-path>.metadata.json.partial
```

If an exception occurs during backup creation, temporary files are cleaned up.

This prevents a failed `pg_dump` from being mistaken for a completed backup.

# Artifact permissions

Before finalization, PyDBAdminKit attempts to restrict the backup artifact permissions to:

```text
0600
```

Failure to restrict permissions raises:

```text
UnsafePathError
```

The metadata sidecar is also created with mode:

```text
0600
```

# Artifact verification before finalization

A successful `pg_dump` process is not enough.

PyDBAdminKit verifies that the temporary artifact:

```text
exists
is readable
has a known size
has size > 0
```

If not:

```text
ToolExecutionError
```

is raised.

# SHA-256 checksum

Checksums are enabled by default.

CLI:

```text
--checksum
```

Default:

```text
true
```

Disable with:

```bash
pydbadmin \
  -c prod \
  backup create accounting \
  --no-checksum
```

When enabled, PyDBAdminKit computes:

```text
SHA-256
```

over the artifact and stores the result in metadata.

# Metadata sidecar

Every completed backup receives a JSON sidecar:

```text
<artifact>.metadata.json
```

Example:

```text
accounting.dump
accounting.dump.metadata.json
```

The sidecar contains secret-safe metadata:

```text
backup_id
database
format
created_at
engine
engine_version
tool_version
size_bytes
checksum_algorithm
checksum
```

No database password is stored there.

# Backup ID

Backup IDs are generated using:

```text
backup_<timestamp>_<database>_<random-suffix>
```

Database-name characters unsafe for the identifier are normalized.

Example shape:

```text
backup_20260926_184500_accounting_a1b2c3d4
```

# Atomic finalization

Without force, PyDBAdminKit uses atomic filesystem linking to publish:

```text
artifact
metadata
```

and detects if the destination changed during execution.

With `--force`, replacement uses a rollback-aware replacement sequence.

If replacement fails, the implementation attempts to restore the prior artifact and metadata.

# Risk model

Normal backup creation is:

```text
low
```

because it creates a new artifact without replacing an existing one.

Confirmation:

```text
low → none
```

## Force overwrite

With:

```text
--force
```

risk becomes:

```text
non-production → medium
production     → high
```

Confirmation:

```text
medium → simple
high   → explicit
```

Unlike critical operations, forced backup overwrite does not use typed-target confirmation in the current implementation.

# Production warning

Any production backup plan includes:

```text
Backup output may contain production-sensitive data and must be protected.
```

A forced backup additionally includes:

```text
Existing backup artifact and metadata may be replaced.
```

# Unknown environment policy

Normal non-force backup creation is not blocked merely because the environment is unknown.

However:

```text
force = true
environment = unknown
```

is blocked with:

```text
PolicyDeniedError
```

This protects destructive overwrite when environment classification is missing.

# Read-only profiles

Backup creation is logically read-only from the database perspective.

The current `BackupService` does **not** block backup creation because a profile has:

```text
read_only = true
```

This differs from mutation services that alter database state.

Filesystem writes still occur at the backup destination.

# Dry-run

Use:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  backup create accounting \
  --output-path /backups/accounting.dump
```

Dry-run returns an `OperationPlan` and does not execute `pg_dump`.

The plan includes:

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

The target is:

```text
output_path
```

# Python backup creation

Build the service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_backup_service
from pydbadminkit.domain.operations import BackupFormat, CreateBackupCommand
from pydbadminkit.domain.safety import MutationOptions

service = build_backup_service(
    "prod",
    Path("config.toml"),
)

command = CreateBackupCommand(
    database="accounting",
    format=BackupFormat.CUSTOM,
    output_path="/backups/accounting.dump",
)

plan = service.plan_create_backup(command)
```

Dry-run:

```python
outcome = service.create_backup(
    command,
    MutationOptions(dry_run=True),
    plan=plan,
)
```

Execution for a normal low-risk backup:

```python
backup = service.create_backup(
    command,
    MutationOptions(),
    plan=plan,
)
```

A forced overwrite requiring approval can use:

```python
backup = service.create_backup(
    command,
    MutationOptions(approved=True),
    plan=plan,
)
```

# Backup model

Successful creation returns:

```text
Backup
```

Fields:

```text
id
database
format
path
created_at
size_bytes
checksum
engine
engine_version
tool_version
status
```

The status is:

```text
succeeded
```

for a successfully created backup.

# Human backup output

Human output contains:

```text
Backup ID
Database
Format
Path
Status
Created at
Size
Checksum
Engine
Engine version
Tool version
```

# JSON backup output

Use:

```bash
pydbadmin \
  -c prod \
  --output json \
  backup create accounting \
  --output-path /backups/accounting.dump
```

The resulting `Backup` is serialized deterministically using the standard machine-output contract.

For automation, prefer JSON rather than parsing human labels.

# Backup validation

Validation is a separate read-only workflow.

CLI:

```bash
pydbadmin backup validate /backups/accounting.dump
```

Python:

```python
from pydbadminkit.bootstrap import build_backup_validation_service

validator = build_backup_validation_service()

result = validator.validate_backup(
    "/backups/accounting.dump",
)
```

No database profile is required.

# Validation loading

Validation first loads:

```text
artifact
metadata sidecar
```

If the artifact is absent:

```text
ResourceNotFoundError
```

If the metadata sidecar is absent or invalid:

```text
BackupValidationError
```

# Artifact-level validation

Validation checks:

```text
artifact exists
artifact readable
artifact non-empty
actual size matches metadata
checksum matches metadata when checksum exists
```

Failures are returned through the `BackupValidation` result where applicable.

# Custom logical validation

For:

```text
format = custom
```

validation additionally uses:

```text
pg_restore --list -- <backup-path>
```

The validation level becomes:

```text
logical
```

If `pg_restore` cannot list the archive, validation returns an error.

# Plain SQL validation

For:

```text
format = plain_sql
```

validation is limited to:

```text
artifact
size
checksum
```

The result includes a warning:

```text
Plain SQL validation is limited to artifact and checksum checks;
full logical validity requires a restore test.
```

This is an important limitation.

A successful plain-SQL validation does not prove that a future restore will succeed.

# BackupValidation model

Fields:

```text
valid
level
warnings
errors
```

Human output displays:

```text
Valid
Level

WARNINGS
ERRORS
```

when those collections are populated.

# Validation timeout

Custom validation can pass a timeout to the native `pg_restore --list` process.

CLI:

```bash
pydbadmin \
  backup validate accounting.dump \
  --timeout 30
```

Python:

```python
result = validator.validate_backup(
    "accounting.dump",
    timeout_seconds=30,
)
```

# Native process safety

The backup implementation uses an argument list for external tools rather than composing a shell command string.

The PostgreSQL backup path is designed around:

```text
explicit executable
explicit argument list
child-process environment
bounded timeout
secret redaction
```

Consumers should use the public services rather than invoking internal process infrastructure directly.

# Audit lifecycle

Backup creation is audited.

Possible events include:

```text
BLOCKED
STARTED
FAILED
SUCCEEDED
```

Policy/approval failure:

```text
BLOCKED
```

Native-tool or backup execution failure after start:

```text
FAILED
```

Successful finalization:

```text
SUCCEEDED
```

The audit event includes the plan correlation ID.

Backup validation itself is not a mutating backup-create operation and does not use this create-operation audit lifecycle.

# Error model

Relevant public errors include:

```text
BackupError
BackupValidationError
FileCollisionError
UnsafePathError
ToolNotFoundError
ToolVersionMismatchError
ToolExecutionError
CapabilityNotAvailableError
PolicyDeniedError
ConfirmationRequiredError
ResourceNotFoundError
OperationTimeoutError
```

# CLI exit codes

Important frozen mappings include:

```text
0  success
2  CLI/configuration/argument error
5  resource not found
6  capability unavailable
7  safety/guardrail failure
8  external tool / backup failure
9  timeout
```

Authentication/authorization failures use:

```text
4
```

Do not parse human messages for automation.

# Worked scenario: safe production backup

Plan:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  backup create accounting \
  --format custom \
  --output-path /srv/backups/accounting.dump
```

Execute:

```bash
pydbadmin \
  -c prod \
  backup create accounting \
  --format custom \
  --output-path /srv/backups/accounting.dump
```

Validate:

```bash
pydbadmin \
  backup validate /srv/backups/accounting.dump
```

Expected filesystem pair:

```text
/srv/backups/accounting.dump
/srv/backups/accounting.dump.metadata.json
```

# Worked scenario: forced replacement

Dry-run:

```bash
pydbadmin \
  -c prod \
  --dry-run \
  backup create accounting \
  --output-path /srv/backups/accounting.dump \
  --force
```

Because this is production + force:

```text
risk = high
confirmation = explicit
```

Execute after review:

```bash
pydbadmin \
  -c prod \
  --yes \
  backup create accounting \
  --output-path /srv/backups/accounting.dump \
  --force
```

# Worked scenario: no overwrite

If:

```text
/srv/backups/accounting.dump
```

already exists and `--force` is absent:

```text
FileCollisionError
```

is expected.

PyDBAdminKit does not silently overwrite the artifact.

# Worked scenario: validate plain SQL

Create:

```bash
pydbadmin \
  -c staging \
  backup create accounting \
  --format plain_sql \
  --output-path ./accounting.sql
```

Validate:

```bash
pydbadmin backup validate ./accounting.sql
```

A valid result can still contain the warning that full logical validity requires a restore test.

# Troubleshooting

## pg_dump not found

Install a compatible PostgreSQL client toolchain or make `pg_dump` discoverable.

Then re-run capability/backup checks.

## pg_dump is older than the server

PyDBAdminKit rejects the backup.

Use a `pg_dump` major that is at least as new as the PostgreSQL server major.

## directory or tar is rejected

Expected in the current implementation.

Use:

```text
custom
plain_sql
```

## --jobs is rejected

Expected.

Parallel backup jobs are currently deferred.

## plain_sql + --compress is rejected

Expected.

Explicit plain-SQL compression is currently deferred.

## destination parent does not exist

Create/select an existing writable parent directory.

PyDBAdminKit does not create the backup directory automatically.

## destination already exists

Use a different path or deliberately use `--force` after reviewing the overwrite plan.

## .partial file already exists

PyDBAdminKit treats stale temporary files as a collision rather than silently reusing them.

Investigate and remove stale files only when operationally safe.

## metadata sidecar missing

Validation cannot reconstruct a PyDBAdminKit `Backup` record without the sidecar.

The result is a backup-validation failure.

## checksum mismatch

Treat the artifact as invalid until investigated.

Do not restore it merely because the file is readable.

## custom validation requires pg_restore

Expected.

Custom archive logical validation uses `pg_restore --list`.

## plain SQL validates with warning

Expected.

Artifact/checksum validation is weaker than a restore test.

# Production considerations

For production backup operations:

1. store backups outside application-working directories;
2. protect backup artifacts as sensitive production data;
3. keep checksums enabled unless there is a deliberate reason not to;
4. validate after creation;
5. use explicit destination paths;
6. avoid `--force` in routine automation;
7. retain metadata sidecars with their artifacts;
8. use a compatible native PostgreSQL client toolchain;
9. preserve audit correlation IDs;
10. periodically perform actual restore tests, especially for plain SQL backups;
11. monitor storage capacity and retention separately;
12. remember logical backup success does not itself prove disaster-recovery readiness.

# Best practices

Prefer:

```text
custom format for archive-oriented workflows
explicit output paths
checksums
post-create validation
dedicated backup directories
no overwrite by default
compatible pg_dump
restore testing
JSON for automation
```

Avoid:

```text
routine --force
committing backup artifacts
storing passwords in commands
discarding metadata sidecars
assuming plain-SQL validation proves restoreability
assuming all BackupFormat values are implemented
parsing human output in scripts
bypassing BackupService
```

## Key takeaways

- PyDBAdminKit creates logical PostgreSQL backups with `pg_dump`.
- The current implementation supports `custom` and `plain_sql`.
- `directory`, `tar` and parallel jobs are not currently implemented.
- Passwords are passed via PostgreSQL child-process environment, not command arguments.
- Older-major `pg_dump` cannot back up a newer PostgreSQL server major.
- Backups are staged to temporary files and atomically finalized.
- Backup artifacts and metadata are restricted to mode 0600 where supported.
- SHA-256 checksum generation is enabled by default.
- Every backup has a JSON metadata sidecar.
- Existing artifacts are protected from overwrite unless `--force` is explicit.
- Normal backup creation is low-risk.
- Forced overwrite raises risk to medium, or high in production.
- Validation does not require a database profile.
- Custom validation uses `pg_restore --list`.
- Plain SQL validation is artifact/checksum level and does not replace a restore test.
- Guide 19 continues with restore operations.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md)
- [Runtime Administration](14_RUNTIME_ADMINISTRATION.md)
- [Restore](19_RESTORE_GUIDE.md)
- [Maintenance](20_MAINTENANCE_GUIDE.md)
- [Dry-run, Guardrails and Confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Audit and Operation Traceability](25_AUDIT_AND_OPERATION_TRACEABILITY.md)
- [Error Handling and Exit Codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Production Usage and Safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Restore](19_RESTORE_GUIDE.md).

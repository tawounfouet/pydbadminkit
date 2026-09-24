# LOT-20 / T20-011 — Command Injection Review

## Status

```text
Ticket: T20-011
Lot: LOT-20 — Hardening
Baseline reviewed: 0.6.0
Result: PASS after argument-injection hardening
```

## Execution boundary

Native PostgreSQL utilities are executed through `SubprocessRunner`.

The runner uses:

```text
argument arrays
shell=False
no command-string concatenation
```

This prevents shell metacharacters in user-controlled values from being interpreted by a
shell.

## Review scope

The native-tool path includes:

- `pg_dump`;
- `pg_restore`;
- `psql`;
- tool `--version` discovery.

The review distinguishes **shell injection** from **option/argument injection**. Avoiding a
shell is necessary but does not by itself prevent a value beginning with `-` from being
reinterpreted as an option by a native utility.

## Finding CMD-20-011-01 — pg_dump database positional argument

### Before review

The backup database name was appended as the final positional argument to `pg_dump`.

A database name beginning with `-` could therefore enter the tool's option parser.

### Remediation

The database is now passed as the required value of:

```text
--dbname <database>
```

The value remains a distinct argv element and cannot become a new top-level option.

### Status

```text
CLOSED
```

## Finding CMD-20-011-02 — pg_restore archive positional argument

### Before review

Custom restore and custom-backup validation passed the archive path positionally without
an explicit end-of-options marker.

### Remediation

Both paths now use:

```text
-- <archive-path>
```

before the positional archive filename.

A path beginning with `--help`, `--dbname` or shell metacharacters therefore remains
archive data rather than a PostgreSQL utility option.

### Status

```text
CLOSED
```

## psql plain restore

Plain SQL restore already passes the backup path as the argument to `--file`, so it does
not use a free positional path.

## Credentials

Database passwords are not included in argv. PostgreSQL native utilities receive the
resolved password through the child environment as `PGPASSWORD`.

This keeps secrets out of process argument listings. Secret-output handling is reviewed
separately by T20-012.

## Tool resolution

The production adapters request fixed tool names (`pg_dump`, `pg_restore`, `psql`).
`PathToolResolver` resolves the executable through `shutil.which` and invokes the
resolved path as argv[0], again without a shell.

## Regression coverage

The hardening suite verifies:

- shell metacharacters remain literal child-process arguments;
- hostile-looking database names remain the value of `--dbname`;
- hostile-looking custom archive paths follow `--`;
- passwords remain absent from argv.

## Frozen rule

```text
Never build a shell command string.
Use argv arrays with shell=False.
Bind option values to explicit options.
Terminate options before user-controlled positional arguments.
Never place database passwords in argv.
```

## Next ticket

```text
T20-012 — redaction review
```

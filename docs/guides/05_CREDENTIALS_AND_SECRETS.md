# PyDBAdminKit 1.0 — Credentials and Secrets

## Objective

Keep resolved PostgreSQL credentials outside persistent PyDBAdminKit connection configuration and
preserve the framework's redaction boundary in CLI, Python, audit and native-tool workflows.

## Reference, not password

The connection profile stores:

```toml
[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"
```

The resolved value is supplied at execution time.

```text
configuration
    ↓
SecretReference
    ↓
runtime resolution
    ↓
SecretValue
    ↓
PostgreSQL execution boundary
```

## Environment-backed resolution

Linux/macOS:

```bash
export PYDBADMIN_LOCAL_PASSWORD="..."
```

PowerShell:

```powershell
$env:PYDBADMIN_LOCAL_PASSWORD = "..."
```

Then:

```bash
pydbadmin --connection local connection test
```

## Public Python model

The stable connection domain includes:

```text
SecretReference
SecretValue
ResolvedConnectionConfig
```

Persist `SecretReference`; treat `SecretValue` as execution-boundary material.

The 1.0 machine serializer represents `SecretValue` as:

```text
<redacted>
```

rather than exposing the underlying secret.

## Backup and restore boundary

Logical operations invoke PostgreSQL native utilities:

```text
pg_dump
pg_restore
psql
```

Passwords are supplied through the child process environment, not process arguments. Native tool
execution uses argument arrays with `shell=False`.

This matters because command arguments are frequently visible to process inspection and logs.

## What not to persist

Do not invent a configuration field containing a resolved password:

```toml
# BAD — resolved credential material does not belong here.
password = "real-password"
```

Do not commit shell scripts, notebooks or examples containing real credentials. Do not add
application logging that prints resolved connection objects or secret values.

## CI/CD pattern

A deployment system can inject a protected secret into the environment:

```text
CI secret store
      ↓
protected environment variable
      ↓
SecretReference
      ↓
runtime resolution
      ↓
database/native tool
```

The external secret store is deployment-specific; PyDBAdminKit defines the reference and execution
boundary.

## Redaction contract

The 1.0 hardening and qualification work protects secret material from:

- machine JSON/YAML serialization;
- public error text;
- audit events;
- native-tool argv.

Integrations built around PyDBAdminKit should preserve the same boundary.

## Operational checklist

```text
[ ] config stores only secret reference metadata
[ ] secret comes from protected runtime environment
[ ] no credential in source control
[ ] no credential in notebook outputs
[ ] no credential in process argv
[ ] no credential in custom application logs
[ ] machine output remains redacted
```

## References

- `docs/reference/PYTHON_API_REFERENCE.md`
- `docs/contracts/JSON_CONTRACT_INVENTORY.md`
- `docs/security/`
- `docs/releases/T21_005_SECURITY_QUALIFICATION.md`

## Next

Continue with `06_CLI_FUNDAMENTALS.md`.

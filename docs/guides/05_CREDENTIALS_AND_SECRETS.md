# PyDBAdminKit 1.0 — Credentials and Secrets

## Objective

Keep PostgreSQL credentials outside persistent PyDBAdminKit configuration and preserve the
framework's secret boundary from configuration through runtime resolution, database connections,
native PostgreSQL tools, machine output, errors and audit records.

This guide documents the **implemented PyDBAdminKit 1.0 credential model**. The standard 1.0
bootstrap registers one secret provider:

```text
env
```

It resolves a named process environment variable into a runtime `SecretValue`.

PyDBAdminKit 1.0 does not ship a built-in Vault, cloud secret-manager, keyring or encrypted-file
provider.

## Prerequisites

Before continuing, you should understand:

- named connection profiles from
  [Configuration and Profiles](04_CONFIGURATION_AND_PROFILES.md);
- the difference between persistent configuration and runtime state;
- basic environment-variable handling on your operating system.

A typical profile already contains connection metadata:

```toml
[connections.local]
host = "localhost"
database = "postgres"
username = "postgres"
environment = "development"
read_only = true
```

The password should not be added directly to that table.

## Core model

PyDBAdminKit separates a **secret reference** from a **resolved secret value**.

```text
config.toml
    ↓
SecretReference
    ↓
SecretProviderPort
    ↓
EnvironmentSecretProvider
    ↓
SecretValue
    ↓
ResolvedConnectionConfig
    ↓
explicit execution boundary
```

The two important domain objects are:

```text
SecretReference
SecretValue
```

### SecretReference

A `SecretReference` identifies **where** a secret can be obtained.

Persistent TOML example:

```toml
[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"
```

This persists:

```text
provider  → env
reference → PYDBADMIN_LOCAL_PASSWORD
```

It does **not** persist the password.

### SecretValue

At runtime, the provider resolves the reference into a `SecretValue`.

Conceptually:

```text
PYDBADMIN_LOCAL_PASSWORD
        ↓
EnvironmentSecretProvider
        ↓
SecretValue("actual runtime value")
```

The raw value is intentionally not the normal presentation form.

`SecretValue` renders as:

```text
<redacted>
```

through `str()`, while `repr()` renders:

```text
SecretValue(<redacted>)
```

The raw value is accessible only through the explicit `reveal()` boundary and is intended for
infrastructure/adapter execution, not logging or presentation.

## Configure an environment-backed secret

Add the secret reference under the selected connection profile:

```toml
[connections.local]
engine = "postgresql"
host = "localhost"
port = 5432
database = "postgres"
username = "postgres"
environment = "development"
read_only = true
ssl_mode = "prefer"

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"
```

Both `provider` and `reference` must be non-blank strings when the secret table is present.

The implemented standard provider name is exactly:

```text
env
```

## Supply the secret at runtime

### Linux and macOS

For the current shell:

```bash
export PYDBADMIN_LOCAL_PASSWORD='...'
```

Then:

```bash
pydbadmin --connection local connection test
```

Remove it from the current shell when it is no longer required:

```bash
unset PYDBADMIN_LOCAL_PASSWORD
```

### PowerShell

Set it for the current PowerShell process:

```powershell
$env:PYDBADMIN_LOCAL_PASSWORD = "..."
```

Then:

```powershell
pydbadmin --connection local connection test
```

Remove it afterward:

```powershell
Remove-Item Env:PYDBADMIN_LOCAL_PASSWORD
```

Prefer process/session-scoped injection to permanently embedding credentials in shell profiles,
scripts or repository files.

## Resolution behavior

The standard bootstrap resolves the profile and then its secret reference.

For:

```toml
[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

resolution is equivalent to:

```text
read profile
    ↓
find provider "env"
    ↓
read process environment variable
    ↓
wrap value in SecretValue
    ↓
construct ResolvedConnectionConfig
```

If no secret section exists, the resolved connection contains no password:

```text
password = None
```

This can be valid for PostgreSQL environments using another authentication mechanism.

## Missing environment variable

If the profile contains:

```toml
[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

but the process environment does not define that variable, resolution raises:

```text
SecretResolutionError
```

The error states that the referenced environment variable is not defined.

Typical recovery:

```bash
export PYDBADMIN_PROD_PASSWORD='...'

pydbadmin -c prod connection test
```

Do not respond to this error by inserting the raw password into `config.toml`.

## Unsupported provider

The standard bootstrap registers:

```text
EnvironmentSecretProvider()
```

under the provider name:

```text
env
```

A profile such as:

```toml
[connections.prod.secret]
provider = "vault"
reference = "database/prod/password"
```

is syntactically a valid reference shape, but the standard bootstrap cannot resolve it because
`vault` is not registered.

Resolution therefore raises:

```text
SecretResolutionError
```

with the semantic meaning:

```text
Secret provider 'vault' is not registered.
```

Do not document an external provider as supported merely because its name fits the
`SecretReference` structure.

## Public Python API

The stable connection-domain surface includes:

```text
SecretReference
SecretValue
ResolvedConnectionConfig
```

and the public extension boundary includes:

```text
SecretProviderPort
```

For normal application use, start with the public bootstrap API.

### Resolve a connection

```python
from pathlib import Path

from pydbadminkit.bootstrap import resolve_connection

resolved = resolve_connection(
    "local",
    Path("./config.toml"),
)

print(resolved.username)
print(resolved.password)
```

If a password was resolved, the output is redacted:

```text
postgres
<redacted>
```

### Inspect the secret wrapper safely

```python
password = resolved.password

if password is not None:
    print(str(password))
    print(repr(password))
```

Expected representations:

```text
<redacted>
SecretValue(<redacted>)
```

Do not write:

```python
print(password.reveal())
```

in notebooks, diagnostics, test output, application logs or exception messages.

`reveal()` exists for explicit execution boundaries that actually need the database credential.

## Secret-provider extension boundary

PyDBAdminKit exposes `SecretProviderPort` as a public 1.0 extension contract.

Its semantic shape is:

```python
class SecretProviderPort(Protocol):
    @property
    def name(self) -> str:
        ...

    def resolve(self, reference: SecretReference) -> SecretValue:
        ...
```

This makes alternative provider implementations possible in custom application composition.

However:

- the standard bootstrap currently wires only the `env` provider;
- PyDBAdminKit 1.0 does not ship built-in implementations for Vault, AWS Secrets Manager,
  Azure Key Vault, GCP Secret Manager, OS keyrings or similar systems;
- a custom provider should still return `SecretValue` and preserve the same redaction
  invariants.

The existence of the extension port should not be confused with built-in provider support.

## CLI behavior

There is no root option such as:

```text
--password
```

and the 1.0 CLI does not ask users to persist a plaintext password in command history.

Use:

```bash
export PYDBADMIN_LOCAL_PASSWORD='...'

pydbadmin \
  --config ./config.toml \
  --connection local \
  connection test
```

The same resolved credential is then used by commands built from that profile.

Examples:

```bash
pydbadmin -c local server info
pydbadmin -c local database list
pydbadmin -c local health check
```

## Machine output redaction

The 1.0 machine serializer explicitly recognizes `SecretValue`.

When a `SecretValue` reaches JSON/YAML serialization, it becomes:

```text
<redacted>
```

rather than the raw value.

Conceptually:

```python
SecretValue("sensitive")
    ↓
to_machine_value(...)
    ↓
"<redacted>"
```

This applies to the common machine serialization layer used for JSON/YAML-safe values.

The redaction contract protects accidental serialization, but callers should still avoid placing
resolved secret objects into output models unnecessarily.

## Database connection boundary

For direct PostgreSQL connectivity through Psycopg, the resolved password is revealed only when
the adapter constructs the database connection.

The security boundary is therefore:

```text
SecretReference
    ↓
SecretValue
    ↓
Psycopg password parameter
```

The raw password should not be copied into application-level DTOs, logs or public exceptions.

## Backup and restore boundary

PyDBAdminKit invokes PostgreSQL native tools for logical backup/restore workflows, including:

```text
pg_dump
pg_restore
psql
```

The qualified 1.0 security model keeps the password out of command-line arguments.

Instead:

```text
SecretValue
    ↓
child process environment
    ↓
PGPASSWORD
    ↓
PostgreSQL native tool
```

The command execution model uses argument arrays with:

```text
shell=False
```

This matters because command-line arguments can be visible through process inspection,
diagnostics and logs.

The child-process environment remains sensitive and should be treated accordingly.

## Native-tool error redaction

Native PostgreSQL utilities can produce stderr.

The 1.0 hardening pass explicitly redacts the exact resolved secret from external diagnostic text
before:

```text
normalization
    ↓
truncation
    ↓
public exception construction
```

If an unexpected external tool or wrapper echoed the exact runtime password, the public diagnostic
path replaces it with:

```text
<redacted>
```

This prevents the resolved password from flowing into public errors and, indirectly, mutation
audit records that contain public exception messages.

## Public database errors

Psycopg failures are translated into stable public PyDBAdminKit errors.

For example, an authentication failure becomes a public message equivalent to:

```text
Database authentication failed.
```

rather than copying arbitrary raw driver diagnostics into the public boundary.

This is part of the redaction and stable-error design.

## Audit boundary

The audit sink is not a secret store and does not resolve credentials.

The qualified rule is:

```text
raw secrets must not enter audit messages
```

Mutation services may record operation lifecycle information such as:

```text
started
succeeded
failed
blocked
```

but resolved passwords must remain outside that persistence path.

## What not to persist

Do not add a plaintext password field:

```toml
# BAD
[connections.prod]
host = "db.example.internal"
database = "app"
username = "app_dba"
password = "real-password"
```

That field is not part of the supported configuration contract and violates the intended secret
boundary.

Use:

```toml
[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

instead.

## What not to put in source control

Do not commit:

- real database passwords;
- shell scripts containing real passwords;
- `.env` files containing production credentials;
- notebook cells containing real credentials;
- notebook outputs that reveal credentials;
- test fixtures containing reusable production secrets;
- screenshots containing secret values;
- logs copied from a session if they contain sensitive environment data;
- private keys unless the repository and security policy explicitly treat them as protected
  secrets—which a normal source repository should not.

Version control may contain **secret references** and safe templates.

Example:

```toml
[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

## Shell-history considerations

This pattern places the raw value in the shell command line:

```bash
export PYDBADMIN_PROD_PASSWORD='real-password'
```

Depending on the shell and local configuration, commands may be recorded in history.

Prefer the secure secret-injection mechanism of your execution environment when available.

For example, CI/CD systems should inject protected secrets into environment variables rather than
hard-code them in the repository pipeline definition.

PyDBAdminKit defines the runtime reference boundary; storage and injection controls outside the
process remain deployment-specific.

## CI/CD pattern

The intended CI/CD flow is:

```text
CI/CD protected secret store
        ↓
job-scoped environment variable
        ↓
SecretReference(provider="env")
        ↓
PyDBAdminKit runtime resolution
        ↓
SecretValue
        ↓
database or native PostgreSQL tool
```

Repository configuration:

```toml
[connections.staging]
host = "staging-db.example.internal"
database = "app"
username = "automation"
environment = "staging"
read_only = true
ssl_mode = "require"

[connections.staging.secret]
provider = "env"
reference = "PYDBADMIN_STAGING_PASSWORD"
```

The pipeline should supply:

```text
PYDBADMIN_STAGING_PASSWORD
```

through its protected secret mechanism.

The repository should contain the variable **name**, not its value.

## Containers

For containers, the same 1.0 contract applies:

```text
container runtime / orchestrator
        ↓
environment variable
        ↓
provider = "env"
        ↓
SecretValue
```

Avoid baking the password into:

- the container image;
- a Dockerfile;
- a committed Compose file;
- startup scripts inside the image.

The mechanism used to inject the environment variable is external to PyDBAdminKit.

## Notebooks

Notebooks require extra care because both inputs and outputs may be persisted.

Prefer:

```python
from pathlib import Path

from pydbadminkit.bootstrap import resolve_connection

connection = resolve_connection("local", Path("config.toml"))

print(connection.name)
print(connection.database)
print(connection.password)
```

The last line remains redacted.

Avoid:

```python
connection.password.reveal()
```

especially in a notebook cell whose output may be committed.

Before committing a notebook, review its outputs for credentials and other sensitive operational
data.

## Worked example

Create `config.toml`:

```toml
[connections.dev]
host = "localhost"
database = "app_dev"
username = "app_admin"
environment = "development"
read_only = true
ssl_mode = "prefer"

[connections.dev.secret]
provider = "env"
reference = "PYDBADMIN_DEV_PASSWORD"
```

Supply the secret:

```bash
export PYDBADMIN_DEV_PASSWORD='...'
```

Test resolution plus connectivity:

```bash
pydbadmin \
  --config ./config.toml \
  --connection dev \
  connection test
```

Inspect the server:

```bash
pydbadmin \
  --config ./config.toml \
  --connection dev \
  server info
```

Use machine output:

```bash
pydbadmin \
  --config ./config.toml \
  --connection dev \
  --output json \
  health check
```

Then remove the shell variable when the session no longer needs it:

```bash
unset PYDBADMIN_DEV_PASSWORD
```

## Dry-run and secrets

`--dry-run` does not mean that credential resolution is irrelevant.

A mutation plan may still need to connect to the target database to inspect state, capabilities or
preconditions.

Therefore:

```text
dry-run ≠ no credentials
dry-run ≠ safe to use the wrong profile
dry-run ≠ permission to expose a secret
```

Keep secret handling identical between planning and execution.

## Errors

Credential-related failures should be distinguished from database authentication failures.

### ConfigurationError

Used for malformed or unusable configuration.

Example causes:

- malformed TOML;
- malformed secret table;
- blank `provider`;
- blank `reference`.

### SecretResolutionError

Used when the configured secret cannot be resolved.

Example causes:

- referenced environment variable does not exist;
- provider is not registered;
- provider receives a reference intended for another provider.

### AuthenticationError

A secret may resolve successfully but still be rejected by PostgreSQL.

That is a database authentication failure, not a secret-resolution failure.

The distinction is:

```text
reference cannot produce a runtime secret
    → SecretResolutionError

runtime secret exists but PostgreSQL rejects it
    → AuthenticationError
```

This distinction is useful in automation and troubleshooting.

## Troubleshooting

### Environment variable is not defined

Confirm the exact name in TOML:

```toml
reference = "PYDBADMIN_PROD_PASSWORD"
```

Then inspect whether your current process has that variable using an OS-appropriate technique that
does **not** print its value into shared logs.

Re-inject it if necessary and rerun:

```bash
pydbadmin -c prod connection test
```

### Provider is not registered

If the profile says:

```toml
provider = "vault"
```

the standard 1.0 bootstrap cannot resolve it.

Use `provider = "env"` for the built-in path, or provide custom application composition that
implements the public secret-provider extension contract.

### Password is redacted in Python

This is expected:

```python
print(resolved.password)
```

returns:

```text
<redacted>
```

Do not work around this for debugging by broadly logging `reveal()`.

### Connection still fails after secret resolution

Possible causes include:

- wrong password value;
- wrong username;
- PostgreSQL authentication rules;
- expired/rotated credential;
- target host/database mismatch;
- SSL configuration mismatch.

At that point, the problem is beyond the secret-reference lookup itself.

### Different shell/process cannot see the secret

Environment variables are process-scoped.

A value exported in one shell is not automatically available to unrelated processes, services,
containers or CI jobs.

Inject the variable into the process environment that actually launches `pydbadmin`.

## Rotation

PyDBAdminKit's reference model supports credential rotation without changing the profile structure
when the variable name remains stable.

For example:

```toml
reference = "PYDBADMIN_PROD_PASSWORD"
```

can remain unchanged while the protected runtime value behind that environment variable changes.

Operationally:

```text
stable reference
    +
rotated runtime value
    =
no plaintext config rewrite
```

Rotation of the external secret itself is the responsibility of the surrounding deployment or
secret-management system.

## Production considerations

For production:

1. keep only `SecretReference` metadata in TOML;
2. inject credentials at process/job runtime;
3. avoid persistent shell-history exposure;
4. separate read-only and administrative database identities;
5. use least-privilege PostgreSQL roles;
6. avoid sharing one credential across unrelated environments;
7. rotate credentials using the external secret-management process;
8. never place raw credentials in CLI arguments;
9. preserve redaction when wrapping PyDBAdminKit in custom code;
10. keep diagnostic and audit pipelines free of raw secret material;
11. restrict access to certificate private keys independently from password handling;
12. review notebook outputs and CI logs before publication.

PyDBAdminKit's redaction controls reduce accidental leakage. They do not replace operating-system,
CI/CD, container-platform or organizational secret-management controls.

## Redaction contract

The 1.0 hardening rule is:

```text
SecretValue may be revealed only at an explicit execution boundary.

Raw secrets must not enter:
- process argv
- public errors
- machine output
- audit messages

External diagnostic text must be redacted before it crosses
the adapter boundary.
```

This is the central rule to preserve when extending or embedding the framework.

## Operational checklist

Before running against a sensitive environment:

```text
[ ] configuration contains only SecretReference metadata
[ ] provider is "env" when using the standard bootstrap
[ ] referenced variable name is correct
[ ] runtime secret is injected through a protected mechanism
[ ] no raw password exists in config.toml
[ ] no raw password exists in repository files
[ ] no raw password exists in notebook outputs
[ ] no raw password is supplied as CLI argv
[ ] custom logging does not call SecretValue.reveal()
[ ] CI logs do not echo secret environment values
[ ] target profile uses the intended database identity
[ ] read-only identity is preferred for inspection
```

## Best practices

Prefer:

```text
SecretReference in persistent config
job/process-scoped secret injection
stable environment-variable names
least-privilege PostgreSQL identities
separate credentials per environment/purpose
redacted machine/public output
rotation outside source control
custom providers through the public port boundary
```

Avoid:

```text
plaintext password fields
password CLI arguments
passwords in Git
passwords in notebooks
passwords in application logs
revealing SecretValue for debugging
assuming arbitrary providers are built in
putting credentials into native-tool argv
using production credentials for local experimentation
```

## Key takeaways

- Persistent profiles store `SecretReference`, not resolved passwords.
- The standard 1.0 bootstrap registers only the `env` secret provider.
- The environment provider reads the variable named by `reference` at runtime.
- Missing variables and unregistered providers raise `SecretResolutionError`.
- Resolved secrets are wrapped in `SecretValue`.
- `str()`, `repr()` and machine serialization preserve redaction.
- Raw access through `reveal()` belongs only at explicit execution boundaries.
- Psycopg receives the password at its connection boundary.
- PostgreSQL native tools receive passwords through child `PGPASSWORD`, not argv.
- Native-tool diagnostics are redacted before public exception construction.
- Audit and machine-output paths must remain free of raw credentials.
- `SecretProviderPort` is a public extension point, but alternative providers are not built into
  the standard 1.0 bootstrap.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Configuration and Profiles](04_CONFIGURATION_AND_PROFILES.md)
- [CLI fundamentals](06_CLI_FUNDAMENTALS.md)
- [Python API fundamentals](08_PYTHON_API_FUNDAMENTALS.md)
- [Backup guide](18_BACKUP_GUIDE.md)
- [Restore guide](19_RESTORE_GUIDE.md)
- [Audit and operation traceability](25_AUDIT_AND_OPERATION_TRACEABILITY.md)
- [Error handling and exit codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Production usage and safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
- [Configuration contract](../contracts/CONFIG_CONTRACT.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)
- [LOT-20 redaction review](../security/LOT20_REDACTION_REVIEW.md)
- [LOT-21 security qualification](../releases/T21_005_SECURITY_QUALIFICATION.md)

## Next

Continue with [CLI Fundamentals](06_CLI_FUNDAMENTALS.md).

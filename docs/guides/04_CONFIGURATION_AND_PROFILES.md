# PyDBAdminKit 1.0 — Configuration and Profiles

## Objective

Use explicit, named database profiles so that connection identity, deployment environment and
safety intent are visible before an administrative operation starts.

This guide covers the **implemented PyDBAdminKit 1.0 configuration contract**. It explains how
to create and select profiles, which fields are supported, how defaults behave, and which
configuration patterns are intentionally **not** part of the 1.0 runtime.

For the normative contract, see
[`CONFIG_CONTRACT.md`](../contracts/CONFIG_CONTRACT.md).

## Prerequisites

Before continuing, you should have:

- PyDBAdminKit 1.0 installed;
- a reachable PostgreSQL server;
- completed [First connection](03_FIRST_CONNECTION.md), or equivalent familiarity with
  `pydbadmin --connection <profile> ...`;
- a safe way to provide the database password at execution time.

PyDBAdminKit 1.0 uses PostgreSQL as its implemented database engine.

## Configuration model

The runtime resolution path is intentionally explicit:

```text
TOML configuration file
        ↓
named connection profile
        ↓
secret reference
        ↓
registered secret provider
        ↓
resolved runtime connection configuration
        ↓
PostgreSQL adapter
```

Persistent configuration stores connection metadata and a **reference** to a secret. It does
not store the resolved raw password.

A profile therefore answers questions such as:

```text
Which server?
Which port?
Which database?
Which username?
Which deployment environment?
Should this profile permit mutations?
Which SSL policy?
Which timeouts?
Where should the password be resolved?
```

## Configuration file location

You can always select a configuration file explicitly:

```bash
pydbadmin \
  --config /path/to/config.toml \
  --connection dev \
  connection test
```

When `--config` is omitted, PyDBAdminKit uses the platform-specific user configuration
directory returned by `platformdirs.user_config_path("pydbadminkit")`, with the filename:

```text
config.toml
```

Using an explicit `--config` path is recommended for automation, CI/CD and operational
runbooks because it removes ambiguity about which configuration source is active.

### No `PYDBADMIN_CONFIG` override in 1.0

Earlier design material mentions a `PYDBADMIN_CONFIG` environment variable. The implemented
1.0 runtime does **not** resolve that variable as a configuration-file override.

Use:

```bash
pydbadmin --config ./config.toml ...
```

rather than relying on an undocumented environment-based configuration path.

## Top-level TOML structure

Connection profiles live below:

```toml
[connections.<profile-name>]
```

For example:

```toml
[connections.dev]
host = "localhost"
database = "app_dev"
username = "app_admin"
```

The profile name is the identifier passed through the CLI:

```bash
pydbadmin --connection dev connection test
```

or through the public Python bootstrap API:

```python
from pathlib import Path

from pydbadminkit.bootstrap import resolve_connection

connection = resolve_connection("dev", Path("config.toml"))

print(connection.name)
print(connection.host)
print(connection.database)
```

## Minimal profile

Only three connection fields are required by the current loader:

```toml
[connections.local]
host = "localhost"
database = "postgres"
username = "postgres"
```

With this minimal profile, PyDBAdminKit applies the frozen 1.0 defaults:

| Field | Default |
| --- | --- |
| `engine` | `postgresql` |
| `port` | `5432` |
| `environment` | `unknown` |
| `read_only` | `false` |
| `ssl_mode` | `prefer` |
| `ssl_root_cert` | unset |
| `ssl_cert` | unset |
| `ssl_key` | unset |
| `connect_timeout_seconds` | `10` |
| `statement_timeout_ms` | unset |
| `lock_timeout_ms` | unset |
| secret | unset |

A minimal profile can therefore be useful for local experimentation, but production profiles
should normally make environment, safety and transport intent explicit rather than relying on
defaults.

## Complete profile example

A complete implemented profile looks like this:

```toml
[connections.prod]
engine = "postgresql"
host = "db.example.internal"
port = 5432
database = "app"
username = "app_dba"
environment = "production"
read_only = true
ssl_mode = "verify-full"
ssl_root_cert = "/etc/ssl/certs/company-root.pem"
ssl_cert = "/etc/pydbadminkit/client.pem"
ssl_key = "/etc/pydbadminkit/client.key"
connect_timeout_seconds = 5
statement_timeout_ms = 30000
lock_timeout_ms = 5000

[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

Provide the referenced secret at execution time:

```bash
export PYDBADMIN_PROD_PASSWORD='...'
```

Then test the profile:

```bash
pydbadmin \
  --config ./config.toml \
  --connection prod \
  connection test
```

The next guide covers credentials and secret handling in detail.

## Stable profile fields

The implemented 1.0 profile surface is:

| Field | Type | Required | Default |
| --- | --- | --- | --- |
| `engine` | string | no | `postgresql` |
| `host` | string | yes | — |
| `port` | integer | no | `5432` |
| `database` | string | yes | — |
| `username` | string | yes | — |
| `environment` | enum string | no | `unknown` |
| `read_only` | boolean | no | `false` |
| `ssl_mode` | enum string | no | `prefer` |
| `ssl_root_cert` | string | no | unset |
| `ssl_cert` | string | no | unset |
| `ssl_key` | string | no | unset |
| `connect_timeout_seconds` | integer | no | `10` |
| `statement_timeout_ms` | integer | no | unset |
| `lock_timeout_ms` | integer | no | unset |

When a secret table is present, both fields below are required and must be non-blank:

```toml
[connections.<profile>.secret]
provider = "env"
reference = "VARIABLE_NAME"
```

## Flat SSL and timeout syntax

PyDBAdminKit 1.0 keeps SSL and timeout fields directly on the profile table:

```toml
[connections.prod]
ssl_mode = "verify-full"
ssl_root_cert = "/certs/root.pem"
connect_timeout_seconds = 5
statement_timeout_ms = 30000
lock_timeout_ms = 5000
```

Earlier design documents may show nested structures such as:

```toml
[connections.prod.ssl]

[connections.prod.timeouts]
```

Those nested forms are **not** the implemented 1.0 loader contract.

## Multiple profiles

One configuration file can describe several database targets:

```toml
[connections.dev]
engine = "postgresql"
host = "localhost"
port = 5432
database = "app_dev"
username = "app_admin"
environment = "development"
read_only = false
ssl_mode = "prefer"

[connections.dev.secret]
provider = "env"
reference = "PYDBADMIN_DEV_PASSWORD"

[connections.staging]
engine = "postgresql"
host = "staging-db.example.internal"
port = 5432
database = "app"
username = "app_admin"
environment = "staging"
read_only = true
ssl_mode = "require"

[connections.staging.secret]
provider = "env"
reference = "PYDBADMIN_STAGING_PASSWORD"

[connections.prod]
engine = "postgresql"
host = "prod-db.example.internal"
port = 5432
database = "app"
username = "app_dba"
environment = "production"
read_only = true
ssl_mode = "verify-full"

[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

Select the target explicitly:

```bash
pydbadmin -c dev server info
pydbadmin -c staging server info
pydbadmin -c prod server info
```

This pattern lets one operator or automation environment keep the **same command shape** while
making the target a deliberate choice.

## Profile naming

Profile names are identifiers, not display labels.

Prefer short, stable names such as:

```text
local
dev
test
staging
prod
analytics-prod
customer-a-readonly
```

Avoid encoding credentials, passwords or transient information in the profile name.

A blank profile name is invalid.

## Environment classification

The stable environment values are:

```text
development
testing
staging
production
unknown
```

Example:

```toml
environment = "production"
```

Environment is not decorative metadata. PyDBAdminKit uses it as an input to safety policy
evaluation.

In particular, do not deliberately mark a production target as `development` merely to make
an operation easier to execute. The profile should describe the real operational environment.

### Prefer explicit environment values

Although `unknown` is the default, explicitly declaring the environment makes reviews and
runbooks easier to reason about:

```toml
environment = "staging"
```

For administration profiles, explicit environment classification is preferred over relying on
`unknown`.

## Read-only profiles

The field:

```toml
read_only = true
```

expresses that PyDBAdminKit should treat the profile as non-mutating.

Good uses include:

- first access to an unfamiliar PostgreSQL server;
- production diagnostics;
- catalog inspection;
- security inspection;
- runtime inspection;
- health checks;
- monitoring;
- automation that must never intentionally alter database state.

A useful operational pattern is to maintain **separate profiles** for inspection and mutation.

For example:

```toml
[connections.prod_ro]
host = "prod-db.example.internal"
database = "app"
username = "app_observer"
environment = "production"
read_only = true
ssl_mode = "verify-full"

[connections.prod_ro.secret]
provider = "env"
reference = "PYDBADMIN_PROD_RO_PASSWORD"

[connections.prod_admin]
host = "prod-db.example.internal"
database = "app"
username = "app_dba"
environment = "production"
read_only = false
ssl_mode = "verify-full"

[connections.prod_admin.secret]
provider = "env"
reference = "PYDBADMIN_PROD_ADMIN_PASSWORD"
```

This is safer than repeatedly editing a single production profile between read-only and writable
modes.

## SSL modes

The supported SSL mode values are libpq-compatible:

```text
disable
allow
prefer
require
verify-ca
verify-full
```

Example:

```toml
ssl_mode = "verify-full"
ssl_root_cert = "/certs/company-root.pem"
```

Optional client-certificate fields are also supported:

```toml
ssl_cert = "/certs/client.pem"
ssl_key = "/certs/client.key"
```

Choose SSL settings according to the PostgreSQL deployment and your organization's transport
security requirements. Do not copy local-development settings such as `disable` into
production profiles without deliberate justification.

## Timeouts

Three timeout concerns are modeled separately.

### Connection timeout

```toml
connect_timeout_seconds = 10
```

Controls connection establishment. It must be a positive integer.

### Statement timeout

```toml
statement_timeout_ms = 30000
```

Represents the PostgreSQL statement execution timeout. When provided, it must be a positive
integer.

### Lock timeout

```toml
lock_timeout_ms = 5000
```

Represents the PostgreSQL lock-acquisition timeout. When provided, it must be a positive
integer.

Do not treat these as interchangeable:

```text
connect timeout   → establishing the database connection
statement timeout → statement execution
lock timeout      → waiting to acquire a lock
```

The correct values depend on the operation and the environment.

## Secret references

A profile may omit a secret entirely, for example when PostgreSQL authentication does not
require a password in the target environment.

When a password is required, persist only a reference:

```toml
[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

The persisted profile never needs to contain:

```toml
password = "plaintext-secret"
```

The current standard bootstrap registers the environment secret provider. Detailed secret
resolution rules are covered in
[Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md).

## Selecting a profile from the CLI

The root option is:

```text
--connection, -c
```

Examples:

```bash
pydbadmin --connection dev connection test
pydbadmin -c dev server info
pydbadmin -c prod database list
```

With an explicit configuration file:

```bash
pydbadmin \
  --config ./ops/config.toml \
  --connection prod \
  --output json \
  server info
```

Root options should be supplied before the command group and command in documented examples.

## Configuration through the Python API

For application code, use the stable bootstrap layer rather than importing configuration
infrastructure directly.

### Resolve a profile

```python
from pathlib import Path

from pydbadminkit.bootstrap import resolve_connection

resolved = resolve_connection(
    "prod",
    Path("./config.toml"),
)

print(resolved.name)
print(resolved.host)
print(resolved.port)
print(resolved.database)
print(resolved.username)
print(resolved.environment)
print(resolved.read_only)
print(resolved.ssl.mode)
print(resolved.timeouts.connect_seconds)
```

If the profile contains a secret reference, the runtime password is represented by a
`SecretValue`.

Its string and `repr` forms are redacted:

```python
print(resolved.password)
# <redacted>
```

Do not call `SecretValue.reveal()` in application logging, notebooks or debugging output.
Raw secret access exists for the execution boundary, not for presentation.

### Build services from a profile

The same profile can be used through the public bootstrap service builders:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_server_service

server = build_server_service(
    "prod",
    Path("./config.toml"),
)

info = server.get_info()
print(info)
```

Application code should not depend on:

```text
pydbadminkit.infrastructure.*
pydbadminkit.adapters.*
pydbadminkit.cli.*
```

Those modules are implementation details and are outside the stable 1.0 compatibility boundary.

## No profile CRUD command in 1.0

The current 1.0 CLI exposes:

```text
connection test
```

It does **not** expose public commands such as:

```text
connection add
connection list
connection update
connection delete
```

Manage the TOML file through your normal configuration-management workflow and then validate the
selected profile with:

```bash
pydbadmin --config ./config.toml -c dev connection test
```

Some early planning documents describe broader profile-management commands. They should not be
treated as executable 1.0 functionality.

## No general override precedence engine in 1.0

Some architecture material describes a broader precedence concept such as:

```text
explicit Python/CLI
    >
PYDBADMIN_* environment overrides
    >
profile
    >
defaults
```

PyDBAdminKit 1.0 does **not** implement that as a general configuration override engine.

The actual stable model is simpler:

```text
selected TOML file
    +
selected named profile
    +
secret resolution
    +
frozen field defaults
```

Document automation against the implemented behavior, not the broader future design.

## Validation rules

Configuration loading rejects malformed or invalid profile data.

Examples include:

- invalid TOML syntax;
- a non-table `connections` value;
- a non-table profile value;
- missing or blank `host`;
- missing or blank `database`;
- missing or blank `username`;
- invalid `engine`;
- invalid `environment`;
- invalid `ssl_mode`;
- a non-integer `port`;
- a port outside `1..65535`;
- a non-boolean `read_only`;
- non-integer timeout fields;
- non-positive timeout values;
- malformed secret-reference fields.

A malformed configuration raises the public typed error:

```text
ConfigurationError
```

Requesting a profile that does not exist raises:

```text
ProfileNotFoundError
```

Secret resolution failures use:

```text
SecretResolutionError
```

See [Error handling and exit codes](26_ERROR_HANDLING_AND_EXIT_CODES.md) for the complete
failure model.

## Worked example — local, staging and production

Create `config.toml`:

```toml
[connections.local]
host = "localhost"
database = "postgres"
username = "postgres"
environment = "development"
read_only = false
ssl_mode = "disable"

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"

[connections.staging]
host = "staging-db.example.internal"
database = "app"
username = "app_observer"
environment = "staging"
read_only = true
ssl_mode = "require"
connect_timeout_seconds = 5

[connections.staging.secret]
provider = "env"
reference = "PYDBADMIN_STAGING_PASSWORD"

[connections.prod]
host = "prod-db.example.internal"
database = "app"
username = "app_observer"
environment = "production"
read_only = true
ssl_mode = "verify-full"
ssl_root_cert = "/certs/company-root.pem"
connect_timeout_seconds = 5
statement_timeout_ms = 15000
lock_timeout_ms = 3000

[connections.prod.secret]
provider = "env"
reference = "PYDBADMIN_PROD_PASSWORD"
```

Export only the secret needed for the current target:

```bash
export PYDBADMIN_LOCAL_PASSWORD='...'
```

Test local:

```bash
pydbadmin --config ./config.toml -c local connection test
```

Inspect the server:

```bash
pydbadmin --config ./config.toml -c local server info
```

For staging:

```bash
export PYDBADMIN_STAGING_PASSWORD='...'

pydbadmin \
  --config ./config.toml \
  -c staging \
  --output json \
  health check
```

For production inspection:

```bash
export PYDBADMIN_PROD_PASSWORD='...'

pydbadmin \
  --config ./config.toml \
  -c prod \
  server info
```

The production profile remains `read_only = true`, making its intended role obvious before
later mutation-oriented guides are introduced.

## Table, JSON and YAML output

Configuration selection is independent of rendering mode.

The same profile can be used with human-readable output:

```bash
pydbadmin -c prod --output table server info
```

or machine-readable output:

```bash
pydbadmin -c prod --output json server info
pydbadmin -c prod --output yaml server info
```

Changing output format does not change the selected profile, connection metadata or safety
semantics.

## Dry-run and configuration

`--dry-run` is a mutation-planning control, not a configuration validation mode.

For example, this tests the connection:

```bash
pydbadmin -c prod connection test
```

while later mutation commands may use:

```bash
pydbadmin -c prod --dry-run <mutation-command>
```

Do not assume that `--dry-run` makes an incorrect profile safe. Always verify the target
profile, host, database, username and environment before a mutation is planned.

## Troubleshooting

### Configuration file not found

Symptom:

```text
ConfigurationError
```

Check:

- the `--config` path;
- the current working directory for relative paths;
- file permissions;
- whether you expected the platform-specific default config location.

Prefer an absolute configuration path in production automation.

### Invalid TOML

Validate brackets, quoting and table structure.

A correct profile header looks like:

```toml
[connections.prod]
```

A secret table is nested below the profile:

```toml
[connections.prod.secret]
```

### Profile not found

If:

```bash
pydbadmin -c production connection test
```

fails with `ProfileNotFoundError`, verify that the TOML file actually contains:

```toml
[connections.production]
```

Profile selection is by exact name.

### Invalid timeout

These values are invalid:

```toml
connect_timeout_seconds = 0
statement_timeout_ms = -1
lock_timeout_ms = 0
```

Configured timeout values must be positive integers.

### Invalid port

The port must be an integer between `1` and `65535`.

### Secret provider not registered

A profile can be syntactically valid yet fail during resolution if it references a provider not
registered by the active bootstrap.

The standard 1.0 bootstrap supports the environment provider:

```toml
provider = "env"
```

### Configuration appears ignored

Verify whether the command is reading the expected file.

Use an explicit path:

```bash
pydbadmin --config /absolute/path/config.toml -c prod connection test
```

Do not rely on `PYDBADMIN_CONFIG`; it is not a 1.0 runtime override.

## Production considerations

For production profiles:

1. declare `environment = "production"` explicitly;
2. prefer `read_only = true` for inspection-only workflows;
3. use a separate writable administration identity when mutation is required;
4. use an explicit `--config` path in automation;
5. keep passwords outside TOML;
6. select SSL policy deliberately;
7. use timeouts appropriate to the operational task;
8. keep certificate/key file permissions restrictive;
9. test the exact profile before running operational commands;
10. review the profile alongside the runbook that uses it.

A production profile should make a dangerous target **more obvious**, not more convenient to
operate accidentally.

## Best practices

Prefer:

```text
one explicit profile per operational identity
clear environment names
read-only inspection profiles
secret references instead of passwords
explicit config paths in automation
verify-full where deployment policy requires certificate and hostname verification
bounded timeouts
version-controlled templates without secrets
configuration review before mutation
```

Avoid:

```text
plaintext passwords in TOML
one shared profile for every environment
mislabeling production as development
editing read_only back and forth casually
depending on undocumented environment overrides
depending on internal infrastructure classes
copying obsolete nested config examples
assuming dry-run compensates for a wrong target
```

## Key takeaways

- PyDBAdminKit 1.0 uses TOML connection profiles below `[connections.<name>]`.
- `host`, `database` and `username` are required; the remaining connection fields have
  frozen defaults or are optional.
- The stable loader uses **flat** SSL and timeout fields.
- The selected profile carries environment and read-only safety intent.
- Persistent configuration stores secret references, not resolved passwords.
- The standard bootstrap resolves `env` secret references.
- `--config` selects an explicit configuration file; `PYDBADMIN_CONFIG` is not part of the
  implemented 1.0 runtime.
- The CLI does not provide connection-profile CRUD commands in 1.0.
- Python consumers should use public bootstrap functions rather than infrastructure
  implementation classes.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [First connection](03_FIRST_CONNECTION.md)
- [Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md)
- [CLI fundamentals](06_CLI_FUNDAMENTALS.md)
- [Python API fundamentals](08_PYTHON_API_FUNDAMENTALS.md)
- [Dry-run, guardrails and confirmations](24_DRY_RUN_GUARDRAILS_AND_CONFIRMATIONS.md)
- [Error handling and exit codes](26_ERROR_HANDLING_AND_EXIT_CODES.md)
- [Production usage and safety](31_PRODUCTION_USAGE_AND_SAFETY.md)
- [Configuration contract](../contracts/CONFIG_CONTRACT.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

## Next

Continue with [Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md).

# PyDBAdminKit 1.0 — Configuration and Profiles

## Objective

Model database targets as explicit named profiles and make environment, connectivity and safety
intent visible before administration begins.

## Persistent format

PyDBAdminKit 1.0 uses TOML for persistent configuration.

Select a profile:

```bash
pydbadmin --connection <profile> ...
```

Select an explicit configuration file:

```bash
pydbadmin --config /path/to/config.toml --connection <profile> ...
```

## Complete profile example

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
connect_timeout_seconds = 10
statement_timeout_ms = 30000
lock_timeout_ms = 5000

[connections.dev.secret]
provider = "env"
reference = "PYDBADMIN_DEV_PASSWORD"
```

## Stable profile fields

The 1.0 configuration contract includes:

```text
engine
host
port
database
username
environment
read_only
ssl_mode
ssl_root_cert
ssl_cert
ssl_key
connect_timeout_seconds
statement_timeout_ms
lock_timeout_ms
```

The secret section stores provider/reference metadata, not resolved credential material.

## Multiple environments

A configuration can contain several named targets:

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

[connections.prod]
engine = "postgresql"
host = "db.example.internal"
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

This makes the target explicit at invocation time:

```bash
pydbadmin -c dev server info
pydbadmin -c prod server info
```

## Environment is operational metadata

The model recognizes environment intent including:

```text
development
testing
staging
production
unknown
```

Environment participates in mutation safety and risk evaluation. An unknown environment fails
closed for mutations.

## Read-only profiles

Use `read_only = true` for:

- first access to an unfamiliar server;
- diagnostics;
- catalog/security inspection;
- runtime inspection;
- monitoring and health;
- environments where PyDBAdminKit should never mutate state.

Prefer a distinct writable administration profile when mutations are required rather than
casually weakening a diagnostic profile.

## SSL modes

The stable connection model supports:

```text
disable
allow
prefer
require
verify-ca
verify-full
```

Certificate fields `ssl_root_cert`, `ssl_cert` and `ssl_key` are available when the deployment
requires certificate material.

## Timeouts

Three configuration concerns are distinct:

```text
connect_timeout_seconds   connection establishment
statement_timeout_ms      PostgreSQL statement execution
lock_timeout_ms           PostgreSQL lock acquisition
```

Use values appropriate to the operational context rather than treating all timeouts as one global
limit.

## Automation

In scripts and CI/CD, an explicit configuration path reduces ambiguity:

```bash
pydbadmin   --config ./config.toml   --connection staging   --output json   health check
```

## Pre-mutation checklist

```text
[ ] profile name
[ ] host
[ ] database
[ ] username
[ ] environment
[ ] read_only state
[ ] exact operation target
[ ] dry-run plan
[ ] confirmation requirement
```

## Next

Continue with [Credentials and Secrets](05_CREDENTIALS_AND_SECRETS.md).

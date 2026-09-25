# PyDBAdminKit 1.0 — First Connection

## Objective

Establish the first PostgreSQL connection safely, validate the selected target, and perform a
small read-only discovery sequence.

## 1. Create a profile

Create `config.toml`:

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
connect_timeout_seconds = 10

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"
```

The password is intentionally not stored in the profile.

## 2. Supply the secret

Linux/macOS:

```bash
export PYDBADMIN_LOCAL_PASSWORD="..."
```

PowerShell:

```powershell
$env:PYDBADMIN_LOCAL_PASSWORD = "..."
```

## 3. Test connectivity

```bash
pydbadmin --config config.toml --connection local connection test
```

The selected connection is a root execution concern: subsequent commands use the same
`--connection` / `-c` option.

## 4. Identify the server

```bash
pydbadmin --config config.toml --connection local server info
```

Then enumerate databases and schemas:

```bash
pydbadmin --config config.toml --connection local database list
pydbadmin --config config.toml --connection local schema list
```

## 5. Discover capabilities

```bash
pydbadmin --config config.toml --connection local capability list
```

Capability discovery is preferable to assuming that every operation is available in every
PostgreSQL environment.

## 6. Run the first health check

```bash
pydbadmin --config config.toml --connection local health check
```

Machine-readable form:

```bash
pydbadmin --config config.toml --connection local --output json health check
```

## Python API

The public composition root is `pydbadminkit.bootstrap`. For application code, prefer the
public builders rather than importing PostgreSQL adapters directly.

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service

catalog = build_catalog_service("local", Path("config.toml"))
databases = catalog.list_databases()

for database in databases:
    print(database)
```

The bootstrap builders are part of the stable 1.0 convenience API. Adapter, infrastructure,
CLI-internal, mapper and PostgreSQL query modules are not stable public contracts.

## Recommended first diagnostic sequence

```text
connection test
    ↓
server info
    ↓
database list
    ↓
schema list
    ↓
capability list
    ↓
health check
```

Keep the first profile `read_only = true`. This adds a fail-closed boundary while learning the
inspection surface.

## Troubleshooting direction

Failures are represented through typed public errors. Configuration, secret resolution,
authentication/authorization, connection, capability and timeout failures remain distinct.

For automation semantics, consult:

- `docs/contracts/ERROR_CODE_CONTRACT.md`
- `docs/contracts/EXIT_CODE_CONTRACT.md`
- `docs/reference/CLI_REFERENCE.md`

## Next

Continue with [Configuration and Profiles](04_CONFIGURATION_AND_PROFILES.md).

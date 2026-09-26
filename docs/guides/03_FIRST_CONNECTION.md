# PyDBAdminKit 1.0 — First Connection

## Objective

Establish a first PostgreSQL connection with **PyDBAdminKit 1.0**, validate the selected
target, and perform a small read-only discovery sequence.

At the end of this guide you will be able to:

- define a named PostgreSQL profile;
- keep its password outside the TOML file;
- select a config file and profile explicitly;
- test connectivity;
- inspect the server and catalog without mutation;
- use the same connection through the public Python API;
- distinguish connectivity from authorization and capability.

This guide deliberately starts with `read_only = true`.

## 1. Prerequisites

You need PyDBAdminKit 1.0 installed, Python 3.11–3.14, a reachable PostgreSQL server,
a database name and a PostgreSQL login role.

Verify the installation:

```bash
pydbadmin --version
pydbadmin --help
```

For this guide line the version should report `pydbadminkit 1.0.0`.

## 2. Understand the connection path

```text
config.toml
    ↓
named ConnectionProfile
    ├── host / port / database / username
    ├── environment / read_only / SSL / timeout
    └── SecretReference
            ↓
      environment variable
            ↓
 ResolvedConnectionConfig
            ↓
        PostgreSQL
```

The persisted profile describes how to connect. The password is resolved only at execution
time.

## 3. Create the first profile

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

The profile name is `local`. The value of `reference` is the **name of an environment
variable**, not the password.

The first profile intentionally combines:

```text
environment = development
read_only   = true
```

so exploration starts behind a fail-closed mutation boundary.

## 4. Supply the secret

Linux/macOS:

```bash
export PYDBADMIN_LOCAL_PASSWORD="your_password"
```

Windows PowerShell:

```powershell
$env:PYDBADMIN_LOCAL_PASSWORD = "your_password"
```

Do not put the raw password in `config.toml`, source control, shell scripts or examples.

PyDBAdminKit 1.0 does not expose a root `--password` option. This also avoids teaching a
pattern that can leak credentials through shell history or process inspection.

## 5. Select the config and profile

When the file is not at the platform default configuration path, select it explicitly:

```bash
pydbadmin --config ./config.toml --connection local connection test
```

The root options have separate responsibilities:

| Option | Purpose |
| --- | --- |
| `--config PATH` | select the TOML configuration file |
| `--connection NAME`, `-c NAME` | select one named profile |

## 6. Test connectivity

Run:

```bash
pydbadmin --config ./config.toml --connection local connection test
```

The implemented 1.0 `connection` command currently exposes `connection test`. Older
design material may mention planned CRUD commands for profiles; do not treat those as
executable 1.0 CLI commands.

A successful test proves that the profile and secret can be resolved and that the tested
PostgreSQL connection can be established.

It does **not** prove that the account may perform every administration operation.
Authorization, capabilities, native tools, managed-service restrictions and PyDBAdminKit
guardrails remain separate concerns.

## 7. Identify the server

After a successful test:

```bash
pydbadmin --config ./config.toml --connection local server info
```

Then enumerate the first catalog levels:

```bash
pydbadmin --config ./config.toml --connection local database list
pydbadmin --config ./config.toml --connection local schema list
pydbadmin --config ./config.toml --connection local table list --schema public
```

These are inspection operations and are the recommended way to become familiar with a
target before enabling any mutation.

## 8. Discover capabilities

```bash
pydbadmin --config ./config.toml --connection local capability list
```

Capability discovery is preferable to assuming that every operation exists or is usable
in every PostgreSQL environment.

A successful connection and a supported PostgreSQL version still do not imply that every
capability is effective for the current principal or deployment.

## 9. Run the first health check

```bash
pydbadmin --config ./config.toml --connection local health check
```

The default health suite is point-in-time monitoring. It does not automatically cancel
queries, terminate sessions, vacuum objects or perform other remediation.

Machine-readable form:

```bash
pydbadmin --config ./config.toml --connection local --output json health check
```

## 10. Table, JSON and YAML output

Human table output is the default. The implemented root CLI supports:

```text
table
json
yaml
```

Examples:

```bash
pydbadmin --config ./config.toml --connection local --output json server info
pydbadmin --config ./config.toml --connection local --output yaml database list
```

For scripts and CI/CD, consume the machine interface rather than parsing human table
rendering.

## 11. Test the profile from Python

The stable composition root is `pydbadminkit.bootstrap`.

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_connection_service

connections = build_connection_service(Path("config.toml"))
result = connections.test("local")

print(result)
```

The public resolver is also available when application code needs the typed resolved
configuration:

```python
from pathlib import Path

from pydbadminkit.bootstrap import resolve_connection

config = resolve_connection("local", Path("config.toml"))

print(config.host)
print(config.port)
print(config.database)
print(config.username)
```

Never print or serialize resolved secret material.

## 12. First Python inspection

Build the public server service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_server_service

server = build_server_service("local", Path("config.toml"))
info = server.get_info()

print(info)
```

Then the catalog service:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service

catalog = build_catalog_service("local", Path("config.toml"))

for database in catalog.list_databases():
    print(database)
```

Application integrations should use public bootstrap builders, application services and
domain objects. Do not couple user code to `pydbadminkit.adapters.*`,
`pydbadminkit.infrastructure.*` or `pydbadminkit.cli.*` internals.

## 13. SSL and timeout

This tutorial uses:

```toml
ssl_mode = "prefer"
connect_timeout_seconds = 10
```

These are learning-profile values, not universal production policy.

Production TLS requirements depend on the PostgreSQL deployment and organizational policy.
A finite connection timeout is desirable, but its value should reflect the network and
operational environment.

The next guides cover configuration and credentials in detail.

## 14. Dry-run and first-connection safety

`--dry-run` exists for supported **mutating operations**. A connection test is already
non-mutating, so dry-run is not part of this workflow.

Keep:

```toml
read_only = true
```

while learning inspection commands.

The safe progression is:

```text
connect
  ↓
identify target
  ↓
inspect
  ↓
discover capabilities
  ↓
understand guardrails
  ↓
only then learn mutations
```

## 15. Troubleshooting

### Profile not found

Verify the profile heading and selected name:

```toml
[connections.local]
```

```bash
--connection local
```

If the file is outside the default path, pass `--config ./config.toml`.

### Secret cannot be resolved

Verify that the reference:

```toml
reference = "PYDBADMIN_LOCAL_PASSWORD"
```

matches an environment variable exported in the shell/process that launches PyDBAdminKit.

Check presence without printing the secret.

Linux/macOS:

```bash
test -n "$PYDBADMIN_LOCAL_PASSWORD" && echo "secret variable is set"
```

PowerShell:

```powershell
if ($env:PYDBADMIN_LOCAL_PASSWORD) { "secret variable is set" }
```

### Connection refused

Check host, port, PostgreSQL service state, firewall/network path and container port
publication when applicable.

### Authentication fails

A reachable endpoint can still reject the login. Verify the PostgreSQL role, password and
server authentication policy.

### Database does not exist

The connection targets the exact configured database. Use an existing database for which
the selected role has `CONNECT` access.

### SSL negotiation fails

Verify that `ssl_mode` matches the target deployment. Managed PostgreSQL services may
enforce stricter TLS requirements than a local server.

## 16. Production considerations

Do not convert the tutorial profile into a production profile by changing only the
hostname.

Review at least:

```text
environment classification
read_only policy
TLS requirements
secret source
least-privilege role
timeouts
network path
managed-service restrictions
audit and guardrails
```

Production operation is covered later as a dedicated learning path.

## 17. Complete first-connection session

```bash
export PYDBADMIN_LOCAL_PASSWORD="your_password"

pydbadmin --config ./config.toml --connection local connection test
pydbadmin --config ./config.toml --connection local server info
pydbadmin --config ./config.toml --connection local database list
pydbadmin --config ./config.toml --connection local schema list
pydbadmin --config ./config.toml --connection local table list --schema public
pydbadmin --config ./config.toml --connection local capability list
pydbadmin --config ./config.toml --connection local health check
pydbadmin --config ./config.toml --connection local --output json server info
```

The sequence remains read-only:

```text
resolve profile
    ↓
resolve secret
    ↓
test connectivity
    ↓
identify server
    ↓
inspect catalog
    ↓
discover capabilities
    ↓
check health
    ↓
consume structured output
```

## 18. What to remember

```text
ConnectionProfile ≠ raw password
successful connection ≠ unrestricted authorization
inspection ≠ mutation
```

A safe first connection is explicit, named, secret-referenced and read-only.

## 19. Next guide

Continue with:

**[04 — Configuration and Profiles](04_CONFIGURATION_AND_PROFILES.md)**

The next guide covers profile schema, configuration locations, environment classification,
read-only policy, SSL/timeouts and resolution behavior in detail.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Getting started](01_GETTING_STARTED.md)
- [Installation](02_INSTALLATION.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)
- [Support matrix](../reference/SUPPORT_MATRIX.md)
- [Error-code contract](../contracts/ERROR_CODE_CONTRACT.md)
- [Exit-code contract](../contracts/EXIT_CODE_CONTRACT.md)

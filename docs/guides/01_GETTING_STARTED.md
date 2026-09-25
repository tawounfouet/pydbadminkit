# Getting Started with PyDBAdminKit

## Objective

This guide takes a new user from a source checkout to a verified read-only PostgreSQL
inspection using PyDBAdminKit 1.0.

At the end you will be able to:

- verify the installed PyDBAdminKit version;
- create a named PostgreSQL connection profile;
- keep the password outside the configuration file;
- test connectivity;
- inspect the server and databases;
- request JSON output;
- call the stable Python API;
- understand the safety boundary before attempting mutations.

This guide intentionally starts in **read-only mode**.

## 1. Prerequisites

PyDBAdminKit 1.0 supports Python **3.11–3.14**.

The qualified PostgreSQL matrix is:

| PostgreSQL | Status |
| --- | --- |
| 18 | Tier A |
| 17 | Tier A |
| 16 | Tier A |
| 15 | Tier A |
| 14 | Transitional |

PostgreSQL 13 and older are outside the 1.0 support matrix.

You need:

- Python 3.11–3.14;
- a reachable PostgreSQL server;
- a PostgreSQL account able to connect;
- the repository checkout for the source-install workflow below.

Docker is optional. It is development/test infrastructure, not a runtime dependency.

## 2. Create an isolated Python environment

From the repository root on Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[binary]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[binary]"
```

The `binary` extra installs the Psycopg 3 binary distribution used by the documented
development workflow.

## 3. Verify the CLI

Run:

```bash
pydbadmin --version
pydbadmin --help
```

For the stable line described by this guide, the version should report
`pydbadminkit 1.0.0`.

If the generated `pydbadmin.exe` launcher is blocked by a Windows environment, the
package can also be invoked as:

```powershell
python -m pydbadminkit --version
python -m pydbadminkit --help
```

## 4. Create the first connection profile

Create a `config.toml` file:

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

Important properties of this first profile:

```text
profile name    local
engine          postgresql
environment     development
read_only       true
secret provider env
secret value    NOT stored in config.toml
```

The persisted configuration contains a **secret reference**, not the resolved password.

## 5. Provide the password at execution time

Linux/macOS:

```bash
export PYDBADMIN_LOCAL_PASSWORD="your_password"
```

Windows PowerShell:

```powershell
$env:PYDBADMIN_LOCAL_PASSWORD = "your_password"
```

Do not replace the `reference` field in `config.toml` with the password itself.

## 6. Test the connection

Run:

```bash
pydbadmin --connection local connection test
```

If your configuration file is not the default one, select it explicitly:

```bash
pydbadmin --config ./config.toml --connection local connection test
```

The root CLI contract provides both:

```text
--connection, -c   named connection profile
--config           path to TOML configuration
```

A connection failure is surfaced through the framework's typed error/exit-code model
rather than being treated as a successful inspection.

## 7. Inspect the PostgreSQL server

Once connectivity succeeds:

```bash
pydbadmin --connection local server info
pydbadmin --connection local database list
pydbadmin --connection local schema list
```

Continue with catalog inspection:

```bash
pydbadmin --connection local table list --schema public
pydbadmin --connection local view list --schema public
pydbadmin --connection local index list --schema public
```

For a known object:

```bash
pydbadmin --connection local table describe public.customers
```

These are inspection operations. They are the recommended place to become familiar with a
real server before enabling mutations.

## 8. Use machine-readable output

Human table output is the default. Select JSON or YAML at the root:

```bash
pydbadmin --connection local --output json database list
pydbadmin --connection local --output yaml health check
```

The 1.0 CLI accepts:

```text
--output table
--output json
--output yaml
```

JSON is the primary frozen machine contract. Machine-readable stdout is designed for
scripts, CI/CD and other programmatic consumers.

Do not parse the human table rendering when JSON is available.

## 9. Run the first health check

Run:

```bash
pydbadmin --connection local health check
```

The default health suite covers:

```text
connectivity
connection usage
long-running queries
long transactions
idle transactions
waiting locks
```

Default exit behavior is:

| Health state | Exit code |
| --- | ---: |
| OK | 0 |
| WARNING | 0 |
| CRITICAL | 1 |
| UNKNOWN | 0 |

For automation that should fail on warnings:

```bash
pydbadmin --connection local health check --fail-on-warning
```

## 10. Discover capabilities

PyDBAdminKit exposes capability discovery:

```bash
pydbadmin --connection local capability list
```

For one capability:

```bash
pydbadmin --connection local capability get <name>
```

Capability names are part of the frozen 1.0 machine contract. Capability discovery is
preferable to assuming that every operation is available in every target environment.

## 11. Use the stable Python API

The package root is intentionally narrow. Application code should normally start from
`pydbadminkit.bootstrap`.

Example:

```python
from pathlib import Path

from pydbadminkit.bootstrap import build_catalog_service

catalog = build_catalog_service("local", Path("config.toml"))

for database in catalog.list_databases():
    print(database)
```

Stable bootstrap builders also exist for connection, server, security, runtime, backup,
restore, maintenance, monitoring, health and capability services.

Do not build application integrations around:

```text
pydbadminkit.adapters.*
pydbadminkit.infrastructure.*
pydbadminkit.cli.*
```

Those namespaces are implementation surfaces and do not carry the 1.0 public
compatibility guarantee.

## 12. Understand the mutation boundary before changing anything

The first profile in this guide uses:

```toml
read_only = true
```

Keep it that way while learning the inspection surfaces.

PyDBAdminKit mutations share safety controls including:

- `--dry-run`;
- explicit approval;
- environment-aware risk;
- `--confirm-target` for operations requiring exact target proof;
- fail-closed behavior for read-only profiles;
- fail-closed behavior for unknown environments;
- audit lifecycle events for guarded mutations.

A typical mutation learning flow is:

```text
inspect
   ↓
understand target
   ↓
dry-run
   ↓
review OperationPlan / risk
   ↓
explicit confirmation
   ↓
execute
   ↓
verify
   ↓
audit
```

For example, do **not** jump directly to query termination. Start with:

```bash
pydbadmin --connection local query list
```

When using a writable disposable development profile later, preview a guarded operation
first:

```bash
pydbadmin --connection local --dry-run query cancel 12345
```

A production-critical operation may additionally require exact typed-target confirmation.
The global `--yes` option does not bypass that proof.

## 13. A complete first session

A minimal read-only learning session is:

```bash
pydbadmin --version

pydbadmin --connection local connection test
pydbadmin --connection local server info

pydbadmin --connection local database list
pydbadmin --connection local schema list
pydbadmin --connection local table list --schema public

pydbadmin --connection local health check
pydbadmin --connection local capability list

pydbadmin --connection local --output json database list
```

This exercises the CLI, configuration resolver, connection layer, server/catalog
inspection, monitoring/health surface, capability discovery and machine interface without
performing an administrative mutation.

## 14. Common first-run problems

### Profile not found

Check the profile name after `[connections.<name>]` and the selected `--connection`.

If the configuration is stored outside the default location, pass `--config` explicitly.

### Secret cannot be resolved

Check that the environment variable named by:

```toml
[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"
```

exists in the shell that launches PyDBAdminKit.

### Database connection fails

Verify host, port, database, username, SSL mode and PostgreSQL reachability. A successful
TCP connection alone does not guarantee PostgreSQL authentication succeeds.

### A mutation is blocked

That is expected for the profile in this guide because `read_only = true`. Do not disable
the guardrail merely to make a command pass. Use a deliberate writable development/testing
profile when learning mutation workflows.

### Native backup/restore tools are unavailable

Backup/restore workflows depend on PostgreSQL native tools:

```text
pg_dump
pg_restore
psql
```

They are covered in the dedicated Operations guides rather than required for the
read-only first session.

## 15. What you have learned

You now have the core mental model:

```text
config.toml
    ↓
named connection profile
    ↓
secret reference
    ↓
secret resolved at execution boundary
    ↓
CLI or public Python API
    ↓
Application service
    ↓
PostgreSQL
```

And for administrative changes:

```text
inspection → dry-run → risk/guardrails → confirmation → execution → verification → audit
```

## 16. Next guide

Continue with:

**[02 — Installation](02_INSTALLATION.md)**

It will cover installation choices, extras, source/development installation, platform
considerations and installation verification in detail.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)
- [Support matrix](../reference/SUPPORT_MATRIX.md)
- [Migration and deprecation policy](../reference/MIGRATION_AND_DEPRECATION_POLICY.md)
- [Error-code contract](../contracts/ERROR_CODE_CONTRACT.md)
- [Exit-code contract](../contracts/EXIT_CODE_CONTRACT.md)

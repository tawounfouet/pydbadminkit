# PyDBAdminKit

CLI-first, Python-first database administration framework.

> **Current release:** `0.3.0` — PostgreSQL Foundation, Object Explorer and Security Administration.

PyDBAdminKit provides a safe, typed administration core for database servers from both a CLI and a Python API. PostgreSQL is the reference and initial engine.

## Current capabilities

### Foundation

- typed Domain / Application / Ports / Adapters architecture;
- TOML connection profiles;
- secret references resolved from the environment;
- PostgreSQL connection testing;
- stable public error hierarchy and exit codes;
- capability discovery;
- package, quality, unit and PostgreSQL integration CI gates.

### Object Explorer

```text
PostgreSQL Server
└── Databases
    └── Schemas
        ├── Tables
        │   ├── Columns
        │   └── Constraints
        ├── Views
        ├── Materialized Views
        └── Indexes
```

Representative commands:

```bash
# Linux / macOS
pydbadmin --connection local server info
pydbadmin --connection local database list
pydbadmin --connection local schema list
pydbadmin --connection local table describe public.customers
pydbadmin --connection local view list --schema public
pydbadmin --connection local index list --schema public --table customers
```

```powershell
# Windows PowerShell
python -m pydbadminkit --connection local server info
python -m pydbadminkit --connection local database list
python -m pydbadminkit --connection local schema list
python -m pydbadminkit --connection local table describe public.customers
python -m pydbadminkit --connection local view list --schema public
python -m pydbadminkit --connection local index list --schema public --table customers
```

> **Windows note:** if the `pydbadmin` alias is set up in your PowerShell profile
> (see [Development setup](#development-setup)), use `pydbadmin` directly instead of
> `python -m pydbadminkit`.

### Machine-readable interface

All implemented inspection and Security commands support:

```bash
--output table
--output json
--output yaml
```

Human output is the default. JSON/YAML stdout is kept machine-readable for scripts, CI/CD and future agents.

### Security Administration

Read-only inspection:

- roles and PostgreSQL login roles;
- role attributes;
- role membership graph;
- direct relation ACL access;
- effective relation access with source attribution:
  - `direct`
  - `inherited`
  - `public`
  - `owner`
  - `superuser`
- database/schema/table/view ownership.

Guarded mutations:

- create / alter / drop roles;
- add / remove memberships;
- grant / revoke relation access.

Safety controls:

- `--dry-run` operation planning;
- risk levels `low / medium / high / critical`;
- explicit and typed-target confirmations;
- `--yes` cannot bypass typed-target confirmation;
- `--non-interactive` deterministic automation behavior;
- fail-closed mutations for read-only profiles and unknown environments;
- protections for PostgreSQL built-in roles and the active connection role;
- local secret-safe JSONL audit events with correlation IDs.

Examples:

```bash
# Linux / macOS
pydbadmin --connection local role list
pydbadmin --connection local role describe app

pydbadmin --connection local access list --role app
pydbadmin --connection local effective-access list --role app
pydbadmin --connection local ownership list --owner app

pydbadmin --connection local --dry-run role create app --login
pydbadmin --connection local --yes role create app --login

pydbadmin --connection local --yes \
  access grant \
  --role app \
  --object public.customers \
  --access SELECT
```

```powershell
# Windows PowerShell (use backtick ` for line continuation, not \)
python -m pydbadminkit --connection local role list
python -m pydbadminkit --connection local role describe app

python -m pydbadminkit --connection local access list --role app
python -m pydbadminkit --connection local effective-access list --role app
python -m pydbadminkit --connection local ownership list --owner app

python -m pydbadminkit --connection local --dry-run role create app --login
python -m pydbadminkit --connection local --yes role create app --login

python -m pydbadminkit --connection local --yes `
  access grant `
  --role app `
  --object public.customers `
  --access SELECT
```

Critical operations require an exact target proof, for example:

```bash
# Linux / macOS
pydbadmin --connection local --non-interactive \
  role create privileged_admin \
  --superuser \
  --confirm-target privileged_admin
```

```powershell
# Windows PowerShell
python -m pydbadminkit --connection local --non-interactive `
  role create privileged_admin `
  --superuser `
  --confirm-target privileged_admin
```

## Development setup

### Linux / macOS

```bash
git clone https://github.com/tawounfouet/pydbadminkit.git
cd pydbadminkit

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

### Windows PowerShell

```powershell
git clone https://github.com/tawounfouet/pydbadminkit.git
cd pydbadminkit

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

> **Windows — `pydbadmin` command:** pip installs a `pydbadmin.exe` launcher that may
> be blocked by some environments (sandboxes, corporate policies). If you get an
> "Access Denied" error, add this function to your PowerShell `$PROFILE`:
> ```powershell
> function pydbadmin { python -m pydbadminkit @args }
> ```
> After reloading (`. $PROFILE`), `pydbadmin` will work like on Linux.

Run the quality gates:

```bash
# Linux / macOS
pydbadmin --version
ruff format --check .
ruff check .
mypy src/pydbadminkit
pytest -m unit --cov=pydbadminkit
pytest -m "integration and postgresql"
```

```powershell
# Windows PowerShell
python -m pydbadminkit --version
ruff format --check .
ruff check .
mypy src/pydbadminkit
pytest -m unit --cov=pydbadminkit
pytest -m "integration and postgresql"
```

## Local PostgreSQL

Two options are available: **Docker** (recommended, version-pinned) or a **locally installed PostgreSQL**.

### Option A — Docker (PostgreSQL 18)

```bash
# Linux / macOS & Windows (same command)
docker compose up -d postgres
docker compose ps
```

> **Windows note for postgres:18+:** the volume must be mounted at `/var/lib/postgresql`
> (not `/var/lib/postgresql/data`). The provided `docker-compose.yml` is already correct.
> If you get a startup error after upgrading the image, run `docker compose down -v` to
> reset the volume, then restart.

Connection profile for Docker:

```toml
[connections.local]
engine = "postgresql"
host = "localhost"
port = 5432
database = "pydbadmin_dev"
username = "postgres"
environment = "development"
read_only = false
ssl_mode = "disable"
connect_timeout_seconds = 10

[connections.local.secret]
provider = "env"
reference = "PYDBADMIN_LOCAL_PASSWORD"
```

Set the password:

```bash
# Linux / macOS
export PYDBADMIN_LOCAL_PASSWORD="postgres"
```

```powershell
# Windows PowerShell
$env:PYDBADMIN_LOCAL_PASSWORD = "postgres"
```

### Option B — Locally installed PostgreSQL (any version)

If PostgreSQL is already installed on your machine (e.g., PostgreSQL 17 on Windows):

```powershell
# Windows — check the service
Get-Service -Name "*postgres*"

# Create the dev database (first time only)
$env:PGPASSWORD = "your_password"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -c "CREATE DATABASE pydbadmin_dev;"
```

```bash
# Linux / macOS — check the service
pg_isready
psql -U postgres -c "CREATE DATABASE pydbadmin_dev;"
```

Connection profile for local PostgreSQL:

```toml
[connections.local-native]
engine = "postgresql"
host = "localhost"
port = 5432
database = "pydbadmin_dev"
username = "postgres"
environment = "development"
read_only = false
ssl_mode = "disable"
connect_timeout_seconds = 10

[connections.local-native.secret]
provider = "env"
reference = "PYDBADMIN_NATIVE_PASSWORD"
```

Set the password:

```bash
# Linux / macOS
export PYDBADMIN_NATIVE_PASSWORD="your_password"
```

```powershell
# Windows PowerShell
$env:PYDBADMIN_NATIVE_PASSWORD = "your_password"
```

### Connection profiles summary

| Profile | Target | Password env var | Notes |
|---------|--------|-----------------|-------|
| `local` | Docker postgres:18 | `PYDBADMIN_LOCAL_PASSWORD` | Requires Docker running |
| `local-native` | Locally installed PG | `PYDBADMIN_NATIVE_PASSWORD` | Requires local service running |

## Python API and notebooks

The repository also includes executable examples for experimenting with the public Python API and CLI:

- `scripts/pydbadminkit_example.py`: end-to-end Python API demonstration aligned with the current 0.3.0 contracts;
- `notebooks/00 - Setup.ipynb`: Python API lab for incremental exploration of domain objects and services;
- `notebooks/pydbadminkit_demo.ipynb`: CLI-oriented lab, including JSON/YAML output examples.

Both notebooks are committed without execution outputs or embedded secrets. Real mutations are opt-in and should only be enabled against a disposable development/testing database.

## Architecture

```text
CLI / Python API
      ↓
Application
      ↓
Domain + Ports
      ↑
Adapters
      ↓
Infrastructure
```

The Domain does not depend on Psycopg, Typer, Rich or PostgreSQL catalog internals.

## Roadmap

```text
0.1.x  Foundation                  ✅
0.2.x  Object Explorer            ✅
0.3.x  Security Administration    ✅
0.4.x  Runtime Administration     next
0.5.x  Operations
0.6.x  Observability
1.0.0  Stable PostgreSQL API
```

The next implementation line is `0.4.x — Runtime Administration`: sessions, queries, transactions, locks, blocking chains and guarded cancel/terminate operations.

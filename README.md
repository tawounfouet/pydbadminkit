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
pydbadmin --connection local server info
pydbadmin --connection local database list
pydbadmin --connection local schema list
pydbadmin --connection local table describe public.customers
pydbadmin --connection local view list --schema public
pydbadmin --connection local index list --schema public --table customers
```

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
pydbadmin --connection local role list
pydbadmin --connection local role describe app

pydbadmin --connection local access list --role app
pydbadmin --connection local effective-access list --role app
pydbadmin --connection local ownership list --owner app

pydbadmin --connection local --dry-run role create app --login
pydbadmin --connection local --yes role create app --login

pydbadmin --connection local --yes   access grant   --role app   --object public.customers   --access SELECT
```

Critical operations require an exact target proof, for example:

```bash
pydbadmin --connection local --non-interactive   role create privileged_admin   --superuser   --confirm-target privileged_admin
```

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

Run the quality gates:

```bash
pydbadmin --version
ruff format --check .
ruff check .
mypy src/pydbadminkit
pytest -m unit --cov=pydbadminkit
pytest -m "integration and postgresql"
```

## Local PostgreSQL

```bash
docker compose up -d postgres
```

The development and CI integration target is PostgreSQL 18.

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

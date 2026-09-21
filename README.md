# PyDBAdminKit

CLI-first, Python-first database administration framework.

> **Status:** early alpha / active implementation. Public APIs may evolve before 1.0.

## Goals

PyDBAdminKit provides a safe, typed administration core for database servers from both a CLI and a Python API. PostgreSQL is the reference and initial engine.

The initial roadmap covers:

- connections and configuration;
- server/database/schema/table inspection;
- roles and privileges;
- sessions, queries, transactions and locks;
- backup, restore and maintenance;
- monitoring and health checks;
- structured machine-readable output and guardrails.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,binary]"
```

Run the initial checks:

```bash
pydbadmin --help
pydbadmin --version
ruff format --check .
ruff check .
mypy src/pydbadminkit
pytest -m unit
```

## Local PostgreSQL

```bash
docker compose up -d postgres
```

The default development container runs PostgreSQL 18 on port 5432.

## Architecture

The project follows explicit boundaries:

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

The domain never depends on Psycopg, Typer, Rich, or PostgreSQL catalog internals.

## Safety

PyDBAdminKit will include destructive administration operations. Production mutations are designed around explicit risk classification, dry-run planning, confirmation, audit and read-only profile policies.

## Current implementation milestone

The repository is implementing:

```text
LOT-00 — Repository Foundation
LOT-01 — Core Domain and Errors
```

The first functional PostgreSQL vertical slice will be:

```bash
pydbadmin connection test
```

followed by:

```bash
pydbadmin server info
pydbadmin database list
```

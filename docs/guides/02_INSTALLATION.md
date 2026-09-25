# Installing PyDBAdminKit

## Objective

This guide describes the installation model for PyDBAdminKit 1.0 and explains which
dependency extras to select for development, direct PostgreSQL connectivity and connection
pooling.

The authoritative 1.0 package metadata requires Python **3.11 or newer**. The qualified
release matrix is Python **3.11–3.14**; Python 3.15 is not yet part of the support promise.

## 1. Installation model

PyDBAdminKit is a Python package with the console entry point:

```text
pydbadmin = pydbadminkit.cli.app:app
```

The repository uses:

```text
build backend    hatchling
package layout   src/pydbadminkit
Python           >=3.11
license          Apache-2.0
```

The source-checkout workflow is the documented and qualified development installation
path. Do not assume that a package index contains a particular release unless that release
has actually been published there.

## 2. Verify Python

Linux/macOS:

```bash
python --version
python -m pip --version
```

Windows PowerShell:

```powershell
python --version
python -m pip --version
```

Use Python 3.11, 3.12, 3.13 or 3.14 for the 1.0 qualified line.

## 3. Create a virtual environment

A dedicated environment prevents PyDBAdminKit dependencies from leaking into the system
Python environment.

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Verify that the environment is active:

```bash
python -c "import sys; print(sys.executable)"
```

## 4. Install from a source checkout

Clone the repository, enter it, upgrade pip and install the package in editable mode.

Linux/macOS:

```bash
git clone https://github.com/tawounfouet/pydbadminkit.git
cd pydbadminkit
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[binary]"
```

Windows PowerShell:

```powershell
git clone https://github.com/tawounfouet/pydbadminkit.git
cd pydbadminkit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[binary]"
```

Editable installation is appropriate when working directly with the repository because
changes under `src/pydbadminkit` are reflected without rebuilding the package.

## 5. Choose dependency extras

The package defines three optional dependency groups relevant to users and contributors.

### binary

```text
psycopg[binary]>=3.3,<4
```

Install with:

```bash
pip install -e ".[binary]"
```

This is the simplest documented local setup for PostgreSQL connectivity.

### pool

```text
psycopg[pool]>=3.3,<4
```

Install with:

```bash
pip install -e ".[pool]"
```

Use this extra when your integration needs the Psycopg 3 pool package. The existence of
the extra does not change the public PyDBAdminKit 1.0 API contract.

### dev

The development extra includes the repository quality and release toolchain, including:

```text
build
mypy
pip-audit
pytest
pytest-cov
pytest-timeout
ruff
twine
types-PyYAML
```

Contributor setup:

```bash
pip install -e ".[dev,binary]"
```

This is the appropriate installation for running the same categories of quality checks
used by the project.

## 6. Core runtime dependencies

PyDBAdminKit 1.0 declares these runtime dependency lines:

| Dependency | Supported line | Purpose |
| --- | --- | --- |
| `platformdirs` | >=4,<5 | platform-aware paths |
| `psycopg` | >=3.3,<4 | PostgreSQL driver |
| `PyYAML` | >=6,<7 | YAML machine output |
| `rich` | >=13,<15 | human-oriented console rendering |
| `typer` | >=0.12,<1 | CLI |

Psycopg 2 is not part of the 1.0 architecture.

## 7. Verify the installation

Check the package import:

```bash
python -c "import pydbadminkit; print(pydbadminkit.__version__)"
```

For this guide line the expected version is:

```text
1.0.0
```

Then check the console interface:

```bash
pydbadmin --version
pydbadmin --help
```

Expected version output identifies `pydbadminkit 1.0.0`.

## 8. Windows launcher fallback

The installed package exposes a `pydbadmin.exe` launcher on Windows. Some sandboxed or
corporate environments can block generated executable launchers.

The module entry point remains available:

```powershell
python -m pydbadminkit --version
python -m pydbadminkit --help
```

For an interactive PowerShell convenience alias:

```powershell
function pydbadmin { python -m pydbadminkit @args }
```

If you want the function persisted, place it in your PowerShell profile according to your
local shell-management policy.

## 9. PostgreSQL native tools

Basic connection, catalog, security, runtime and monitoring usage does not require Docker.

Logical Operations use PostgreSQL native client tools:

| Tool | Used for |
| --- | --- |
| `pg_dump` | logical backup |
| `pg_restore` | custom archive validation and restore |
| `psql` | plain-SQL restore |

The 1.0 qualification matrix uses client tools matching the PostgreSQL server major.

The implemented compatibility policy rejects an older `pg_dump` against a newer server
and rejects restore tooling that is too old for the target server.

Therefore, an installation can be valid for inspection while backup/restore capabilities
remain unavailable because native tools are missing.

Use capability discovery rather than treating that as a package-installation failure.

## 10. Docker is optional

PyDBAdminKit has no runtime dependency on Docker.

The repository provides Docker-based PostgreSQL development/test infrastructure. For the
documented local PostgreSQL 18 environment:

```bash
docker compose up -d postgres
docker compose ps
```

You can instead use a natively installed PostgreSQL server or a reachable remote server.

## 11. Build distribution artifacts

Contributors with the `dev` extra can build the package:

```bash
python -m build
```

This produces wheel and source-distribution artifacts under `dist/`.

Validate artifact metadata:

```bash
python -m twine check dist/*
```

The 1.0 release qualification separately tests clean installation of both wheel and sdist
on Python 3.11, 3.12, 3.13 and 3.14.

## 12. Clean wheel smoke test

A local approximation of the release installation gate is:

```bash
python -m build

python -m venv .venv-wheel
.venv-wheel/bin/python -m pip install --upgrade pip
.venv-wheel/bin/python -m pip install dist/*.whl
.venv-wheel/bin/python -c "import pydbadminkit; print(pydbadminkit.__version__)"
.venv-wheel/bin/pydbadmin --version
```

On Windows, use the executables under `.venv-wheel\Scripts\`.

A clean artifact installation is a stronger packaging check than relying only on an
editable development environment.

## 13. Contributor quality setup

With:

```bash
pip install -e ".[dev,binary]"
```

run:

```bash
ruff format --check .
ruff check .
mypy src/pydbadminkit
pytest -m unit --cov=pydbadminkit
pytest -m "integration and postgresql"
```

The project coverage threshold is **85%**.

PostgreSQL integration tests require their database environment and should not be confused
with package import smoke tests.

## 14. Operating-system support

The package is designed for Linux, macOS and Windows path/config/process semantics.

For the 1.0 support promise:

```text
Linux      authoritative automated CI
macOS      portability target
Windows    portability target
```

Do not describe macOS or Windows as independently Tier A-qualified operating-system
matrices unless dedicated CI qualification is added in a future release.

## 15. Managed PostgreSQL

The 1.0 support matrix treats these as best-effort PostgreSQL-semantic targets:

```text
Amazon RDS for PostgreSQL
Azure Database for PostgreSQL
Google Cloud SQL for PostgreSQL
```

Provider restrictions can affect superuser operations, maintenance, backend termination,
extensions and other privileged behavior. Successful package installation does not imply
that every capability is available on a managed service.

## 16. Installation troubleshooting

### `python` is below 3.11

Use a supported interpreter and recreate the virtual environment. The package metadata
requires Python >=3.11.

### Python 3.15 is installed

Python 3.15 is not yet in the 1.0 qualified support matrix. Use Python 3.11–3.14 for a
supported deployment.

### `pydbadmin` is not found

Verify that the intended virtual environment is active and inspect:

```bash
python -m pip show pydbadminkit
python -m pydbadminkit --version
```

If module execution works, investigate the virtual environment's scripts/bin path.

### Psycopg installation problems

Use the documented `binary` extra for the simplest development setup:

```bash
pip install -e ".[binary]"
```

### Backup reports missing tools

This does not necessarily mean PyDBAdminKit itself is incorrectly installed. Verify
`pg_dump`, `pg_restore` and `psql` availability and version compatibility.

## 17. Installation checklist

```text
[ ] Python 3.11–3.14
[ ] dedicated virtual environment
[ ] PyDBAdminKit installed
[ ] import reports 1.0.0
[ ] CLI reports 1.0.0
[ ] --help works
[ ] PostgreSQL reachable for the next guide
[ ] native tools installed if backup/restore will be used
```

## 18. Next guide

Continue with:

**[03 — First connection](03_FIRST_CONNECTION.md)**

The next guide focuses on connection profiles, secret resolution, connectivity testing,
SSL-related fields and the first server inspection.

## See also

- [Guides index](00_GUIDES_INDEX.md)
- [Getting started](01_GETTING_STARTED.md)
- [Support matrix](../reference/SUPPORT_MATRIX.md)
- [CLI reference](../reference/CLI_REFERENCE.md)
- [Python API reference](../reference/PYTHON_API_REFERENCE.md)

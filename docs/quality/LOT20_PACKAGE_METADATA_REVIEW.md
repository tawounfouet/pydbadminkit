# LOT-20 / T20-015 — Package Metadata Review

## Status

```text
Ticket: T20-015
Lot: LOT-20 — Hardening
Baseline reviewed: 0.6.0
Result: metadata hardened; one owner-policy item remains for 1.0 publication
```

## Distribution identity

The package metadata now explicitly advertises:

```text
name: pydbadminkit
Python: >=3.11
console script: pydbadmin
typed package
console environment
database / systems-administration topic
Python 3.11–3.14 classifiers
```

The version remains single-sourced from `src/pydbadminkit/version.py` through Hatch.

## Runtime dependency policy

Runtime dependencies retain explicit major-version ceilings:

```text
platformdirs >=4,<5
psycopg >=3.3,<4
PyYAML >=6,<7
rich >=13,<15
typer >=0.12,<1
```

Optional Psycopg binary/pool extras remain on the same Psycopg compatibility line.

## Project URLs

Package metadata now exposes canonical navigation for:

```text
Homepage
Repository
Issues
Changelog
```

All point to the canonical `tawounfouet/pydbadminkit` repository.

## Build and install qualification

The existing Package workflow already verifies:

```text
python -m build
twine check
wheel installation into a clean virtual environment
pydbadmin --version
pydbadmin --help
```

This remains the release artifact gate.

## Metadata regression tests

`tests/unit/test_package_metadata.py` freezes:

- distribution name;
- Python floor;
- README metadata;
- dynamic version source;
- console entry point;
- project URLs;
- advertised Python versions;
- major bounds for runtime dependencies.

## Finding PKG-20-015-01 — license declaration

No `LICENSE` file or explicit `project.license` decision currently exists in the
repository.

T20-015 deliberately does **not** invent a legal licensing choice. A public Git repository
does not by itself establish which license the project owner intends to grant.

This is therefore recorded as an explicit owner-policy decision for the 1.0 publication
gate:

```text
Choose license policy
        ↓
add LICENSE when applicable
        ↓
declare project.license / license-files metadata
        ↓
re-run build + twine qualification
```

Until that decision is made, package metadata must not claim MIT, Apache, proprietary or
another license.

## LOT-20 result

With T20-015, the implementation tickets of LOT-20 have all been reviewed. The remaining
step is to verify the complete hardening branch through CI, including the PostgreSQL 14–18
matrix, then hand the repository to LOT-21 qualification/documentation.

## Next lot

```text
LOT-21 — Qualification / Documentation
```

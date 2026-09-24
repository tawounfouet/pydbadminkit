# PyDBAdminKit 1.0 Support Matrix

## Release line

This matrix defines the compatibility promise prepared for the PyDBAdminKit 1.0 line.

## Python

| Python | Status | Qualification |
| --- | --- | --- |
| 3.11 | Supported | full unit + artifact install matrix |
| 3.12 | Supported | full unit + artifact install matrix |
| 3.13 | Supported | full unit + artifact install matrix |
| 3.14 | Supported | full unit + artifact install matrix |
| 3.15 | Not yet supported | add only after release-toolchain qualification |
| <=3.10 | Unsupported | below `requires-python` |

Package metadata:

```text
requires-python = >=3.11
```

Dropping a supported Python version after 1.0 requires an explicit support-policy change,
documentation and CI removal.

## PostgreSQL

| PostgreSQL | Status | Qualification |
| --- | --- | --- |
| 18 | Tier A | full live integration matrix |
| 17 | Tier A | full live integration matrix |
| 16 | Tier A | full live integration matrix |
| 15 | Tier A | full live integration matrix |
| 14 | Transitional | live integration matrix |
| 19 beta/devel | Unsupported | no release support promise |
| <=13 | Unsupported | outside 1.0 matrix |

Tier A means:

```text
full support
full matrix
bug fixes accepted
```

Transitional means temporary compatibility with a reduced future guarantee. PostgreSQL 14
must be re-evaluated at the 1.0 stable boundary according to upstream community lifecycle.

A PostgreSQL version is not advertised as supported merely because it appears to work. It
must be CI-tested and documented.

## PostgreSQL feature coverage

The Tier A matrix exercises the implemented 1.0 surfaces:

```text
connection
catalog
security
runtime
monitoring / health
maintenance
backup / restore
CLI + machine output
```

## Psycopg

Runtime dependency:

```text
psycopg >=3.3,<4
```

The optional binary/pool extras remain on the Psycopg 3 compatibility line.

Psycopg 2 is not part of the 1.0 architecture.

## PostgreSQL native tools

Logical operations use:

```text
pg_dump     backup
pg_restore  custom restore / archive validation
psql        plain-SQL restore
```

Release qualification uses client tools matching the PostgreSQL server major.

Runtime compatibility rules reject an older `pg_dump` against a newer server and reject
restore tooling that is too old for the target server according to the implemented
preflight policy.

## Operating systems

The framework is Python-based and its path/config/process abstractions are designed for
Linux, macOS and Windows usage.

The authoritative automated 1.0 CI currently runs on Linux GitHub-hosted runners. Windows
and macOS therefore remain portability targets documented by the project, not independent
Tier A operating-system matrices.

No runtime dependency on Docker exists. Docker is development/test infrastructure only.

## Managed PostgreSQL

The following are **best-effort PostgreSQL-semantic compatibility targets**:

```text
Amazon RDS for PostgreSQL
Azure Database for PostgreSQL
Google Cloud SQL for PostgreSQL
```

No provider-specific qualification matrix currently exists. Provider restrictions around
superuser privileges, extensions, backend termination, maintenance or native-tool access
may reduce available capabilities.

## Unsupported 1.0 scope

The 1.0 support promise does not include:

```text
MySQL
MariaDB
SQL Server
PostgreSQL physical backup/PITR
replication administration
async adapter
Prometheus exporter runtime adapter
OpenTelemetry exporter runtime adapter
web administration UI
```

## Support-state vocabulary

```text
Tier A        fully qualified release support
Transitional temporary support with planned re-evaluation
Unsupported   no compatibility promise; may happen to work
Best-effort   semantic target without dedicated qualification matrix
```

## Change policy

Support removals must be announced in documentation, changelog/release notes and CI. A
passing unqualified platform does not silently expand the support promise.
